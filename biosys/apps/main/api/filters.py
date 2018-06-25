from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from main import models


class UserFilterSet(filters.FilterSet):
    project__id = filters.CharFilter(name='project', method='filter_project_id_custodians')
    project__name = filters.CharFilter(name='project', method='filter_project_name_custodians')
    project__code = filters.CharFilter(name='project', method='filter_project_code_custodians')

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
    # TODO: Add custom filter field for JSONField
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
            'published': ['exact'],
            'consumed': ['exact'],
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
