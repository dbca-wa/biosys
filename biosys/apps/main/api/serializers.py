from __future__ import absolute_import, unicode_literals, print_function, division

import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from rest_framework import serializers, fields, validators
from rest_framework_gis import serializers as serializers_gis
from drf_extra_fields.fields import Base64ImageField

from main.api.validators import get_record_validator_for_dataset
from main.constants import MODEL_SRID
from main.models import Program, Project, Site, Dataset, Record, Media, DatasetMedia, ProjectMedia, Form
from main.utils_auth import is_admin
from main.utils_species import get_key_for_value

import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class UsernameValidator(RegexValidator):
    """
    A username validator that allows `\` (backslash). This is a requirement imposed by NSW OEH.
    By default Django and DRF doesn't allow it.
    """
    regex = r'^[\w.@+-\\]+$'
    message = 'Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_/\ characters.'


class WhoAmISerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()
    is_data_engineer = serializers.SerializerMethodField()

    def get_is_admin(self, user):
        return is_admin(user)

    def get_is_data_engineer(self, user):
        return Program.objects.filter(data_engineers__in=[user.pk]).count() > 0

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_admin', 'is_data_engineer')


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        style={'input_type': 'password'},
        write_only=True
    )
    username = fields.CharField(
        max_length=150,
        required=True,
        validators=[
            validators.UniqueValidator(queryset=User.objects.all()),
            UsernameValidator()
        ]
    )

    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get('password')

        try:
            validate_password(password, user)
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})

        return attrs

    def create(self, validated_data):
        try:
            user = User.objects.create_user(**validated_data)
            # assign new user as custodians of some projects if requested.
            # look for a 'projects' string or list in the post data
            # TODO: Should not create the user but return a 400 error if a requested project is not allowed
            # TODO: use a proper validator
            request_data = self.context['request'].data
            if 'projects' in request_data:
                requested_project_names = request_data['projects']
                # compare with the server settings allowed public projects
                allowed_project_names = settings.ALLOWED_PUBLIC_REGISTRATION_PROJECTS
                if allowed_project_names and requested_project_names:
                    if not isinstance(requested_project_names, list):
                        requested_project_names = [requested_project_names]
                    for project_name in [p for p in requested_project_names if p in allowed_project_names]:
                        project = Project.objects.filter(name=project_name).first()
                        if project is not None:
                            project.custodians.add(user)

            # FIXME: A more elegant solution to this would be to extend the use of djoser user registration so that
            # emails could be handled through the plugin. However at present user creation is handled through a vanilla
            # DRF endpoint and client applications in production utilise this for user registration, re: discussion on
            # public user registration for BioSys, so this is used to fulfill requirements for now
            if settings.SEND_REGISTRATION_CONF:
                try:
                    send_mail(
                        subject=settings.REGISTRATION_EMAIL_SUBJECT,
                        message=settings.REGISTRATION_EMAIL_BODY,
                        html_message=settings.REGISTRATION_EMAIL_BODY,
                        from_email=(settings.DEFAULT_FROM_EMAIL),
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                except Exception as mail_exception:
                    logger.warning('Error sending registration confirmation: ' + str(mail_exception))

            return user
        except Exception as e:
            self.fail('cannot create user: {}'.format(e))

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password')


class UserSerializer(serializers.ModelSerializer):
    username = fields.CharField(
        max_length=150,
        required=True,
        validators=[
            validators.UniqueValidator(queryset=User.objects.all()),
            UsernameValidator()
        ]
    )

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'email',
            'date_joined', 'last_login', 'is_active'
        )
        read_only_fields = ('id', 'date_joined', 'last_login', 'is_active')


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField(required=False)
    centroid = serializers_gis.GeometryField(required=False, read_only=True)
    extent = serializers.ListField(required=False, read_only=True)
    dataset_count = serializers.IntegerField(required=False, read_only=True)
    site_count = serializers.IntegerField(required=False, read_only=True)
    record_count = serializers.IntegerField(required=False, read_only=True)

    class Meta:
        model = Project
        fields = '__all__'


class SiteSerializer(serializers.ModelSerializer):
    centroid = serializers_gis.GeometryField(required=False, read_only=True)

    class Meta:
        model = Site
        fields = '__all__'


class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = '__all__'


