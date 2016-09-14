from __future__ import absolute_import, unicode_literals, print_function, division

from rest_framework import serializers
from rest_framework_bulk import BulkSerializerMixin, BulkListSerializer
from rest_framework.validators import UniqueValidator

from main.models import Project, Site, Dataset, GenericRecord, Observation, SpeciesObservation


class ProjectSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    timezone = serializers.CharField()

    class Meta:
        model = Project
        list_serializer_class = BulkListSerializer
        fields = '__all__'


class SiteSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Site
        list_serializer_class = BulkListSerializer
        fields = '__all__'


class DataPackageValidator:
    def __init__(self):
        self.dataset_type = Dataset.TYPE_GENERIC

    def __call__(self, value):
        Dataset.validate_data_package(value, self.dataset_type)

    def set_context(self, serializer_field):
        data = serializer_field.parent.context['request'].data
        self.dataset_type = data.get('type')


class DatasetSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    data_package = serializers.JSONField(
        validators=[
            DataPackageValidator()
        ]
    )

    class Meta:
        model = Dataset
        fields = '__all__'


class GenericRecordSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = GenericRecord
        list_serializer_class = BulkListSerializer
        fields = '__all__'


class ObservationSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Observation
        list_serializer_class = BulkListSerializer
        fields = '__all__'


class SpeciesObservationSerializer(BulkSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = SpeciesObservation
        list_serializer_class = BulkListSerializer
        fields = '__all__'
