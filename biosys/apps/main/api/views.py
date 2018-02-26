from __future__ import absolute_import, unicode_literals, print_function, division

import datetime
from collections import OrderedDict
from os import path

from django.contrib.auth import get_user_model, logout
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.db.models import Q
from django.shortcuts import get_object_or_404
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, filters, generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.views import APIView, Response

from main import models, constants
from main.api import serializers
from main.api.helpers import to_bool
from main.api.uploaders import SiteUploader, FileReader, RecordCreator, DataPackageBuilder
from main.api.validators import get_record_validator_for_dataset
from main.models import Project, Site, Dataset, Record
from main.utils_auth import is_admin
from main.utils_data_package import Exporter
from main.utils_http import WorkbookResponse
from main.utils_species import HerbieFacade
from main.utils_misc import search_json_fields, order_by_json_field


class UserPermission(BasePermission):
    """
    Rules:
    Get: authenticated
    Update: admin or user itself
    Create: admin
    Delete: forbidden through API
    """

    def has_permission(self, request, view):
        """
        Global level.
        Reject Delete and Create for non admin.
        The rest will be checked at object level (below)
        """
        method = request.method
        if method == 'DELETE':
            return False
        if method == 'POST':
            return is_admin(request.user)
        return True

    def has_object_permission(self, request, view, obj):
        """
        Object level. Will be called only if the global level passed (see above).
        Note: it won't be called for a Create (POST) method
        """
        is_owner = (request.user == obj)
        return request.method in SAFE_METHODS or is_admin(request.user) or is_owner


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, UserPermission,)
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('username', 'first_name', 'last_name', 'email')


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('id', 'name', 'custodians', 'code')


class ProjectPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return \
            request.method in SAFE_METHODS \
            or is_admin(user) \
            or (hasattr(view, 'project') and view.project and view.project.is_custodian(user))


