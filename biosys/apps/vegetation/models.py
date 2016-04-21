from __future__ import unicode_literals
from django.db import models

from main.models import AbstractLookup, SpeciesObservation, AbstractSiteVisitObservation


class VegetationVisit(AbstractSiteVisitObservation):
    collector = models.CharField(max_length=150, blank=True,
                                 verbose_name="Vegetation collector", help_text="")
    date = models.DateField(null=True, blank=True,
                            verbose_name="Visit Date", help_text="")

    def __unicode__(self):
        return 'Date: {} ({})'.format(self.date, self.site_visit)


class AbstractVegetationObservation(models.Model):
    vegetation_visit = models.ForeignKey(VegetationVisit, null=False, blank=False,
                                         verbose_name="Vegetation Visit", help_text="")

    class Meta:
        abstract = True


class AbstractGroundCoverObservation(AbstractVegetationObservation):
    perennial_grass = models.FloatField(null=True, blank=True,
                                        verbose_name="Perennial Grass %", help_text="")
    annual_grass = models.FloatField(null=True, blank=True,
                                     verbose_name="Annual Grass %", help_text="")
    herb = models.FloatField(null=True, blank=True,
                             verbose_name="Herb %", help_text="")
    litter = models.FloatField(null=True, blank=True,
                               verbose_name="Litter %", help_text="")
    logs = models.FloatField(null=True, blank=True,
                             verbose_name="Logs (>50mm) %", help_text="")
    rock_gravel = models.FloatField(null=True, blank=True,
                                    verbose_name="Exposed Rock and Gravel %", help_text="")
    bare_ground = models.FloatField(null=True, blank=True,
                                    verbose_name="Bare Ground %", help_text="")
    termite_mound = models.FloatField(null=True, blank=True,
                                      verbose_name="Termite Mound %", help_text="")

    class Meta:
        abstract = True


class StratumSpecies(AbstractVegetationObservation):
    significance = models.ForeignKey('SignificanceLookup', null=True, blank=True, on_delete=models.PROTECT,
                                     verbose_name='Significance', help_text="")
    stratum = models.ForeignKey('StratumLookup', null=False, blank=False, on_delete=models.PROTECT,
                                verbose_name="Stratum", help_text="")
    species = models.ForeignKey(SpeciesObservation, null=True, blank=True,
                                verbose_name="Species", help_text="")
    collector_no = models.CharField(max_length=200, blank=True,
                                    verbose_name="Collector No", help_text="")
    avg_height = models.FloatField(null=True, blank=True,
                                   verbose_name="Average Height (m)", help_text="")
    cover = models.FloatField(null=True, blank=True,
                              verbose_name="Cover %", help_text="")
    basal_area = models.FloatField(null=True, blank=True,
                                   verbose_name="Basal Area", help_text="")
    bitterlich_cover = models.FloatField(null=True, blank=True,
                                         verbose_name="Bitterlich % cover", help_text="")
    juv_lt_2m = models.BooleanField(blank=False, default=False,
                                    verbose_name="Juvenile <2m", help_text="")
    juv_mt_2m = models.BooleanField(blank=False, default=False,
                                    verbose_name="Juvenile >2m", help_text="")
    adult = models.BooleanField(blank=False, default=False,
                                verbose_name="Adult", help_text="")
    mature = models.BooleanField(blank=False, default=False,
                                 verbose_name="Mature (at peak of prod.)", help_text="")
    condition = models.ForeignKey('ConditionLookup', null=True, blank=True,
                                  on_delete=models.PROTECT)
    flowering = models.BooleanField(default=False,
                                    verbose_name="Flowering", help_text="")
    fruiting = models.BooleanField(blank=False, default=False,
                                   verbose_name="Fruiting", help_text="")
    seeding = models.BooleanField(blank=False, default=False,
                                  verbose_name="Seeding", help_text="")
    comments = models.TextField(blank=True,
                                verbose_name="Comments", help_text="")

    class Meta:
        verbose_name_plural = 'stratum species'


