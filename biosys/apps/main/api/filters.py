import logging
import json

from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters, constants
from rest_framework.exceptions import APIException

from main import models

logger = logging.getLogger(__name__)


class FilterException(APIException):
    """
    An DRF APIException specific for filters.
    When raised DRF will handle the response correctly.
    """
    status_code = 400
    default_detail = 'There was an error while applying filters'
    default_code = 'filter_error'


class JSONFilter(filters.CharFilter):
    """
    A filter that json decode the lookup value before passing it to the queryset filter.
    Typical use for a JSONField with contains lookup
    """

    def filter(self, qs, value):
        if value in constants.EMPTY_VALUES:
            return qs
        # value should be a valid json string
        try:
            if isinstance(value, str):
                # replace single quote by double quote
                value = value.replace('\'', '\"')
                value = json.loads(value)
            qs = super(JSONFilter, self).filter(qs, value)
        except Exception as e:
            message = "Error while filtering {field}__{lookup} with value: '{value}'. {e}".format(
                field=self.field_name,
                lookup=self.lookup_expr,
                value=value,
                e=e
            )
            raise FilterException(message)

        return qs


class GeometryFilter(filters.CharFilter):
    """
    The purpose of this class is just to catch exception that can be raise while filtering the geometry.
    Typical use case: client sends an invalid geojson for a geometry__within filter.
    """

    def filter(self, qs, value):
        if value in constants.EMPTY_VALUES:
            return qs
        try:
            return super(GeometryFilter, self).filter(qs, value)
        except Exception as e:
            message = "Error while filtering {field}__{lookup} with value: '{value}'. {e}".format(
                field=self.field_name,
                lookup=self.lookup_expr,
                value=value,
                e=e
            )
            raise FilterException(message)


class UserFilterSet(filters.FilterSet):
    project__id = filters.CharFilter(field_name='project', method='filter_project_id_custodians')
    project__name = filters.CharFilter(field_name='project', method='filter_project_name_custodians')
    project__code = filters.CharFilter(field_name='project', method='filter_project_code_custodians')

    @staticmethod
    def filter_project_id_custodians(queryset, name, project_ids):
        if not isinstance(project_ids, list):
            project_ids = [project_ids]
        return queryset.filter(project__in=project_ids)

    @staticmethod
    def filter_project_name_custodians(queryset, name, project_name):
        project_ids = list(models.Project.objects.filter(name=project_name).values_list('id', flat=True))
        return UserFilterSet.filter_project_id_custodians(queryset, name, project_ids)

    @staticmethod
    def filter_project_code_custodians(queryset, name, project_code):
        project_ids = list(models.Project.objects.filter(code=project_code).values_list('id', flat=True))
        return UserFilterSet.filter_project_id_custodians(queryset, name, project_ids)

    class Meta:
        model = get_user_model()
        fields = {
            'id': ['exact', 'in'],
            'username': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
        }


class ProgramFilterSet(filters.FilterSet):
    class Meta:
        model = models.Program
        fields = '__all__'


class ProjectFilterSet(filters.FilterSet):
    class Meta:
        model = models.Project
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact'],
            'code': ['exact'],
            'custodians': ['exact'],
            'program': ['exact'],
            'program__name': ['exact'],
            'program__code': ['exact'],
            'program__data_engineers': ['exact']
        }


class DatasetFilterSet(filters.FilterSet):
    class Meta:
        model = models.Dataset
        fields = {
            'id': ['exact', 'in'],
            'name': ['exact'],
            'code': ['exact'],
            'type': ['exact'],
            'project': ['exact'],
            'project__id': ['exact', 'in'],
            'project__name': ['exact'],
            'project__code': ['exact'],
            'record__species_name': ['iexact'],
            'record__name_id': ['exact'],
            'record__datetime': ['exact', 'gt', 'lt', 'gte', 'lte']
        }


class RecordFilterSet(filters.FilterSet):
    # TODO: how to document these filters so that a description appears in the swagger.
    data__contains = JSONFilter(field_name='data', lookup_expr='contains', distinct=True)
    data__has_key = filters.CharFilter(field_name='data', lookup_expr='has_key', distinct=True)
    geometry__within = GeometryFilter(field_name='geometry', lookup_expr='within', distinct=True)

    class Meta:
        model = models.Record
        fields = {
            'id': ['exact', 'in'],
            'dataset__id': ['exact', 'in'],
            'dataset__name': ['exact'],
            'dataset__project__id': ['exact', 'in'],
            'dataset__project__name': ['exact'],
            'datetime': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'species_name': ['iexact'],
            'name_id': ['exact', 'in'],
            'created': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'last_modified': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'validated': ['exact'],
            'locked': ['exact'],
            'site': ['exact'],
            'site__id': ['exact', 'in'],
            'site__code': ['exact'],
            'site__name': ['exact'],
            'client_id': ['exact', 'in']
        }


class MediaFilterSet(filters.FilterSet):
    class Meta:
        model = models.Media
        fields = {
            'id': ['exact', 'in'],
            'record': ['exact', 'in'],
            'record__id': ['exact', 'in'],
            'record__species_name': ['exact'],
            'record__dataset__id': ['exact', 'in'],
            'record__dataset__name': ['exact'],
            'record__dataset__code': ['exact'],
            'record__dataset__project__id': ['exact', 'in'],
            'record__dataset__project__name': ['exact'],
            'record__dataset__project__code': ['exact'],
        }


class ProjectMediaFilterSet(filters.FilterSet):
    class Meta:
        model = models.ProjectMedia
        fields = {
            'id': ['exact', 'in'],
            'project': ['exact', 'in'],
            'project__id': ['exact', 'in'],
            'project__name': ['exact'],
            'project__code': ['exact'],
        }


class DatasetMediaFilterSet(filters.FilterSet):
    class Meta:
        model = models.DatasetMedia
        fields = {
            'id': ['exact', 'in'],
            'dataset': ['exact', 'in'],
            'dataset__id': ['exact', 'in'],
            'dataset__name': ['exact'],
            'dataset__code': ['exact'],
            'dataset__project': ['exact', 'in'],
            'dataset__project__id': ['exact', 'in'],
            'dataset__project__name': ['exact'],
            'dataset__project__code': ['exact'],
        }
