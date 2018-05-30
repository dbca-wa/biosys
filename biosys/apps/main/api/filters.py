from django_filters import rest_framework as filters

from main import models


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
            'site__name': ['exact']
        }
