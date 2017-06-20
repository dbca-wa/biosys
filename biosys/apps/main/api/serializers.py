from __future__ import absolute_import, unicode_literals, print_function, division

import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers
from rest_framework_gis import serializers as serializers_gis

from main.api.validators import get_record_validator_for_dataset
from main.constants import MODEL_SRID
from main.models import Project, Site, Dataset, Record
from main.utils_species import get_key_for_value


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_superuser', 'is_staff')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude = ('password',)


class ProjectSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField(required=False)
    centroid = serializers_gis.GeometryField(required=False, read_only=True)
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


class DatasetSerializer(serializers.ModelSerializer):
    record_count = serializers.IntegerField(required=False, read_only=True)

    class DataPackageValidator:
        def __init__(self):
            self.dataset_type = Dataset.TYPE_GENERIC

        def __call__(self, value):
            Dataset.validate_data_package(value, self.dataset_type)

        def set_context(self, serializer_field):
            data = serializer_field.parent.context['request'].data
            self.dataset_type = data.get('type')

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
    def __init__(self, instance=None, **kwargs):
        super(RecordSerializer, self).__init__(instance, **kwargs)
        ctx = kwargs.get('context', {})
        strict = ctx.get('strict', False)
        species_mapping = ctx.get('species_mapping')
        schema_validator = SchemaValidator(strict=strict, species_mapping=species_mapping)
        self.fields['data'].validators = [schema_validator]
        self.dataset = kwargs.get('context', {}).get('dataset', None)

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
        default_srid = dataset.project.datum or MODEL_SRID
        return dataset.schema.cast_geometry(data, default_srid=default_srid)

    @staticmethod
    def set_date(instance, validated_data, commit=True):
        dataset = instance.dataset
        observation_date = RecordSerializer.get_datetime(dataset, validated_data['data'])
        if observation_date:
            # convert to datetime with timezone awareness
            if isinstance(observation_date, datetime.date):
                observation_date = datetime.datetime.combine(observation_date, datetime.time.min)
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
        species_mapping = self.context.get('species_mapping')
        if species_mapping:
            # name id takes precedence
            if name_id:
                species_name = get_key_for_value(species_mapping, int(name_id), None)
                if not species_name:
                    raise Exception("Cannot find a species with nameId={}".format(name_id))
            elif species_name:
                name_id = int(species_mapping.get(species_name, -1))
            else:
                raise Exception('Missing Species Name or Species NameId')
        else:
            # what to do if we don't have an species mapping (herbie down?)
            name_id = name_id or -1
        instance.species_name = species_name
        instance.name_id = name_id
        if commit:
            instance.save()
        return instance

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
        return self.set_fields_from_data(instance, validated_data)

    class Meta:
        model = Record
        fields = '__all__'
