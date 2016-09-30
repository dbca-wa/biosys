from __future__ import absolute_import, unicode_literals, print_function, division

import datetime

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from main.constants import MODEL_SRID
from main.models import Project, Site, Dataset, GenericRecord, Observation, SpeciesObservation


class ProjectSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField(required=False)

    class Meta:
        model = Project
        fields = '__all__'


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = '__all__'


class DatasetSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Dataset
        fields = '__all__'


class GenericDataValidator:
    def __call__(self, data):
        if self.dataset is not None:
            self.dataset.validate_data(data)
            # validate site
            schema = self.dataset.schema
            site_fk = schema.get_fk_for_model('Site')
            if site_fk:
                model_field = site_fk.model_field
                site_value = data.get(site_fk.data_field)
                kwargs = {
                    "project": self.dataset.project,
                    model_field: site_value
                }
                if not Site.objects.filter(**kwargs).exists():
                    msg = "Could not find the site '{} in: {}':".format(site_value, data)
                    raise ValidationError(msg)

    def set_context(self, serializer_field):
        ctx = serializer_field.parent.context
        if 'dataset' in ctx:
            self.dataset = ctx['dataset']
        elif 'dataset' in ctx['request'].data:
            self.dataset = Dataset.objects.get(pk=ctx['request'].data['dataset'])
        else:
            self.dataset = None


class GenericRecordListSerializer(serializers.ListSerializer):
    """
    This serializer uses the django bulk_create instead of creating one by one.
    """
    def create(self, validated_data):
        records = []
        model = self.child.Meta.model
        for data in validated_data:
            record = model(**data)
            self.child.set_site(record, data, force_create=False, commit=False)
            records.append(record)
        return model.objects.bulk_create(records)

    def update(self, instance, validated_data):
        raise NotImplementedError(
            "Serializers with many=True do not support multiple update by "
            "default, only multiple create. For updates it is unclear how to "
            "deal with insertions and deletions. If you need to support "
            "multiple update, use a `ListSerializer` class and override "
            "`.update()` so you can specify the behavior exactly."
        )


class GenericRecordSerializer(serializers.ModelSerializer):
    data = serializers.JSONField(
        validators=[
            GenericDataValidator()
        ]
    )

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
        site = GenericRecordSerializer.get_site(instance.dataset, validated_data['data'], force_create=force_create)
        if site is not None and instance.site != site:
            instance.site = site
            if commit:
                instance.save()
        return instance

    def create(self, validated_data):
        """
        Extract the Site from data if not specified
        :param validated_data:
        :return:
        """
        instance = super(GenericRecordSerializer, self).create(validated_data)
        return self.set_site(instance, validated_data, force_create=False)

    def update(self, instance, validated_data):
        instance = super(GenericRecordSerializer, self).update(instance, validated_data)
        result = self.set_site(instance, validated_data)
        return result

    class Meta:
        model = GenericRecord
        list_serializer_class = GenericRecordListSerializer
        fields = '__all__'


class ObservationListSerializer(GenericRecordListSerializer):
    def create(self, validated_data):
        records = []
        model = self.child.Meta.model
        for data in validated_data:
            record = model(**data)
            self.child.set_site(record, data, commit=False, force_create=False)
            self.child.set_date_and_geometry(record, data, commit=False)
            records.append(record)
        return model.objects.bulk_create(records)

    def update(self, instance, validated_data):
        return super(ObservationListSerializer, self).update(instance, validated_data)


class ObservationSerializer(GenericRecordSerializer):
    @staticmethod
    def get_datetime(dataset, data):
        return dataset.schema.cast_record_observation_date(data)

    @staticmethod
    def get_geometry(dataset, data):
        return dataset.schema.cast_geometry(data, default_srid=MODEL_SRID)

    @staticmethod
    def set_date(instance, validated_data, commit=True):
        dataset = instance.dataset
        observation_date = ObservationSerializer.get_datetime(dataset, validated_data['data'])
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
        geom = ObservationSerializer.get_geometry(instance.dataset, validated_data['data'])
        if geom:
            instance.geometry = geom
            if commit:
                instance.save()
        return instance

    def set_date_and_geometry(self, instance, validated_data, commit=True):
        self.set_date(instance, validated_data, commit=commit)
        self.set_geometry(instance, validated_data, commit=commit)
        return instance

    def create(self, validated_data):
        instance = super(ObservationSerializer, self).create(validated_data)
        return self.set_date_and_geometry(instance, validated_data)

    def update(self, instance, validated_data):
        instance = super(ObservationSerializer, self).update(instance, validated_data)
        return self.set_date_and_geometry(instance, validated_data)

    class Meta:
        model = Observation
        list_serializer_class = ObservationListSerializer


class SpeciesObservationListSerializer(ObservationListSerializer):
    def create(self, validated_data):
        records = []
        model = self.child.Meta.model
        for data in validated_data:
            record = model(**data)
            self.child.set_site(record, data, commit=False, force_create=False)
            self.child.set_date_and_geometry(record, data, commit=False)
            self.child.set_species_name_and_id(record, data, commit=False)
            records.append(record)
        return model.objects.bulk_create(records)

    def update(self, instance, validated_data):
        return super(ObservationListSerializer, self).update(instance, validated_data)


class SpeciesObservationSerializer(ObservationSerializer):
    @staticmethod
    def get_species_name(dataset, data):
        return dataset.schema.cast_species_name(data)

    @classmethod
    def set_species_name(cls, instance, validated_data, commit=True):
        species_name = cls.get_species_name(instance.dataset, validated_data['data'])
        if species_name:
            instance.species_name = species_name
            if commit:
                instance.save()
        return instance

    def get_name_id(self, species_name):
        name_id = -1
        if 'species_mapping' in self.context and species_name:
            name_id = int(self.context['species_mapping'].get(species_name, -1))
        return name_id

    def set_name_id(self, instance, commit=True):
        name_id = self.get_name_id(instance.species_name)
        instance.name_id = name_id
        if commit:
            instance.save()
        return instance

    def set_species_name_and_id(self, instance, validated_data, commit=True):
        self.set_species_name(instance, validated_data, commit=commit)
        self.set_name_id(instance, commit=commit)
        return instance

    def create(self, validated_data):
        instance = super(SpeciesObservationSerializer, self).create(validated_data)
        return self.set_species_name_and_id(instance, validated_data)

    def update(self, instance, validated_data):
        instance = super(SpeciesObservationSerializer, self).update(instance, validated_data)
        return self.set_species_name_and_id(instance, validated_data)

    class Meta:
        model = SpeciesObservation
        list_serializer_class = SpeciesObservationListSerializer
