from rest_framework import viewsets
from rest_framework import filters

from main import models
from main.api import serializers


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'title',)


class SiteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Site.objects.all()
    serializer_class = serializers.SiteSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'name', 'code')


class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'project')


class GenericRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.GenericRecord.objects.all()
    serializer_class = serializers.GenericRecordSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'site', 'dataset__id', 'dataset__name')


class ObservationViewSet(GenericRecordViewSet):
    queryset = models.Observation.objects.all()
    serializer_class = serializers.ObservationSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = GenericRecordViewSet.filter_fields + ('datetime',)


class SpeciesObservationViewSet(ObservationViewSet):
    queryset = models.SpeciesObservation.objects.all()
    serializer_class = serializers.SpeciesObservationSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ObservationViewSet.filter_fields + ('input_name', 'name_id',)
