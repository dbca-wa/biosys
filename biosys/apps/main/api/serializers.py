from __future__ import absolute_import, unicode_literals, print_function, division

from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer
from rest_framework.validators import UniqueValidator

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
    def __call__(self, value):
        if self.dataset is not None:
            self.dataset.validate_data(value)

    def set_context(self, serializer_field):
        ctx = serializer_field.parent.context
        if 'dataset' in ctx:
            self.dataset = ctx['dataset']
        elif 'dataset' in ctx['request'].data:
            self.dataset = Dataset.objects.get(pk=ctx['request'].data['dataset'])
        else:
            self.dataset = None


class GenericRecordSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    data = serializers.JSONField(
        validators=[
            GenericDataValidator()
        ]
    )

    def create(self, validated_data):
        """
        Extract the Site from data if not specified
        :param validated_data:
        :return:
        """
        instance = super(GenericRecordSerializer, self).create(validated_data)
        if instance.site is None:
            dataset = validated_data['dataset']
            schema = dataset.schema
            site_fk = schema.get_fk_for_model('Site')
            if site_fk:
                model_field = site_fk.model_field
                site_value = validated_data['data'].get(site_fk.data_field)
                kwargs = {
                    "project": dataset.project,
                    model_field: site_value
                }
                site = Site.objects.filter(**kwargs).first()
                if site is not None:
                    instance.site = site
                    instance.save()
        return instance


    class Meta:
        model = GenericRecord
        list_serializer_class = BulkListSerializer
        fields = '__all__'


class ObservationSerializer(GenericRecordSerializer):
    class Meta:
        model = Observation


class SpeciesObservationSerializer(ObservationSerializer):
    class Meta:
        model = SpeciesObservation