class DatasetSerializer(serializers.ModelSerializer):
    record_count = serializers.IntegerField(required=False, read_only=True)
    extent = serializers.ListField(required=False, read_only=True)

    class DataPackageValidator:
        def __init__(self):
            # the next variables are set in the set_context method.
            self.dataset_type = Dataset.TYPE_GENERIC
            self.project = None

        def __call__(self, value):
            Dataset.validate_data_package(value, self.dataset_type, self.project)

        def set_context(self, serializer_field):
            if 'request' in serializer_field.parent.context:
                data = serializer_field.parent.context['request'].data
                self.dataset_type = data.get('type')
                self.project = Project.objects.filter(pk=data.get('project')).first()

    data_package = serializers.JSONField(
        validators=[
            DataPackageValidator()
        ]
    )

    def update(self, instance, validated_data):
        has_data = Record.objects.filter(dataset=instance).count() > 0
        if has_data:
            different_type = instance.type != validated_data.get('type')
            different_data_package = instance.data_package != validated_data.get('data_package')
            # TODO: implement a smart risk-checking of changing dataset schema when there's data.
            different_data_package = False
            if different_type or different_data_package:
                message = "This dataset already contains records. " \
                          "You cannot change this field. " \
                          "In order to change this dataset you first need to delete all its records."
                response = {}
                if different_type:
                    response['type'] = message
                if different_data_package:
                    response['data_package'] = message
                raise serializers.ValidationError(response)
        return super(DatasetSerializer, self).update(instance, validated_data)

    class Meta:
        model = Dataset
        fields = '__all__'
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Dataset.objects.all(),
                fields=('name', 'project'),
                message='A dataset with this name already exists in the project.'
            )
        ]


class SchemaValidator:
    def __init__(self, strict=True, **kwargs):
        self.strict = strict
        self.dataset = None,
        self.kwargs = kwargs

    def __call__(self, data):
        if not data:
            msg = "cannot be null or empty"
            raise ValidationError(('data', msg))
        if self.dataset is not None:
            validator = get_record_validator_for_dataset(self.dataset, **self.kwargs)
            validator.schema_error_as_warning = not self.strict
            result = validator.validate(data)
            if result.has_errors:
                error_messages = ['{col_name}::{message}'.format(col_name=k, message=v) for k, v in
                                  result.errors.items()]
                raise ValidationError(error_messages)

    def set_context(self, serializer_field):
        ctx = serializer_field.parent.context
        if 'dataset' in ctx:
            self.dataset = ctx['dataset']


class RecordSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    # TODO: Split the serializer in 3 subclasses. One for every type of dataset.
    def __init__(self, instance=None, **kwargs):
        super(RecordSerializer, self).__init__(instance, **kwargs)
        ctx = kwargs.get('context', {})
        self.dataset = ctx.get('dataset')
        self.strict_schema_validation = ctx.get('strict', False)
        # species naming service
        self.species_naming_facade_class = ctx.get('species_naming_facade_class')
        # the next object will hold a cached version of the 'species_name' -> name_id obtained
        # from the species_naming_facade above.
        self.species_name_id_mapping_cached = None

        # dynamic fields
        request = ctx.get('request')
        if request:
            expected_fields = request.query_params.getlist('fields', [])
            if expected_fields:
                existing_fields = self.fields.keys()
                excluded_fields = set(existing_fields) - set(expected_fields)
                for field in excluded_fields:
                    self.fields.pop(field)

    @staticmethod
    def get_site(dataset, data, force_create=False):
        schema = dataset.schema
        site_fk = schema.get_fk_for_model('Site')
        site = None
        if site_fk:
            model_field = site_fk.model_field
            site_value = data.get(site_fk.data_field)
            kwargs = {
                "project": dataset.project,
                model_field: site_value
            }
            site = Site.objects.filter(**kwargs).first()
            if site is None and force_create:
                site = Site.objects.create(**kwargs)
        return site

    @staticmethod
    def set_site(instance, validated_data, force_create=False, commit=True):
        site = RecordSerializer.get_site(instance.dataset, validated_data['data'], force_create=force_create)
        if site is not None and instance.site != site:
            instance.site = site
            if commit:
                instance.save()
        return instance

    @staticmethod
    def get_datetime(dataset, data):
        return dataset.schema.cast_record_observation_date(data)

    @staticmethod
    def get_geometry(dataset, data):
        return dataset.schema.cast_geometry(data, default_srid=dataset.project.datum or MODEL_SRID)

    @staticmethod
    def set_date(instance, validated_data, commit=True):
        dataset = instance.dataset
        observation_date = RecordSerializer.get_datetime(dataset, validated_data['data'])
        if observation_date:
            # convert to datetime with timezone awareness
            if isinstance(observation_date, datetime.date) and not isinstance(observation_date, datetime.datetime):
                observation_date = datetime.datetime.combine(observation_date, datetime.time.min)
            if timezone.is_naive(observation_date):
                tz = dataset.project.timezone or timezone.get_current_timezone()
                observation_date = timezone.make_aware(observation_date, tz)
            instance.datetime = observation_date
            if commit:
                instance.save()
        return instance

    @staticmethod
    def set_geometry(instance, validated_data, commit=True):
        geom = RecordSerializer.get_geometry(instance.dataset, validated_data['data'])
        if geom:
            instance.geometry = geom
            if commit:
                instance.save()
        return instance

    def set_date_and_geometry(self, instance, validated_data, commit=True):
        self.set_date(instance, validated_data, commit=commit)
        self.set_geometry(instance, validated_data, commit=commit)
        return instance

    def set_species_name_and_id(self, instance, validated_data, commit=True):
        dataset = instance.dataset
        schema = dataset.schema
        schema_data = validated_data['data']
        # either a species name or a nameId
        species_name = schema.cast_species_name(schema_data)
        name_id = schema.cast_species_name_id(schema_data)
        species_mapping = self.get_species_name_id_mapping()
        if species_mapping:
            # name id takes precedence
            if name_id and name_id != -1:
                species_name = get_key_for_value(species_mapping, int(name_id), None)
                if not species_name:
                    raise Exception("Cannot find a species with nameId={}".format(name_id))
            elif species_name:
                name_id = int(species_mapping.get(species_name, -1))
            else:
                raise Exception('Missing Species Name or Species Name Id')
        else:
            # TODO: what to do if we don't have a species mapping?
            name_id = name_id or -1
        instance.species_name = species_name
        instance.name_id = name_id
        if commit:
            instance.save()
        return instance

    def get_species_name_id_mapping(self):
        if all([
            self.species_name_id_mapping_cached is None,
            self.species_naming_facade_class is not None,
            callable(getattr(self.species_naming_facade_class, 'name_id_by_species_name'))
        ]):
            self.species_name_id_mapping_cached = self.species_naming_facade_class().name_id_by_species_name()
        return self.species_name_id_mapping_cached

    def set_fields_from_data(self, instance, validated_data):
        try:
            instance = self.set_site(instance, validated_data)
            if self.dataset and self.dataset.type in [Dataset.TYPE_OBSERVATION, Dataset.TYPE_SPECIES_OBSERVATION]:
                instance = self.set_date_and_geometry(instance, validated_data)
                if self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                    instance = self.set_species_name_and_id(instance, validated_data)
            return instance
        except Exception as e:
            raise serializers.ValidationError(e)

    def get_parent(self, record):
        """
        Return the FIRST parent record.id or None
        """
        parents = record.parents
        # currently client support only one parent
        return parents[0].id if parents else None

    def get_children(self, record):
        """
        :param record:
        :return: an array of children record ids, or None
        """
        children = record.children
        return [rec.id for rec in children] if children is not None else None

    def validate_data(self, data):
        """
        Validate the Record.data JSONField.
        We add a schema validator.
        :param data:
        :return:
        """
        schema_validator = SchemaValidator(strict=self.strict_schema_validation)
        schema_validator.dataset = self.dataset
        if self.dataset and self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
            schema_validator.kwargs['species_name_id_mapping'] = self.get_species_name_id_mapping()
        schema_validator(data)
        return data

    def create(self, validated_data):
        """
        Extract the Site from data if not specified
        :param validated_data:
        :return:
        """
        instance = super(RecordSerializer, self).create(validated_data)
        return self.set_fields_from_data(instance, validated_data)

    def update(self, instance, validated_data):
        instance = super(RecordSerializer, self).update(instance, validated_data)
        # if data are sent we need to update the extracted fields
        if validated_data.get('data') is not None:
            instance = self.set_fields_from_data(instance, validated_data)
        return instance

    class Meta:
        model = Record
        fields = '__all__'


class Base64ProjectMediaSerializer(serializers.ModelSerializer):
    # Only image supported for base 64
    # TODO: investigate extending drf_extra_fields.fields.Base64FileField for video support
    file = Base64ImageField(required=True)

    class Meta:
        model = ProjectMedia
        fields = ('id', 'file', 'project', 'created', 'filesize')


class ProjectMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMedia
        fields = ('id', 'file', 'project', 'created', 'filesize')


class Base64DatasetMediaSerializer(serializers.ModelSerializer):
    # Only image supported for base 64
    # TODO: investigate extending drf_extra_fields.fields.Base64FileField for video support
    file = Base64ImageField(required=True)

    class Meta:
        model = DatasetMedia
        fields = ('id', 'file', 'dataset', 'created', 'filesize')


class DatasetMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetMedia
        fields = ('id', 'file', 'dataset', 'created', 'filesize')


class Base64MediaSerializer(serializers.ModelSerializer):
    # Only image supported for base 64
    # TODO: investigate extending drf_extra_fields.fields.Base64FileField for video support
    file = Base64ImageField(required=True)

    class Meta:
        model = Media
        fields = '__all__'


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = '__all__'


class GeometrySerializer(serializers.Serializer):
    geometry = serializers_gis.GeometryField(required=False)


class GeoConvertSerializer(GeometrySerializer):
    data = serializers.JSONField(required=False)