class TransectObservation(AbstractGroundCoverObservation):
    low_shrub = models.FloatField(null=True, blank=True,
                                  verbose_name="Woody Subshrub %", help_text="")
    shrub = models.FloatField(null=True, blank=True,
                              verbose_name="Shrub %", help_text="")
    tree = models.FloatField(null=True, blank=True,
                             verbose_name="Tree %", help_text="")

    class Meta:
        # verbose_name = "Transect 50m Intercept Foliage"
        pass

    def __unicode__(self):
        return self.vegetation_visit.__unicode__()


class TransectDistinctChanges(AbstractVegetationObservation):
    point_of_change = models.FloatField(null=True, blank=True,
                                        verbose_name="Point of Change (m.cm)", help_text="")
    change_from = models.CharField(max_length=150, blank=True,
                                   verbose_name="Change from", help_text="")
    change_to = models.CharField(max_length=150, blank=True,
                                 verbose_name="Change to", help_text="")

    class Meta:
        verbose_name_plural = 'transect distinct changes'


class BasalBitterlichObservation(AbstractVegetationObservation):
    basal_area = models.IntegerField(null=True, blank=True,
                                     verbose_name="Basal Area", help_text="")
    bitterlich_trees = models.IntegerField(null=True, blank=True,
                                           verbose_name="Bitterlich (trees)", help_text="")
    bitterlich_shrubs = models.IntegerField(null=True, blank=True,
                                            verbose_name="Bitterlich (shrubs)", help_text="")

    class Meta:
        pass


class ErosionPeg(AbstractVegetationObservation):
    Y_DIRECTION_CHOICES = [('', ''), ('left', 'Left'), ('right', 'Right')]
    peg_ID = models.CharField(max_length=20, null=False, blank=False, default='A',
                              verbose_name="Peg ID", help_text="")
    transect_x = models.FloatField(null=False, blank=False,
                                   verbose_name="at ... m on transect", help_text="")
    transect_y = models.FloatField(null=False, blank=False,
                                   verbose_name="walk ... m", help_text="")
    y_direction = models.CharField(choices=Y_DIRECTION_CHOICES, max_length=10, default=Y_DIRECTION_CHOICES[0][0],
                                   null=True, blank=True, verbose_name="to the")

    def __unicode__(self):
        return self.peg_ID


class PegObservation(AbstractVegetationObservation):
    peg_ID = models.CharField(max_length=20, null=True, blank=True, default='A',
                              verbose_name="Peg ID", help_text="")
    intact_litter = models.FloatField(null=True, blank=True, default=0.0,
                                      verbose_name="Intact Litter (mm)", help_text="")
    frag_decay = models.FloatField(null=True, blank=True, default=0.0,
                                   verbose_name="Fragm. and decaying", help_text="")
    crust = models.FloatField(null=True, blank=True, default=0.0,
                              verbose_name="Crust", help_text="")
    worm = models.FloatField(null=True, blank=True, default=0.0,
                             verbose_name="Worm cast layer", help_text="")
    organic = models.FloatField(null=True, blank=True, default=0.0,
                                verbose_name="Organic mineral layer", help_text="")
    erosion = models.FloatField(null=True, blank=True, default=0.0,
                                verbose_name="Erosion pegs", help_text="")

    class Meta:
        pass


class GroundCoverSummary(AbstractGroundCoverObservation):
    comments = models.TextField(blank=True,
                                verbose_name='Comments', help_text="")

    class Meta:
        verbose_name_plural = 'ground cover summaries'