class ProjectSitesView(generics.ListCreateAPIView, generics.DestroyAPIView):
    permission_classes = (IsAuthenticated, ProjectPermission)
    serializer_class = serializers.SiteSerializer

    def __init__(self, **kwargs):
        super(ProjectSitesView, self).__init__(**kwargs)
        self.project = None

    def dispatch(self, request, *args, **kwargs):
        """
        Intercept any request to set the project from the pk
        This is necessary for the ProjectPermission.
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

    def destroy(self, request, *args, **kwargs):
        site_ids = request.data
        if isinstance(site_ids, list):
            qs = Site.objects.filter(project=self.project, id__in=site_ids)
        elif site_ids == 'all':
            qs = Site.objects.filter(project=self.project)
        else:
            return Response("A list of site ids must be provided or 'all'", status=status.HTTP_400_BAD_REQUEST)
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectSitesUploadView(APIView):
    permission_classes = (IsAuthenticated, ProjectPermission)
    parser_classes = (FormParser, MultiPartParser)

    def dispatch(self, request, *args, **kwargs):
        """
        Intercept any request to set the project from the pk.
        This is necessary for the ProjectPermission.
        :param request:
        """
        self.project = get_object_or_404(Project, pk=self.kwargs.get('pk'))
        return super(ProjectSitesUploadView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        file_obj = request.data['file']
        if file_obj.content_type not in SiteUploader.SUPPORTED_TYPES:
            msg = "Wrong file type {}. Should be one of: {}".format(file_obj.content_type, SiteUploader.SUPPORTED_TYPES)
            return Response(msg, status=status.HTTP_501_NOT_IMPLEMENTED)

        uploader = SiteUploader(file_obj, self.project)
        data = {}
        # return an item by parsed row
        # {1: { site: pk|None, error: msg|None}, 2:...., 3:... }

        has_error = False
        row = 0
        for site, error in uploader:
            row += 1
            result = {
                'site': None,
                'error': None
            }
            if site:
                result['site'] = site.pk
            if error:
                has_error = True
                result['error'] = str(error)
            data[row] = result
        uploader.close()
        status_code = status.HTTP_200_OK if not has_error else status.HTTP_400_BAD_REQUEST
        return Response(data, status=status_code)


class SiteViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Site.objects.all()
    serializer_class = serializers.SiteSerializer
    filter_fields = ('id', 'name', 'code', 'project__name', 'project__code', 'project__id')

    def perform_update(self, serializer):
        """
        Use case: A site has its geometry updated, all records related to the site having the same geometry
        should be updated accordingly.
        :param serializer:
        :return:
        """
        instance = self.get_object()
        if instance.geometry is not None:
            records = Record.objects.filter(site=instance, geometry=instance.geometry)
        else:
            records = Record.objects.none()
        serializer.save()
        instance.refresh_from_db()
        if instance.geometry is not None:
            records.update(geometry=instance.geometry)


class DatasetViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    serializer_class = serializers.DatasetSerializer

    def get_queryset(self):
        queryset = models.Dataset.objects.all()

        name = self.request.query_params.get('name', None)
        if name is not None:
            queryset = queryset.filter(name=name)

        project = self.request.query_params.get('project', None)
        if project is not None:
            queryset = queryset.filter(project=project)

        type_ = self.request.query_params.get('type', None)
        if type_ is not None:
            queryset = queryset.filter(type=type_)

        datetime_start = self.request.query_params.get('record__datetime__start', None)
        if datetime_start is not None:
            queryset = queryset.filter(record__datetime__gte=datetime_start)

        datetime_end = self.request.query_params.get('record__datetime__end', None)
        if datetime_end is not None:
            queryset = queryset.filter(record__datetime__lte=datetime_end)

        species_name = self.request.query_params.get('record__species_name', None)
        if species_name is not None:
            queryset = queryset.filter(record__species_name=species_name)

        name_id = self.request.query_params.get('record__name_id', None)
        if name_id is not None:
            queryset = queryset.filter(record__name_id=name_id)

        return queryset.distinct()


class DatasetRecordsPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return \
            request.method in SAFE_METHODS \
            or is_admin(user) \
            or (hasattr(view, 'dataset') and view.dataset and view.dataset.is_custodian(user))


class SpeciesMixin(object):
    species_facade_class = HerbieFacade


class DatasetRecordsView(generics.ListAPIView, generics.DestroyAPIView, SpeciesMixin):
    permission_classes = (IsAuthenticated, DatasetRecordsPermission)

    def __init__(self, **kwargs):
        super(DatasetRecordsView, self).__init__(**kwargs)
        self.dataset = None

    def dispatch(self, request, *args, **kwargs):
        """
        Intercept any request to set the dataset.
        This is necessary for the DatasetRecordsPermission
        :param request:
        """
        self.dataset = get_object_or_404(models.Dataset, pk=kwargs.get('pk'))
        return super(DatasetRecordsView, self).dispatch(request, *args, **kwargs)

    def get_serializer_class(self):
        return serializers.RecordSerializer

    def get_serializer(self, *args, **kwargs):
        kwargs["many"] = True
        ser = super(DatasetRecordsView, self).get_serializer(*args, **kwargs)
        # TODO: find a better way to initialize the dataset field of the serializer
        if hasattr(ser, 'initial_data'):
            for r in ser.initial_data:
                r['dataset'] = self.dataset.pk
        return ser

    def get_serializer_context(self):
        ctx = super(DatasetRecordsView, self).get_serializer_context()
        if self.dataset:
            ctx['dataset'] = self.dataset
            if self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION and 'species_naming_facade_class' not in ctx:
                ctx['species_naming_facade_class'] = self.species_facade_class
        return ctx

    def get_queryset(self):
        if self.dataset:
            queryset = self.dataset.record_queryset

            search_param = self.request.query_params.get('search')
            if search_param is not None:
                field_info = {
                    'data': self.dataset.schema.field_names,
                    'source_info': ['file_name', 'row']
                }

                queryset = search_json_fields(queryset, field_info, search_param)

            ordering_param = self.request.query_params.get('ordering')
            if ordering_param is not None:
                queryset = order_by_json_field(queryset, 'data', self.dataset.schema.field_names, ordering_param)
                queryset = order_by_json_field(queryset, 'source_info', ['file_name', 'row'], ordering_param)

            return queryset
        else:
            return Dataset.objects.none()

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
        return super(DatasetRecordsView, self).list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        record_ids = request.data
        if isinstance(record_ids, list):
            qs = Record.objects.filter(dataset=self.dataset, id__in=record_ids)
        elif record_ids == 'all':
            qs = Record.objects.filter(dataset=self.dataset)
        else:
            return Response("A list of record ids must be provided or 'all'", status=status.HTTP_400_BAD_REQUEST)
        qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecordViewSet(viewsets.ModelViewSet, SpeciesMixin):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Record.objects.all()
    serializer_class = serializers.RecordSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    filter_fields = ('id', 'site', 'dataset__id', 'dataset__name', 'dataset__project__id', 'dataset__project__name',
                     'datetime', 'species_name', 'name_id')

    def __init__(self, **kwargs):
        super(RecordViewSet, self).__init__(**kwargs)
        self.dataset = None
        # validation mode
        self.strict = False

    def get_dataset(self, request, *args, **kwargs):
        ds = None
        pk = request.data['dataset'] if 'dataset' in request.data else request.query_params.get('dataset__id')
        if pk:
            ds = get_object_or_404(Dataset, pk=pk)
        else:
            name = request.query_params.get('dataset__name')
            if name:
                ds = get_object_or_404(Dataset, name=name)
        return ds

    def get_queryset(self):
        queryset = super(RecordViewSet, self).get_queryset()
        if self.dataset:
            # add some specific json field queries (postgres)
            search_param = self.request.query_params.get('search')
            if search_param is not None:
                field_info = {
                    'data': self.dataset.schema.field_names,
                    'source_info': ['file_name', 'row']
                }

                queryset = search_json_fields(queryset, field_info, search_param)

            ordering_param = self.request.query_params.get('ordering')
            if ordering_param is not None:
                queryset = order_by_json_field(queryset, 'data', self.dataset.schema.field_names, ordering_param)
                queryset = order_by_json_field(queryset, 'source_info', ['file_name', 'row'], ordering_param)

        return queryset

    def initial(self, request, *args, **kwargs):
        result = super(RecordViewSet, self).initial(request, *args, **kwargs)
        self.dataset = self.get_dataset(request, *args, **kwargs)
        self.strict = 'strict' in request.query_params
        return result

    def get_serializer_context(self):
        ctx = super(RecordViewSet, self).get_serializer_context()
        ctx['dataset'] = self.dataset
        ctx['strict'] = self.strict
        if self.dataset and self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
            ctx['species_naming_facade_class'] = self.species_facade_class
        return ctx

    def list(self, request, *args, **kwargs):
        # don't use 'format' param as it's kind of reserved by DRF
        if self.request.query_params.get('output') == 'xlsx':
            if not self.dataset:
                return Response(status=status.HTTP_400_BAD_REQUEST, data="No dataset specified")
            qs = self.filter_queryset(self.get_queryset())
            exporter = Exporter(self.dataset, qs)
            wb = exporter.to_workbook()
            now = datetime.datetime.now()
            file_name = self.dataset.name + '_' + now.strftime('%Y-%m-%d-%H%M%S') + '.xlsx'
            response = WorkbookResponse(wb, file_name)
            return response
        else:
            return super(RecordViewSet, self).list(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        # apply the model filters: filter_fields
        queryset = super(RecordViewSet, self).filter_queryset(queryset)
        # other filters
        datetime_start = self.request.query_params.get('datetime__start', None)
        if datetime_start is not None:
            queryset = queryset.filter(datetime__gte=datetime_start)
        datetime_end = self.request.query_params.get('datetime__end', None)
        if datetime_end is not None:
            queryset = queryset.filter(datetime__lte=datetime_end)
        return queryset

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.dataset = instance.dataset
        return super(RecordViewSet, self).update(request, *args, **kwargs)


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
        total_records_count = Record.objects.count()
        generic_record_count = Record.objects.filter(dataset__type=Dataset.TYPE_GENERIC).count()
        observation_record_count = Record.objects.filter(dataset__type=Dataset.TYPE_OBSERVATION).count()
        species_observation_count = Record.objects.filter(dataset__type=Dataset.TYPE_SPECIES_OBSERVATION).count()
        data['records'] = OrderedDict([
            ('total', total_records_count),
            ('generic', {
                'total': generic_record_count
            }),
            ('observation', {
                'total': observation_record_count
            }),
            ('speciesObservation', {
                'total': species_observation_count
            }),
        ])
        qs = Site.objects.all()
        data['sites'] = {
            'total': qs.count()
        }
        return Response(data)


class WhoamiView(APIView):
    serializers = serializers.SimpleUserSerializer

    def get(self, request, **kwargs):
        data = {}
        if request.user.is_authenticated():
            data = self.serializers(request.user).data
        return Response(data)


class DatasetUploadRecordsView(APIView, SpeciesMixin):
    """
    Upload file for records (xlsx, csv)
    """
    permission_classes = (IsAuthenticated, DatasetRecordsPermission)
    parser_classes = (FormParser, MultiPartParser)

    def dispatch(self, request, *args, **kwargs):
        """
        Intercept any request to set the dataset from the pk.
        This is necessary for the DatasetRecordsPermission.
        :param request:
        """
        self.dataset = get_object_or_404(models.Dataset, pk=kwargs.get('pk'))
        return super(DatasetUploadRecordsView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        file_obj = request.data['file']
        create_site = 'create_site' in request.data and to_bool(request.data['create_site'])
        delete_previous = 'delete_previous' in request.data and to_bool(request.data['delete_previous'])
        strict = 'strict' in request.data and to_bool(request.data['strict'])

        if file_obj.content_type not in FileReader.SUPPORTED_TYPES:
            msg = "Wrong file type {}. Should be one of: {}".format(file_obj.content_type, SiteUploader.SUPPORTED_TYPES)
            return Response(msg, status=status.HTTP_501_NOT_IMPLEMENTED)

        if delete_previous:
            self.dataset.record_queryset.delete()
        generator = FileReader(file_obj)
        validator = get_record_validator_for_dataset(self.dataset)
        validator.schema_error_as_warning = not strict
        creator = RecordCreator(self.dataset, generator,
                                validator=validator, create_site=create_site, commit=True,
                                species_facade_class=self.species_facade_class)
        data = []
        has_error = False
        row = 1  # starts at 1 to match excel row id
        for record, validator_result in creator:
            row += 1
            result = {
                'row': row
            }
            if validator_result.has_errors:
                has_error = True
            else:
                result['recordId'] = record.id
            result.update(validator_result.to_dict())
            data.append(result)
        status_code = status.HTTP_200_OK if not has_error else status.HTTP_400_BAD_REQUEST
        return Response(data, status=status_code)


class SpeciesView(APIView, SpeciesMixin):
    def get(self, request, *args, **kwargs):
        """
        Get a list of all species name present in the system
        :return: a list of species name.
        """
        qs = Record.objects.exclude(species_name__isnull=True)
        qs = self.filter_queryset(qs)
        # we output just the species name
        data = qs \
            .distinct('species_name') \
            .order_by('species_name') \
            .values_list('species_name', flat=True)
        return Response(data=data)

    def filter_queryset(self, queryset):
        query = Q()
        # search
        search = self.request.query_params.get('search')
        if search:
            query &= Q(species_name__icontains=search)
        # strict
        strict = to_bool(self.request.query_params.get('strict', False))
        if strict:
            query &= ~Q(name_id=-1)
        return queryset.filter(query)


class LogoutView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Logout of the system.
        """
        logout(request)

        return Response(status=status.HTTP_204_NO_CONTENT)


