from django_filters import rest_framework as filters

from main import models


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