class StratumSummary(AbstractVegetationObservation):
    stratum = models.ForeignKey('StratumLookup', null=False, blank=False, on_delete=models.PROTECT,
                                verbose_name="Stratum", help_text="")
    growth_form = models.CharField(max_length=100, blank=False,
                                   verbose_name="Growth Form", help_text="")
    crown_cover = models.FloatField(null=False, blank=False,
                                    verbose_name="% Cover (Crown Cover)", help_text="")
    avg_height = models.FloatField(null=False, blank=False,
                                   verbose_name="Average Height (m)", help_text="")
    max_height = models.FloatField(null=False, blank=False,
                                   verbose_name="Maximum Height (m)", help_text="")

    class Meta:
        verbose_name_plural = 'stratum summaries'


class DisturbanceIndicator(AbstractVegetationObservation):
    evidence_recent_fire = models.ForeignKey('EvidenceRecentFireLookup', on_delete=models.PROTECT,
                                             null=True, blank=True,
                                             verbose_name="Evidence of recent Fire", help_text="")
    fire_intensity = models.ForeignKey('FireIntensityLookup', on_delete=models.PROTECT,
                                       null=True, blank=True,
                                       verbose_name="Fire Intensity", help_text="")
    recently_burned_percent = models.IntegerField(default=0, null=True, blank=True,
                                                  verbose_name="Recently Burned Veg in %", help_text="")
    scorch_height = models.IntegerField(default=0, null=True, blank=True,
                                        verbose_name="Scorch Height m", help_text="")
    cattle_sighted = models.ForeignKey('CattleSightedLookup', on_delete=models.PROTECT,
                                       null=True, blank=True,
                                       verbose_name="Cattle sighted", help_text="")
    grazing_level = models.ForeignKey('GrazingLevelLookup', on_delete=models.PROTECT,
                                      null=True, blank=True,
                                      verbose_name="Grazing Level", help_text="")
    tracks_trampling = models.ForeignKey('TracksTramplingLookup', on_delete=models.PROTECT,
                                         null=True, blank=True,
                                         verbose_name="Tracks and Trampling", help_text="")
    cattle_dung = models.ForeignKey('CattleDungLookup', on_delete=models.PROTECT,
                                    null=True, blank=True,
                                    verbose_name="Cattle Dung", help_text="")
    signs_damage_percent = models.IntegerField(default=0, null=True, blank=True,
                                               verbose_name="Veg affected within Site %", help_text="")
    pigs = models.ForeignKey('FeralEvidenceLookup', related_name='pigs_evidence', on_delete=models.PROTECT,
                             null=True, blank=True,
                             verbose_name="Pigs", help_text="")
    cats = models.ForeignKey('FeralEvidenceLookup', related_name='cats_evidence', on_delete=models.PROTECT,
                             null=True, blank=True,
                             verbose_name="Cats", help_text="")
    horses_donkeys = models.ForeignKey('FeralEvidenceLookup', related_name='horses_donkeys_evidence',
                                       null=True, blank=True, on_delete=models.PROTECT,
                                       verbose_name="Horses/ Donkeys", help_text="")
    camels = models.ForeignKey('FeralEvidenceLookup', related_name='camels_evidence', on_delete=models.PROTECT,
                               null=True, blank=True,
                               verbose_name="Camels", help_text="")
    weed_percent = models.FloatField(null=True, blank=True, default=0,
                                     verbose_name="Veg consisting of Weeds in %", help_text="")
    comments = models.TextField(blank=True,
                                verbose_name="Comments", help_text="")

    class Meta:
        pass


class PlantObservation(AbstractVegetationObservation):
    species = models.ForeignKey(SpeciesObservation, null=True, blank=True,
                                verbose_name="Species", help_text="")
    introduced = models.BooleanField(default=False,
                                     verbose_name="Introduced", help_text="")
    extent = models.CharField(max_length=200, blank=True,
                              verbose_name="Extent of Infestation", help_text="")
    density = models.CharField(max_length=50, blank=True,
                               verbose_name="Density", help_text="")
    invasiveness = models.CharField(max_length=50, blank=True,
                                    verbose_name="Invasiveness", help_text="")

    class Meta:
        pass


