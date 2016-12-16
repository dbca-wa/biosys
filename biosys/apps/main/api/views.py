from __future__ import absolute_import, unicode_literals, print_function, division

from collections import OrderedDict

from django.shortcuts import get_object_or_404
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, filters, generics
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.views import APIView
from rest_framework.views import Response

from main import models
from main.api import serializers
from main.models import Project, Site, Dataset, GenericRecord, Observation, SpeciesObservation
from main.utils_auth import is_admin
from main.utils_species import HerbieFacade


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'title',)


class ProjectPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return \
            request.method in SAFE_METHODS \
            or is_admin(user) \
            or (hasattr(view, 'project') and view.project and view.project.is_custodian(user))


class ProjectSitesView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, ProjectPermission)
    serializer_class = serializers.SiteSerializer

    def __init__(self, **kwargs):
        super(ProjectSitesView, self).__init__(**kwargs)
        self.project = None

    def dispatch(self, request, *args, **kwargs):
        """
        Intercept any request to set the project from the pk
        :param request:
        """
        self.project = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        return super(ProjectSitesView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        project = self.project if hasattr(self, 'project') else get_object_or_404(Project, pk=self.kwargs.get('pk'))
        return Site.objects.filter(project=project)

    def get_serializer(self, *args, **kwargs):
        kwargs["many"] = True
        ser = super(ProjectSitesView, self).get_serializer(*args, **kwargs)
        if hasattr(ser, 'initial_data') and self.project:
            for r in ser.initial_data:
                r['project'] = self.project.pk
        return ser


class SiteViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Site.objects.all()
    serializer_class = serializers.SiteSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'name', 'code')


class DatasetViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'project', 'type')


class DatasetDataPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return \
            request.method in SAFE_METHODS \
            or is_admin(user) \
            or (hasattr(view, 'dataset') and view.dataset and view.dataset.is_custodian(user))


class SpeciesMixin:
    species_facade_class = HerbieFacade


class DatasetDataView(generics.ListCreateAPIView, SpeciesMixin):
    permission_classes = (IsAuthenticated, DatasetDataPermission)

    def __init__(self, **kwargs):
        super(DatasetDataView, self).__init__(**kwargs)
        self.dataset = None

    def dispatch(self, request, *args, **kwargs):
        """
        Intercept any request to set the dataset
        :param request:
        """
        self.dataset = get_object_or_404(models.Dataset, pk=kwargs.get('pk'))
        return super(DatasetDataView, self).dispatch(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.dataset:  # test needed for the swagger
            if self.dataset.type == models.Dataset.TYPE_SPECIES_OBSERVATION:
                return serializers.SpeciesObservationSerializer
            elif self.dataset.type == models.Dataset.TYPE_OBSERVATION:
                return serializers.ObservationSerializer
            else:
                return serializers.GenericRecordSerializer
        else:
            # for the swagger
            return serializers.GenericRecordSerializer

    def get_serializer(self, *args, **kwargs):
        kwargs["many"] = True
        ser = super(DatasetDataView, self).get_serializer(*args, **kwargs)
        # TODO: find a better way to initialize the dataset field of the serializer
        if hasattr(ser, 'initial_data'):
            for r in ser.initial_data:
                r['dataset'] = self.dataset.pk
        return ser

    def get_serializer_context(self):
        ctx = super(DatasetDataView, self).get_serializer_context()
        if self.dataset:
            ctx['dataset'] = self.dataset
            if self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION and 'species_mapping' not in ctx:
                ctx['species_mapping'] = self.species_facade_class().name_id_by_species_name()
        return ctx

    def get_queryset(self):
        return self.dataset.record_queryset if self.dataset else Dataset.objects.none()

    def get(self, request, *args, **kwargs):
        """
        Forward the get to the list of ListModelMixin
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        if not self.dataset:
            self.dataset = get_object_or_404(models.Dataset, pk=kwargs.get('pk'))
        return super(DatasetDataView, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        result = super(DatasetDataView, self).create(request, *args, **kwargs)
        return result

    def post(self, request, *args, **kwargs):
        if not self.dataset:
            self.dataset = get_object_or_404(models.Dataset, pk=kwargs.get('pk'))
        return super(DatasetDataView, self).post(request, *args, **kwargs)


class GenericRecordViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.GenericRecord.objects.all()
    serializer_class = serializers.GenericRecordSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('id', 'site', 'dataset__id', 'dataset__name')


class ObservationViewSet(GenericRecordViewSet):
    queryset = models.Observation.objects.all()
    serializer_class = serializers.ObservationSerializer
    filter_fields = GenericRecordViewSet.filter_fields + ('datetime',)


class SpeciesObservationViewSet(ObservationViewSet, SpeciesMixin):
    queryset = models.SpeciesObservation.objects.all()
    serializer_class = serializers.SpeciesObservationSerializer
    filter_fields = ObservationViewSet.filter_fields + ('species_name', 'name_id',)

    def get_serializer_context(self):
        ctx = super(SpeciesObservationViewSet, self).get_serializer_context()
        if 'species_mapping' not in ctx:
            ctx['species_mapping'] = self.species_facade_class().name_id_by_species_name()
        return ctx


class StatisticsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        data = OrderedDict()
        qs = Project.objects.all()
        data['projects'] = {
            'total': qs.count()
        }
        qs = Dataset.objects.all()
        data['datasets'] = OrderedDict([
            ('total', qs.count()),
            ('generic', {
                'total': qs.filter(type=Dataset.TYPE_GENERIC).count()
            }),
            ('observation', {
                'total': qs.filter(type=Dataset.TYPE_OBSERVATION).count()
            }),
            ('speciesObservation', {
                'total': qs.filter(type=Dataset.TYPE_SPECIES_OBSERVATION).count()
            }),
        ])
        # records
        generic_records_count = GenericRecord.objects.count()
        observation_record_count = Observation.objects.count()
        species_observation_count = SpeciesObservation.objects.count()
        data['records'] = OrderedDict([
            ('total', generic_records_count + observation_record_count + species_observation_count),
            ('generic', {
                'total': generic_records_count
            }),
            ('observation', {
                'total': observation_record_count
            }),
            ('speciesObservation', {
                'total': species_observation_count
            }),
        ])
        return Response(data)


class WhoamiView(APIView):
    serializers = serializers.SimpleUserSerializer

    def get(self, request, **kwargs):
        data = {}
        if request.user.is_authenticated():
            data = self.serializers(request.user).data
        return Response(data)
