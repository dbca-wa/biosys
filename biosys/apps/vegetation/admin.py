from django.contrib import admin
from reversion.admin import VersionAdmin
from models import *
from main.admin import AbstractLookupAdmin


@admin.register(VegetationVisit)
class VegetationVisitAdmin(VersionAdmin):
    list_display = ('site_visit', 'collector', 'date')


@admin.register(BasalBitterlichObservation)
class BasalBitterlichObservationAdmin(VersionAdmin):
    pass


@admin.register(GroundCoverSummary)
class GroundCoverSummaryAdmin(VersionAdmin):
    pass


@admin.register(TransectObservation)
class TransectObservationAdmin(VersionAdmin):
    pass


@admin.register(TransectDistinctChanges)
class TransectDistinctChangesAdmin(VersionAdmin):
    pass


@admin.register(ErosionPeg)
class ErosionPegAdmin(VersionAdmin):
    list_display = ('__str__', 'vegetation_visit', 'transect_x', 'transect_y')
    list_filter = ('vegetation_visit', )


@admin.register(PegObservation)
class PegObservationAdmin(VersionAdmin):
    pass


@admin.register(StratumSummary)
class StratumSummaryAdmin(VersionAdmin):
    pass


@admin.register(StratumSpecies)
class StratumSpeciesAdmin(VersionAdmin):
    list_display = ('vegetation_visit', 'significance', 'stratum', 'species')


@admin.register(DisturbanceIndicator)
class DisturbanceIndicatorAdmin(VersionAdmin):
    pass


@admin.register(BiodiversityIndicator)
class BiodiversityIndicatorAdmin(VersionAdmin):
    pass


@admin.register(PlantObservation)
class PlantObservationAdmin(VersionAdmin):
    pass

#########################
# Lookups
#########################


@admin.register(ConditionLookup)
class ConditionLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(StratumLookup)
class StratumLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(SignificanceLookup)
class SignificanceLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(EvidenceRecentFireLookup)
class EvidenceRecentFireLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(FireIntensityLookup)
class FireIntensityLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(CattleSightedLookup)
class CattleSightedLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(GrazingLevelLookup)
class GrazingLevelLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(TracksTramplingLookup)
class TracksTramplingLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(CattleDungLookup)
class CattleDungLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(FeralEvidenceLookup)
class FeralEvidenceLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(BiodiversityIndicatorLookup)
class BiodiversityIndicatorLookupAdmin(AbstractLookupAdmin):
    pass
