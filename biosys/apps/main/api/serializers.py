from __future__ import absolute_import, unicode_literals, print_function, division

from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer

from main.models import Project, Site, Dataset, GenericRecord, Observation, SpeciesObservation


class ProjectSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField()

    class Meta:
        model = Project
        fields = '__all__'


class SiteSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Site
        list_serializer_class = BulkListSerializer
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
                site = Site.objects.filter(**kwargs).first()
                if site is None:
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
    def create(self, validated_data):
        records = []
        model = self.child.Meta.model
        for data in validated_data:
            record = model(**data)
            record.site = self.child.get_site(record.dataset, data, force_create=False)
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
            site_value = data['data'].get(site_fk.data_field)
            kwargs = {
                "project": dataset.project,
                model_field: site_value
            }
            site = Site.objects.filter(**kwargs).first()
            if site is None and force_create:
                site = Site.objects.create(**kwargs)
        return site

    @staticmethod
    def set_site(instance, validated_data, force_create=False):
        site = GenericRecordSerializer.get_site(instance.dataset, validated_data, force_create=force_create)
        if site is not None and instance.site != site:
            instance.site = site
            instance.save()
        return instance

    def create(self, validated_data):
        print('ser create', validated_data)
        """
        Extract the Site from data if not specified
        :param validated_data:
        :return:
        """
        instance = super(GenericRecordSerializer, self).create(validated_data)
        return self.set_site(instance, validated_data, force_create=False)

    def update(self, instance, validated_data):
        instance = super(GenericRecordSerializer, self).update(instance, validated_data)
        result = self.extract_site(instance, validated_data)
        return result

    class Meta:
        model = GenericRecord
        list_serializer_class = GenericRecordListSerializer
        fields = '__all__'


class ObservationSerializer(GenericRecordSerializer):
    class Meta:
        model = Observation


class SpeciesObservationSerializer(ObservationSerializer):
    class Meta:
        model = SpeciesObservation