class GeoConvertView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.GeoConvertSerializer
    OUTPUT_GEOMETRY = "geometry"
    OUTPUT_DATA = "data"

    output = OUTPUT_GEOMETRY  # set it the url

    def to_geometry(self, dataset, record_data):
        try:
            schema = dataset.schema
            geom_parser = schema.geometry_parser
            geometry = geom_parser.from_record_to_geometry(
                record_data,
                default_srid=dataset.project.datum or constants.MODEL_SRID
            )
            # we output in WGS84
            geometry.transform(constants.MODEL_SRID)
            serializer = self.serializer_class({
                'geometry': geometry,
                'data': record_data
            })
            return Response(serializer.data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    def to_data(self, dataset, geometry, record_data):
        try:
            schema = dataset.schema
            default_srid = dataset.project.datum or constants.MODEL_SRID
            geom_parser = schema.geometry_parser
            record_data = geom_parser.from_geometry_to_record(geometry, record_data, default_srid=default_srid)
            serializer = self.serializer_class({
                'data': record_data,
                'geometry': geometry
            })
            return Response(serializer.data)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, **kwargs):
        dataset = get_object_or_404(Dataset, pk=kwargs.get('pk'))
        if dataset.type == Dataset.TYPE_GENERIC:
            return Response("Conversion not available for records from generic dataset",
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            record_data = serializer.validated_data.get('data', {})
            if self.output == self.OUTPUT_GEOMETRY:
                return self.to_geometry(dataset, record_data)
            elif self.output == self.OUTPUT_DATA:
                geometry = serializer.validated_data.get('geometry')
                if geometry is None:
                    return Response("geometry is required.",
                                    status=status.HTTP_400_BAD_REQUEST)
                if not geometry.srid:
                    geometry.srid = constants.MODEL_SRID
                return self.to_data(dataset, geometry, record_data)
            else:
                return Response("Output format not valid {}. Should be one of:{}"
                                .format(self.output, [self.OUTPUT_DATA, self.OUTPUT_GEOMETRY]),
                                status=status.HTTP_400_BAD_REQUEST)


class InferDatasetView(APIView):
    """
    Accept a xlsx or csv file and return a datapackage with schema inferred
    """
    permission_classes = (IsAuthenticated,)
    parser_classes = (FormParser, MultiPartParser)

    def post(self, request, *args, **kwargs):
        try:
            # we want the uploaded file to be physically saved on disk (no InMemoryFileUploaded) so we force the file
            # upload handlers of the request.
            request.upload_handlers = [TemporaryFileUploadHandler(request)]
            file_obj = request.data.get('file')
            if file_obj is None:
                response_data = {
                    'errors': 'Missing file'
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            if file_obj.content_type not in FileReader.SUPPORTED_TYPES:
                msg = "Wrong file type {}. Should be one of: {}".format(file_obj.content_type,
                                                                        SiteUploader.SUPPORTED_TYPES)
                return Response(msg, status=status.HTTP_501_NOT_IMPLEMENTED)
            file_format = 'csv' if file_obj.content_type in FileReader.CSV_TYPES else 'xlsx'
            dataset_name = path.splitext(file_obj.name)[0]
            builder = DataPackageBuilder.infer_from_file(
                file_obj.temporary_file_path(),
                name=dataset_name,
                format_=file_format
            )
            if builder.valid:
                response_data = {
                    'name': builder.title,  # use the data-package title instead of name (name is a slug)
                    'type': builder.infer_biosys_type(),
                    'data_package': builder.descriptor
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                errors = [str(e) for e in builder.errors]
                response_data = {
                    'errors': errors
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            response_data = {
                'errors': str(e)
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
