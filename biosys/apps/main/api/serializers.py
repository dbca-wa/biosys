from __future__ import absolute_import, unicode_literals, print_function, division

from rest_framework import serializers

from main.models import Project, Site, Dataset, GenericRecord, Observation, SpeciesObservation


class ProjectSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField()

    class Meta:
        model = Project
        fields = '__all__'


class SiteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Site
        fields = '__all__'


class DatasetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dataset
        fields = '__all__'


class GenericRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = GenericRecord
        fields = '__all__'


class ObservationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Observation
        fields = '__all__'


class SpeciesObservationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpeciesObservation
        fields = '__all__'
