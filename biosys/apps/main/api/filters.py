from django_filters import rest_framework as filters

from main import models


class DatasetFilterSet(filters.FilterSet):
    class Meta:
        model = models.Dataset
        fields = {
            'id': ['exact'],
            'name': ['exact'],
            'code': ['exact'],
            'type': ['exact'],
            'project': ['exact'],
            'project__id': ['exact'],
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
            'id': ['exact'],
            'dataset__id': ['exact'],
            'dataset__name': ['exact'],
            'dataset__project__id': ['exact'],
            'dataset__project__name': ['exact'],
            'datetime': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'species_name': ['iexact'],
            'name_id': ['exact'],
            'created': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'last_modified': ['exact', 'gt', 'lt', 'gte', 'lte'],
            'published': ['exact'],
            'consumed': ['exact'],
            'site': ['exact'],
            'site__id': ['exact'],
            'site__code': ['exact'],
            'site__name': ['exact'],
            'client_id': ['exact']
        }


class MediaFilterSet(filters.FilterSet):
    class Meta:
        model = models.Media
        fields = [
            'id',
            'record',
            'record__id',
            'record__species_name',
            'record__dataset__id',
            'record__dataset__name',
            'record__dataset__code',
            'record__dataset__project__id',
            'record__dataset__project__name',
            'record__dataset__project__code',
        ]
