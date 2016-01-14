from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS

from main.api import AbstractSiteVisitObservationResource, SpeciesObservationResource, AbstractLookupResource, \
    DatumField
from animals.models import *


class TrapResource(AbstractSiteVisitObservationResource):
    # lookups
    trap_type = fields.ToOneField(
        'animals.api.TrapTypeLookupResource', attribute='trap_type',
        readonly=True, null=True, full=True)
    datum = DatumField(attribute='datum', readonly=True)

    class Meta(AbstractSiteVisitObservationResource.Meta):
        queryset = Trap.objects.all()


class AnimalObservationResource(AbstractSiteVisitObservationResource):
    species = fields.ToOneField(
        SpeciesObservationResource, attribute='species', readonly=True, null=True, full=True)

    # lookups
    capture_type = fields.ToOneField(
        'animals.api.CaptureTypeLookupResource', attribute='capture_type',
        readonly=True, null=True, full=True)

    sex = fields.ToOneField(
        'animals.api.SexLookupResource', attribute='sex',
        readonly=True, null=True, full=True)

    age = fields.ToOneField(
        'animals.api.AgeLookupResource', attribute='age',
        readonly=True, null=True, full=True)

    class Meta(AbstractSiteVisitObservationResource.Meta):
        queryset = AnimalObservation.objects.all()
        filtering = AbstractSiteVisitObservationResource.Meta.filtering.copy()
        filtering.update({
            'species': ALL_WITH_RELATIONS
        })


class OpportunisticObservationResource(AbstractSiteVisitObservationResource):
    species = fields.ToOneField(
        SpeciesObservationResource, attribute='species', readonly=True, null=True, full=True)
    datum = DatumField(attribute='datum', readonly=True)

    class Meta(AbstractSiteVisitObservationResource.Meta):
        queryset = OpportunisticObservation.objects.all()
        filtering = AbstractSiteVisitObservationResource.Meta.filtering.copy()
        filtering.update({
            'species': ALL_WITH_RELATIONS
        })


#########################
# Lookup resources
#########################

class TrapTypeLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = TrapTypeLookup.objects.all()


class CaptureTypeLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = CaptureTypeLookup.objects.all()


class SexLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = SexLookup.objects.all()


class AgeLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = AgeLookup.objects.all()
