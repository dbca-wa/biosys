from __future__ import absolute_import, unicode_literals, print_function, division

import datetime
import logging
from collections import OrderedDict
from os import path

from django.contrib.auth import get_user_model, logout
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.conf import settings
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import viewsets, generics, status
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser, JSONParser
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS
from rest_framework.views import APIView, Response
from rest_framework.settings import import_from_string

from main import models, constants
from main.api import serializers
from main.api import filters
from main.api.helpers import to_bool
from main.api.uploaders import SiteUploader, FileReader, RecordCreator, DataPackageBuilder
from main.api.validators import get_record_validator_for_dataset
from main.models import Project, Site, Dataset, Record
from main.utils_auth import is_admin, can_create_user
from main.api.exporters import DefaultExporter
from main.utils_http import WorkbookResponse, CSVFileResponse
from main.utils_species import NoSpeciesFacade
from main.utils_misc import search_json_fields, order_by_json_field


logger = logging.getLogger(__name__)


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
        user = request.user
        if method == 'DELETE':
            return False
        elif method == 'POST':
            return can_create_user(user)
        else:
            return user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object level. Will be called only if the global level passed (see above).
        Note: it won't be called for a Create (POST) method
        """
        is_owner = (request.user == obj)
        return request.method in SAFE_METHODS or is_admin(request.user) or is_owner


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (UserPermission,)
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer
    filter_class = filters.UserFilterSet

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.CreateUserSerializer
        else:
            return self.serializer_class


class ProgramViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Program.objects.all()
    serializer_class = serializers.ProgramSerializer
    filter_class = filters.ProgramFilterSet


class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
    filter_class = filters.ProjectFilterSet


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


class FormViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    serializer_class = serializers.FormSerializer
    queryset = models.Form.objects.all().distinct()


class DatasetViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    serializer_class = serializers.DatasetSerializer
    filter_class = filters.DatasetFilterSet
    queryset = models.Dataset.objects.all().distinct()


class DatasetRecordsPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return \
            request.method in SAFE_METHODS \
            or is_admin(user) \
            or (hasattr(view, 'dataset') and view.dataset and (view.dataset.is_custodian(user) or view.dataset.is_data_engineer(user)))


class SpeciesMixin(object):
    species_facade_class = NoSpeciesFacade
    if settings.SPECIES_FACADE_CLASS:
        try:
            species_facade_class = import_from_string(settings.SPECIES_FACADE_CLASS, 'SPECIES_FACADE_CLASS')
        except Exception as e:
            msg = "Error while importing the species facade class {}".format(settings.SPECIES_FACADE_CLASS)
            logger.exception(msg)


class DatasetRecordsView(generics.ListAPIView, generics.DestroyAPIView, SpeciesMixin):
    permission_classes = (IsAuthenticated, DatasetRecordsPermission)
    # TODO: the filters don't appear in the swagger
    filter_class = filters.RecordFilterSet

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
    # TODO: implement a patch for the data JSON field. Ability to partially update some of the data properties.
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Record.objects.all()
    serializer_class = serializers.RecordSerializer
    filter_class = filters.RecordFilterSet

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
        output = self.request.query_params.get('output')
        if output in ['xlsx', 'csv']:
            if not self.dataset:
                return Response(status=status.HTTP_400_BAD_REQUEST, data="No dataset specified")
            qs = self.filter_queryset(self.get_queryset())

            # exporter class
            exporter_class = DefaultExporter
            if hasattr(settings, 'EXPORTER_CLASS') and settings.EXPORTER_CLASS:
                try:
                    exporter_class = import_from_string(settings.EXPORTER_CLASS, 'EXPORTER_CLASS')
                except Exception:
                    logger.exception("Error while importing exporter class: {}".format(settings.EXPORTER_CLASS))

            exporter = exporter_class(self.dataset, qs)
            now = datetime.datetime.now()
            file_name = self.dataset.name + '_' + now.strftime('%Y-%m-%d-%H%M%S')
            if output == 'xlsx':
                file_name += '.xlsx'
                wb = exporter.to_workbook()
                response = WorkbookResponse(wb, file_name)
            else:
                # csv
                file_name += '.csv'
                response = CSVFileResponse(file_name=file_name)
                exporter.to_csv(response)
            return response
        else:
            return super(RecordViewSet, self).list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self.dataset = instance.dataset
        return super(RecordViewSet, self).update(request, *args, **kwargs)


class MediaViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.Media.objects.all()
    filter_class = filters.MediaFilterSet
    parser_classes = (FormParser, MultiPartParser, JSONParser)

    def get_serializer_class(self):
        if self.request.content_type.startswith('application/json'):
            return serializers.Base64MediaSerializer
        else:
            # multipart form serializer
            return serializers.MediaSerializer


class ProjectMediaViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.ProjectMedia.objects.all()
    filter_class = filters.ProjectMediaFilterSet
    parser_classes = (FormParser, MultiPartParser, JSONParser)

    def get_serializer_class(self):
        if self.request.content_type.startswith('application/json'):
            return serializers.Base64ProjectMediaSerializer
        else:
            # multipart form serializer
            return serializers.ProjectMediaSerializer


class DatasetMediaViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, DRYPermissions)
    queryset = models.DatasetMedia.objects.all()
    filter_class = filters.DatasetMediaFilterSet
    parser_classes = (FormParser, MultiPartParser, JSONParser)

    def get_serializer_class(self):
        if self.request.content_type.startswith('application/json'):
            return serializers.Base64DatasetMediaSerializer
        else:
            # multipart form serializer
            return serializers.DatasetMediaSerializer


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
    serializers = serializers.WhoAmISerializer

    def get(self, request, **kwargs):
        data = {}
        if request.user.is_authenticated:
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
            infer_dataset_type = to_bool(request.data.get('infer_dataset_type', True))
            if file_obj is None:
                response_data = {
                    'errors': 'Missing file'
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            file_format = FileReader.get_uploaded_file_format(file_obj)
            if file_format == FileReader.NOT_SUPPORTED_FORMAT:
                msg = "Wrong file type {}. Should be one of: {}".format(file_obj.content_type,
                                                                        FileReader.SUPPORTED_TYPES)
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            dataset_name = path.splitext(file_obj.name)[0]
            builder = DataPackageBuilder.infer_from_file(
                file_obj.temporary_file_path(),
                name=dataset_name,
                format_=file_format,
                infer_dataset_type=infer_dataset_type
            )
            if builder.valid:
                response_data = {
                    'name': builder.title,  # use the data-package title instead of name (name is a slug)
                    'type': builder.dataset_type,
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