class BiodiversityIndicator(AbstractVegetationObservation):
    fauna_habitat = models.ForeignKey('BiodiversityIndicatorLookup', related_name='fauna_habitat_indicator',
                                      on_delete=models.PROTECT,
                                      verbose_name="Fauna Habitat and Shelter", help_text="")
    veg_cover = models.ForeignKey('BiodiversityIndicatorLookup', related_name='veg_cover_indicator',
                                  on_delete=models.PROTECT,
                                  verbose_name="Veg Cover", help_text="")
    crevices = models.ForeignKey('BiodiversityIndicatorLookup', related_name='crevices_indicator',
                                 on_delete=models.PROTECT,
                                 verbose_name="Rock Crevices", help_text="")
    tree_hollows = models.ForeignKey('BiodiversityIndicatorLookup', related_name='tree_hollows_indicator',
                                     on_delete=models.PROTECT,
                                     verbose_name="Tree Hollows", help_text="")
    logs = models.ForeignKey('BiodiversityIndicatorLookup', related_name='logs_indicator',
                             on_delete=models.PROTECT,
                             verbose_name="Logs", help_text="")
    food_avail = models.ForeignKey('BiodiversityIndicatorLookup', related_name='food_avail_indicator',
                                   on_delete=models.PROTECT,
                                   verbose_name="Food Availability", help_text="")
    fruiting = models.ForeignKey('BiodiversityIndicatorLookup', related_name='fruiting_indicator',
                                 on_delete=models.PROTECT,
                                 verbose_name="Fruiting", help_text="")
    flowering = models.ForeignKey('BiodiversityIndicatorLookup', related_name='flowering_indicator',
                                  on_delete=models.PROTECT,
                                  verbose_name="Flowering", help_text="")
    seeding = models.ForeignKey('BiodiversityIndicatorLookup', related_name='seeding_indicator',
                                on_delete=models.PROTECT,
                                verbose_name="Seeding", help_text="")
    termites = models.ForeignKey('BiodiversityIndicatorLookup', related_name='termites_indicator',
                                 on_delete=models.PROTECT,
                                 verbose_name="Termite Mounds", help_text="")
    traces = models.ForeignKey('BiodiversityIndicatorLookup', related_name='traces_indicator',
                               on_delete=models.PROTECT,
                               verbose_name="Tracks and Traces", help_text="")
    sightings = models.ForeignKey('BiodiversityIndicatorLookup', related_name='sightings_indicator',
                                  on_delete=models.PROTECT,
                                  verbose_name="Sightings", help_text="")
    tracks = models.ForeignKey('BiodiversityIndicatorLookup', related_name='tracks_indicator',
                               on_delete=models.PROTECT,
                               verbose_name="Tracks", help_text="")
    scats = models.ForeignKey('BiodiversityIndicatorLookup', related_name='scats_indicator',
                              on_delete=models.PROTECT,
                              verbose_name="Scats", help_text="")
    others = models.ForeignKey('BiodiversityIndicatorLookup', related_name='others_indicator',
                               on_delete=models.PROTECT,
                               verbose_name="Other Signs", help_text="")
    comments = models.TextField(blank=True,
                                verbose_name="Comments", help_text="")

    class Meta:
        pass


#########################
# Lookups
#########################

class ConditionLookup(AbstractLookup):
    strict = False


class StratumLookup(AbstractLookup):
    strict = True


class SignificanceLookup(AbstractLookup):
    pass


class EvidenceRecentFireLookup(AbstractLookup):
    strict = True


class FireIntensityLookup(AbstractLookup):
    strict = True


class CattleSightedLookup(AbstractLookup):
    strict = True


class GrazingLevelLookup(AbstractLookup):
    strict = True


class TracksTramplingLookup(AbstractLookup):
    strict = True


class CattleDungLookup(AbstractLookup):
    strict = True


class FeralEvidenceLookup(AbstractLookup):
    strict = True


class BiodiversityIndicatorLookup(AbstractLookup):
    strict = True
