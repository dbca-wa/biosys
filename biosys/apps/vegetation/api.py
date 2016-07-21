from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.resources import ModelResource

from main.admin import readonly_user
from main.api import (BaseMetaClass, AbstractLookupResource,
                      SpeciesObservationResource, AbstractSiteVisitObservationResource)
from . import models


class VegetationVisitResource(AbstractSiteVisitObservationResource):

    class Meta(BaseMetaClass):
        queryset = models.VegetationVisit.objects.all()
        filtering = {
            'id': ALL,
            'site_visit': ALL_WITH_RELATIONS,
            'collector': ALL,
            'date': ALL,
        }


class AbstractVegObservationResource(ModelResource):
    """Abstract ModelResource class, includes a link field to vegetation_visit.
    """
    vegetation_visit = fields.ToOneField(
        VegetationVisitResource, attribute='vegetation_visit', readonly=True, full=True)

    class Meta(BaseMetaClass):
        limit = 0
        max_limit = 0
        filtering = {
            'id': ALL,
            'vegetation_visit': ALL_WITH_RELATIONS,
        }

    def get_object_list(self, request):
        """Filter the queryset based upon the request user.
        """
        object_list = super(AbstractVegObservationResource, self).get_object_list(request)
        if readonly_user(request.user):
            return object_list.filter(vegetation_visit__site_visit__data_status='approved')
        else:
            return object_list


class StratumSpeciesResource(AbstractVegObservationResource):
    significance = fields.ToOneField(
        'vegetation.api.SignificanceLookupResource', attribute='significance',
        readonly=True, null=True, full=True)
    stratum = fields.ToOneField(
        'vegetation.api.StratumLookupResource', attribute='stratum',
        readonly=True, null=True, full=True)
    species = fields.ToOneField(
        SpeciesObservationResource, attribute='species', readonly=True, null=True, full=True)
    condition = fields.ToOneField(
        'vegetation.api.ConditionLookupResource', attribute='condition',
        readonly=True, null=True, full=True)

    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.StratumSpecies.objects.all()
        filtering = {
            'id': ALL,
            'vegetation_visit': ALL_WITH_RELATIONS,
            'collector_no': ALL,
            'significance': ALL_WITH_RELATIONS,
            'stratum': ALL_WITH_RELATIONS,
            'species': ALL_WITH_RELATIONS,
            'condition': ALL_WITH_RELATIONS,
        }


class TransectObservationResource(AbstractVegObservationResource):
    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.TransectObservation.objects.all()


class TransectDistinctChangesResource(AbstractVegObservationResource):
    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.TransectDistinctChanges.objects.all()


class BasalBitterlichObservationResource(AbstractVegObservationResource):
    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.BasalBitterlichObservation.objects.all()


class ErosionPegResource(AbstractVegObservationResource):
    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.ErosionPeg.objects.all()


class PegObservationResource(AbstractVegObservationResource):
    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.PegObservation.objects.all()


class GroundCoverSummaryResource(AbstractVegObservationResource):
    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.GroundCoverSummary.objects.all()


class StratumSummaryResource(AbstractVegObservationResource):
    stratum = fields.ToOneField(
        'vegetation.api.StratumLookupResource', attribute='stratum',
        readonly=True, null=True, full=True)

    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.StratumSummary.objects.all()
        filtering = {
            'id': ALL,
            'vegetation_visit': ALL_WITH_RELATIONS,
            'stratum': ALL_WITH_RELATIONS,
        }


class DisturbanceIndicatorResource(AbstractVegObservationResource):
    evidence_recent_fire = fields.ToOneField(
        'vegetation.api.EvidenceRecentFireLookupResource', attribute='evidence_recent_fire',
        readonly=True, null=True, full=True)
    fire_intensity = fields.ToOneField(
        'vegetation.api.FireIntensityLookupResource', attribute='fire_intensity',
        readonly=True, null=True, full=True)
    cattle_sighted = fields.ToOneField(
        'vegetation.api.CattleSightedLookupResource', attribute='cattle_sighted',
        readonly=True, null=True, full=True)
    grazing_level = fields.ToOneField(
        'vegetation.api.GrazingLevelLookupResource', attribute='grazing_level',
        readonly=True, null=True, full=True)
    tracks_trampling = fields.ToOneField(
        'vegetation.api.TracksTramplingLookupResource', attribute='tracks_trampling',
        readonly=True, null=True, full=True)
    cattle_dung = fields.ToOneField(
        'vegetation.api.CattleDungLookupResource', attribute='cattle_dung',
        readonly=True, null=True, full=True)
    pigs = fields.ToOneField(
        'vegetation.api.FeralEvidenceLookupResource', attribute='pigs',
        readonly=True, null=True, full=True)
    cats = fields.ToOneField(
        'vegetation.api.FeralEvidenceLookupResource', attribute='cats',
        readonly=True, null=True, full=True)
    horses_donkeys = fields.ToOneField(
        'vegetation.api.FeralEvidenceLookupResource', attribute='horses_donkeys',
        readonly=True, null=True, full=True)
    camels = fields.ToOneField(
        'vegetation.api.FeralEvidenceLookupResource', attribute='camels',
        readonly=True, null=True, full=True)

    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.DisturbanceIndicator.objects.all()


class PlantObservationResource(AbstractVegObservationResource):
    species = fields.ToOneField(
        SpeciesObservationResource, attribute='species', readonly=True, null=True, full=True)

    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.PlantObservation.objects.all()
        filtering = {
            'id': ALL,
            'vegetation_visit': ALL_WITH_RELATIONS,
            'species': ALL_WITH_RELATIONS,
        }


class BiodiversityIndicatorResource(AbstractVegObservationResource):
    fauna_habitat = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='fauna_habitat', readonly=True, full=True)
    veg_cover = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='veg_cover', readonly=True, full=True)
    crevices = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='crevices', readonly=True, full=True)
    tree_hollows = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='tree_hollows', readonly=True, full=True)
    logs = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='logs', readonly=True, full=True)
    food_avail = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='food_avail', readonly=True, full=True)
    fruiting = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='fruiting', readonly=True, full=True)
    flowering = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='flowering', readonly=True, full=True)
    seeding = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='seeding', readonly=True, full=True)
    termites = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='termites', readonly=True, full=True)
    traces = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='traces', readonly=True, full=True)
    sightings = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='sightings', readonly=True, full=True)
    tracks = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='tracks', readonly=True, full=True)
    scats = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='scats', readonly=True, full=True)
    others = fields.ToOneField(
        'vegetation.api.BiodiversityIndicatorLookupResource',
        attribute='others', readonly=True, full=True)

    class Meta(AbstractVegObservationResource.Meta):
        queryset = models.BiodiversityIndicator.objects.all()


#########################
# Lookup resources
#########################


class SignificanceLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.SignificanceLookup.objects.all()


class StratumLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.StratumLookup.objects.all()


class ConditionLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.ConditionLookup.objects.all()


class EvidenceRecentFireLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.EvidenceRecentFireLookup.objects.all()


class FireIntensityLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.FireIntensityLookup.objects.all()


class CattleSightedLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.CattleSightedLookup.objects.all()


class GrazingLevelLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.GrazingLevelLookup.objects.all()


class TracksTramplingLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.TracksTramplingLookup.objects.all()


class CattleDungLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.CattleDungLookup.objects.all()


class FeralEvidenceLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.FeralEvidenceLookup.objects.all()


class BiodiversityIndicatorLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.BiodiversityIndicatorLookup.objects.all()
