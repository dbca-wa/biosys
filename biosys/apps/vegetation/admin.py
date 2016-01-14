from django.contrib import admin
import reversion
from models import *
from main.admin import AbstractLookupAdmin


@admin.register(VegetationVisit)
class VegetationVisitAdmin(reversion.VersionAdmin):
    list_display = ('site_visit', 'collector', 'date')


@admin.register(BasalBitterlichObservation)
class BasalBitterlichObservationAdmin(reversion.VersionAdmin):
    pass


@admin.register(GroundCoverSummary)
class GroundCoverSummaryAdmin(reversion.VersionAdmin):
    pass


@admin.register(TransectObservation)
class TransectObservationAdmin(reversion.VersionAdmin):
    pass


@admin.register(TransectDistinctChanges)
class TransectDistinctChangesAdmin(reversion.VersionAdmin):
    pass


@admin.register(ErosionPeg)
class ErosionPegAdmin(reversion.VersionAdmin):
    list_display = ('__str__', 'vegetation_visit', 'transect_x', 'transect_y')
    list_filter = ('vegetation_visit', )


@admin.register(PegObservation)
class PegObservationAdmin(reversion.VersionAdmin):
    pass


@admin.register(StratumSummary)
class StratumSummaryAdmin(reversion.VersionAdmin):
    pass


@admin.register(StratumSpecies)
class StratumSpeciesAdmin(reversion.VersionAdmin):
    list_display = ('vegetation_visit', 'significance', 'stratum', 'species')


@admin.register(DisturbanceIndicator)
class DisturbanceIndicatorAdmin(reversion.VersionAdmin):
    pass


@admin.register(BiodiversityIndicator)
class BiodiversityIndicatorAdmin(reversion.VersionAdmin):
    pass


@admin.register(PlantObservation)
class PlantObservationAdmin(reversion.VersionAdmin):
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
