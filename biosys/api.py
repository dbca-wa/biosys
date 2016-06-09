from tastypie.api import Api
from tastypie.http import HttpUnauthorized

from main import api as main_api
from vegetation import api as veg_api
from animals import api as animal_api


class V2Api(Api):
    """A subclass of Api that restricts anonymous access to the top_level view.
    """
    def top_level(self, request, api_name=None):
        if not request.user.is_authenticated():
            return HttpUnauthorized('Forbidden')
        return super(V2Api, self).top_level(request, api_name)


class BiosysApi(Api):
    """A subclass of Api that restricts anonymous access to the top_level view.
    """

    def top_level(self, request, api_name=None):
        if not request.user.is_authenticated():
            return HttpUnauthorized('Forbidden')
        return super(BiosysApi, self).top_level(request, api_name)


v2_api = V2Api(api_name='v2')
v2_api.register(main_api.ProjectResource())
v2_api.register(main_api.SiteResource())
v2_api.register(main_api.DataSetResource())


v1_api = BiosysApi(api_name='v1')
v1_api.register(main_api.ProjectResource())
v1_api.register(main_api.SiteResource())
v1_api.register(main_api.VisitResource())
v1_api.register(main_api.SiteVisitDataFileResource())
v1_api.register(main_api.SiteVisitResource())
v1_api.register(main_api.SpeciesObservationResource())
v1_api.register(main_api.SiteCharacteristicResource())
v1_api.register(veg_api.VegetationVisitResource())
v1_api.register(veg_api.StratumSpeciesResource())
v1_api.register(veg_api.TransectObservationResource())
v1_api.register(veg_api.TransectDistinctChangesResource())
v1_api.register(veg_api.BasalBitterlichObservationResource())
v1_api.register(veg_api.ErosionPegResource())
v1_api.register(veg_api.PegObservationResource())
v1_api.register(veg_api.GroundCoverSummaryResource())
v1_api.register(veg_api.StratumSummaryResource())
v1_api.register(veg_api.DisturbanceIndicatorResource())
v1_api.register(veg_api.PlantObservationResource())
v1_api.register(veg_api.BiodiversityIndicatorResource())
v1_api.register(veg_api.SignificanceLookupResource())
v1_api.register(veg_api.StratumLookupResource())
v1_api.register(veg_api.ConditionLookupResource())
v1_api.register(animal_api.TrapResource())
v1_api.register(animal_api.AnimalObservationResource())
v1_api.register(animal_api.OpportunisticObservationResource())
