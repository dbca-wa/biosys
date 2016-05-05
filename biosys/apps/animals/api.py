from tastypie import fields
from tastypie.constants import ALL_WITH_RELATIONS, ALL
from tastypie.resources import ModelResource

from main.api import AbstractSiteVisitObservationResource, SpeciesObservationResource, AbstractLookupResource, \
    DatumField, LocationLookupResource
from animals.models import *


#########################
# Lookup resources
#########################

class ObservationTypeLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = ObservationTypeLookup.objects.all()


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


#############
# Models
##############

class TrapResource(AbstractSiteVisitObservationResource):
    # lookups
    trap_type = fields.ToOneField(
        TrapTypeLookupResource, attribute='trap_type',
        readonly=True, null=True, full=True)
    datum = DatumField(attribute='datum', readonly=True)

    class Meta(AbstractSiteVisitObservationResource.Meta):
        queryset = Trap.objects.all()


class AnimalObservationResource(AbstractSiteVisitObservationResource):
    species = fields.ToOneField(
        SpeciesObservationResource, attribute='species', readonly=True, null=True, full=True)

    # lookups
    trap_type = fields.ToOneField(
        TrapTypeLookupResource, attribute='trap_type',
        readonly=True, null=True, full=True)

    capture_type = fields.ToOneField(
        CaptureTypeLookupResource, attribute='capture_type',
        readonly=True, null=True, full=True)

    sex = fields.ToOneField(
        SexLookupResource, attribute='sex',
        readonly=True, null=True, full=True)

    age = fields.ToOneField(
        AgeLookupResource, attribute='age',
        readonly=True, null=True, full=True)

    class Meta(AbstractSiteVisitObservationResource.Meta):
        queryset = AnimalObservation.objects.all()
        filtering = AbstractSiteVisitObservationResource.Meta.filtering.copy()
        filtering.update({
            'species': ALL_WITH_RELATIONS
        })


class OpportunisticObservationResource(ModelResource):
    species = fields.ToOneField(
        SpeciesObservationResource, attribute='species', readonly=True, null=True, full=True)
    datum = DatumField(attribute='datum', readonly=True)
    # lookups
    location = fields.ToOneField(
        LocationLookupResource, attribute='location',
        readonly=True, null=True, full=True)
    observation_type = fields.ToOneField(
        'ObservationTypeLookupResource', attribute='location',
        readonly=True, null=True, full=True)

    class Meta(AbstractSiteVisitObservationResource.Meta):
        queryset = OpportunisticObservation.objects.all()
        filtering = {
            'id': ALL,
            'location': ALL_WITH_RELATIONS,
            'observation_type': ALL_WITH_RELATIONS,
            'date': ALL,
            'species': ALL_WITH_RELATIONS
        }
