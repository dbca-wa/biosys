from __future__ import unicode_literals
import datetime
from os import path
from reversion import revisions as reversion
import jsontableschema
import datapackage

from django.db import transaction
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.db.models import Max
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from django.contrib.gis.geos.polygon import Polygon
from django.core.exceptions import ValidationError
from django.conf import settings

from timezone_field import TimeZoneField

from main.constants import DATUM_CHOICES, MODEL_SRID, DEFAULT_SITE_ID
from utils_data_package import GenericSchema, ObservationSchema, SpeciesObservationSchema


@python_2_unicode_compatible
class Dataset(models.Model):
    TYPE_GENERIC = 'generic'
    TYPE_OBSERVATION = 'observation'
    TYPE_SPECIES_OBSERVATION = 'species_observation'
    TYPE_CHOICES = [
        (TYPE_GENERIC, TYPE_GENERIC.capitalize()),
        (TYPE_OBSERVATION, TYPE_OBSERVATION.capitalize()),
        (TYPE_SPECIES_OBSERVATION, 'Species observation')
    ]
    project = models.ForeignKey('Project', null=False, blank=False, related_name='projects',
                                related_query_name='project')
    name = models.CharField(max_length=200, null=False, blank=False)
    type = models.CharField(max_length=100, null=False, blank=False, choices=TYPE_CHOICES, default=TYPE_GENERIC)
    #  data_package should follow the Tabular Data Package format described at:
    #  http://data.okfn.org/doc/tabular-data-package
    #  also in:
    #  http://dataprotocols.org/data-packages/
    #  The schema inside the 'resources' must follow the JSON Table Schema defined at:
    #  http://dataprotocols.org/json-table-schema/
    # IMPORTANT! The data_package should contain only one resources
    data_package = JSONField()

    def __str__(self):
        return '{}'.format(self.name)

    @property
    def record_model(self):
        if self.type == Dataset.TYPE_SPECIES_OBSERVATION:
            return SpeciesObservation
        elif self.type == Dataset.TYPE_OBSERVATION:
            return Observation
        else:
            return GenericRecord

    @property
    def schema_model(self):
        if self.type == Dataset.TYPE_SPECIES_OBSERVATION:
            return SpeciesObservationSchema
        elif self.type == Dataset.TYPE_OBSERVATION:
            return ObservationSchema
        else:
            return GenericSchema

    @property
    def schema(self):
        return self.resource.get('schema', {})

    @property
    def resource(self):
        return self.resources[0]

    @property
    def resources(self):
        return self.data_package.get('resources', [])

    def clean(self):
        """
        Validate the data descriptor
        """
        if self.type == self.TYPE_SPECIES_OBSERVATION:
            raise ValidationError('The support for {} is not yet implemented'.format(self.type))
        #  Validate the data package
        validator = datapackage.DataPackage(self.data_package)
        try:
            validator.validate()
        except Exception as e:
            raise ValidationError('Data package errors: {}'.format([e.message for e in validator.iter_errors()]))
        # Check that there is at least one resources defined (not required by the standard)
        if len(self.resources) == 0:
            raise ValidationError('You must define at least one resource')
        if len(self.resources) > 1:
            raise ValidationError('Only one resource per DataSet')
        # Validate the schema
        if 'schema' not in self.resource:
            raise ValidationError("Resource without a 'schema'.")
        else:
            schema = self.schema
            try:
                # use frictionless validator
                jsontableschema.validate(schema)
            except Exception as e:
                raise ValidationError(
                    'Schema errors for resource "{}": {}'.format(
                        self.resource.get('name'),
                        [e.message for e in jsontableschema.validator.iter_errors(schema)]))
            try:
                # use our own schema class to validate.
                # The constructor should raise an exception if error
                if self.type == self.TYPE_SPECIES_OBSERVATION:
                    SpeciesObservationSchema(schema)
                elif self.type == self.TYPE_OBSERVATION:
                    ObservationSchema(schema)
                else:
                    GenericSchema(schema)
            except Exception as e:
                raise ValidationError(
                    'Schema errors for resource "{}": {}'.format(
                        self.resource.get('name'),
                        e))

    class Meta:
        unique_together = ('project', 'name')


@python_2_unicode_compatible
class DatasetFile(models.Model):
    file = models.FileField(upload_to='%Y/%m/%d')
    uploaded_date = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, null=True, blank=True)
    dataset = models.ForeignKey(Dataset, blank=False, null=True)

    def __str__(self):
        return self.file.name

    @property
    def path(self):
        return self.file.path

    @property
    def filename(self):
        return path.basename(self.path)


@python_2_unicode_compatible
class AbstractRecord(models.Model):
    data = JSONField()
    dataset = models.ForeignKey(Dataset, null=False, blank=False)

    def __str__(self):
        return "{0}: {1}".format(self.dataset.name, Truncator(self.data).chars(100))

    @property
    def data_with_id(self):
        return dict({'id': self.id}, **self.data)

    class Meta:
        abstract = True


class AbstractObservationRecord(AbstractRecord):
    datetime = models.DateTimeField(null=True, blank=True)
    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True)

    class Meta:
        abstract = True


class GenericRecord(AbstractRecord):
    site = models.ForeignKey('Site', null=True, blank=True)


class Observation(AbstractObservationRecord):
    site = models.ForeignKey('Site', null=True, blank=True)


@python_2_unicode_compatible
class SpeciesObservation(AbstractObservationRecord):
    """
    If the input_name has been validated against the species database the name_id is populated with the value from the
    databasedate
    """
    site = models.ForeignKey('Site', null=True, blank=True)
    input_name = models.CharField(max_length=500, null=False, blank=False,
                                  verbose_name="Species", help_text="")
    name_id = models.IntegerField(default=-1,
                                  verbose_name="Name ID", help_text="The unique ID from the herbarium database")
    uncertainty = models.CharField(max_length=50, blank=True,
                                   verbose_name="Species uncertainty", help_text="")

    def __str__(self):
        return self.input_name

    @property
    def valid(self):
        return self.name_id > 0


class Project(models.Model):
    DEFAULT_TIMEZONE = settings.TIME_ZONE

    title = models.CharField(max_length=300, null=False, blank=False, unique=True,
                             verbose_name="Title", help_text="Enter a brief title for the project (required).")
    code = models.CharField(max_length=30, null=True, blank=True,
                            verbose_name="Code",
                            help_text="Provide a brief code or acronym for this project. This code could be used for prefixing site codes.")
    datum = models.IntegerField(null=True, blank=True, choices=DATUM_CHOICES, default=MODEL_SRID,
                                verbose_name="Default Datum",
                                help_text="The datum all locations will be assumed to have unless otherwise specified.")

    timezone = TimeZoneField(default=DEFAULT_TIMEZONE)

    custodian = models.CharField(max_length=100, null=True, blank=True,
                                 verbose_name="Custodian",
                                 help_text="The person responsible for the content of this project.")
    email = models.EmailField(null=True, blank=True,
                              verbose_name="Email", help_text="")
    objectives = models.TextField(null=True, blank=True,
                                  verbose_name="Objectives", help_text="")
    methodology = models.TextField(null=True, blank=True,
                                   verbose_name="Methodology", help_text="")
    funding = models.TextField(null=True, blank=True,
                               verbose_name="Funding", help_text="")
    duration = models.CharField(max_length=100, null=True, blank=True,
                                verbose_name="Duration", help_text="The likely duration of the project.")
    extent_lat_min = models.FloatField(null=True, blank=True,
                                       verbose_name="Extent latitude min",
                                       help_text="The southernmost extent of the project (-90 - 0)")
    extent_lat_max = models.FloatField(null=True, blank=True,
                                       verbose_name="Extent latitude max",
                                       help_text="The northernmost extent of the project (-90 - 0)")
    extent_long_min = models.FloatField(null=True, blank=True,
                                        verbose_name="Extent longitude min",
                                        help_text="The westernmost extent of the project (0 - 180)")
    extent_long_max = models.FloatField(null=True, blank=True,
                                        verbose_name="Extent longitude max",
                                        help_text="The easternmost extent of the project (0 - 180)")
    comments = models.TextField(null=True, blank=True,
                                verbose_name="Comments", help_text="")
    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True, editable=True,
                                    verbose_name="Extent Geometry", help_text="")
    attributes = JSONField(null=True, blank=True)
    attributes_schema = JSONField(null=True, blank=True)

    class Meta:
        pass

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.extent_lat_min is not None and self.extent_long_min is not None and self.extent_lat_max is not None and \
                        self.extent_long_max is not None:
            self.geometry = Polygon.from_bbox((self.extent_long_min, self.extent_lat_min,
                                               self.extent_long_max, self.extent_lat_max))

        super(Project, self).save(*args, **kwargs)


def _calculate_site_ID():  # @NoSelf
    if Site.objects.count() == 0:
        return DEFAULT_SITE_ID
    else:
        return Site.objects.aggregate(Max('site_ID'))['site_ID__max'] + 1


class Site(models.Model):
    project = models.ForeignKey('Project', null=False, blank=False,
                                verbose_name="Project", help_text="Select the project this site is part of (required)")
    site_ID = models.IntegerField(null=False, blank=False, unique=True, default=_calculate_site_ID,
                                  verbose_name="Site ID", help_text="Site ID from Scientific Site Register.")
    parent_site = models.ForeignKey('self', null=True, blank=True,
                                    verbose_name="Parent Site",
                                    help_text="Sites can be grouped together. If you have a subregion within the project that contains a number of sites, create that region as a parent site first, then select that parent when you're creating this site.")
    site_code = models.CharField(max_length=100, null=False, blank=False,
                                 verbose_name="Site Code",
                                 help_text="Local site code must be unique to this project. e.g. LCI123 (required)")
    site_name = models.CharField(max_length=150, blank=True,
                                 verbose_name="Site Name",
                                 help_text="Enter a more descriptive name for this site, if one exists.")
    date_established = models.DateField(default=datetime.date.today, null=False, blank=False,
                                        verbose_name="Date established",
                                        help_text="The date this site was first established (required)")
    latitude = models.FloatField(null=True, blank=True,
                                 help_text="Latitude of site origin (e.g. corner, centroid, etc., required)")
    longitude = models.FloatField(null=True, blank=True,
                                  help_text="Longitude of site origin (e.g. corner, centroid, etc., required)")
    accuracy = models.FloatField(default=30.0, null=False, blank=False,
                                 verbose_name="Accuracy (m)", help_text="")
    datum = models.IntegerField(null=False, blank=False, choices=DATUM_CHOICES, default=MODEL_SRID,
                                verbose_name="Datum", help_text="")
    established_by = models.CharField(max_length=200, null=True, blank=True,
                                      verbose_name="Established by", help_text="")
    bearing = models.FloatField(null=True, blank=True,
                                verbose_name="Bearing",
                                help_text="Degrees (0 - 360)")
    width = models.IntegerField(null=True, blank=True,
                                verbose_name="Width (m)", help_text="")
    height = models.IntegerField(null=True, blank=True,
                                 verbose_name="Height (m)", help_text="")
    ASPECT_CHOICES = [
        ('N', 'N'), ('NNE', 'NNE'), ('NE', 'NE'), ('ENE', 'ENE'), ('E', 'E'), ('ESE', 'ESE'), ('SE', 'SE'),
        ('SSE', 'SSE'),
        ('S', 'S'), ('SSW', 'SSW'), ('SW', 'SW'), ('WSW', 'WSW'), ('W', 'W'), ('WNW', 'WNW'), ('NW', 'NW'),
        ('NNW', 'NNW')
    ]
    aspect = models.CharField(max_length=10, null=True, blank=True, choices=ASPECT_CHOICES,
                              verbose_name="Aspect", help_text="Compass bearing (e.g. N, SSE)")
    slope = models.FloatField(null=True, blank=True,
                              verbose_name="Slope", help_text="Degrees (0 - 90)")
    altitude = models.FloatField(null=True, blank=True,
                                 verbose_name="Altitude", help_text="Altitude, in metres")
    radius = models.FloatField(null=True, blank=True,
                               verbose_name="Radius", help_text="Radius, in metres")
    location = models.ForeignKey('LocationLookup', null=True, blank=True, on_delete=models.PROTECT,
                                 verbose_name="Location", help_text="")
    geology_group = models.ForeignKey('GeologyGroupLookup', null=True, blank=True, on_delete=models.PROTECT,
                                      verbose_name="Geology group", help_text="")
    vegetation_group = models.ForeignKey('VegetationGroupLookup', null=True, blank=True, on_delete=models.PROTECT,
                                         verbose_name="Vegetation group", help_text="")
    tenure = models.CharField(max_length=50, null=True, blank=True, verbose_name="Tenure", help_text="")
    underlaying_geology = models.ForeignKey('GeologyLookup', null=True, blank=True, on_delete=models.PROTECT,
                                            verbose_name="Underlaying geology")
    closest_water_distance = models.IntegerField(null=True, blank=True,
                                                 verbose_name="Distance to closest water (m)", help_text="")
    closest_water_type = models.ForeignKey('WaterTypeLookup', null=True, blank=True, on_delete=models.PROTECT,
                                           verbose_name="Type of closest water", help_text="")
    landform_pattern = models.ForeignKey('LandformPatternLookup', null=True, blank=True, on_delete=models.PROTECT,
                                         verbose_name="Landform pattern (300m radius)", help_text="")
    landform_element = models.ForeignKey('LandformElementLookup', null=True, blank=True, on_delete=models.PROTECT,
                                         verbose_name="Landform element (20m radius)", help_text="")
    soil_surface_texture = models.ForeignKey('SoilSurfaceTextureLookup', null=True, blank=True,
                                             on_delete=models.PROTECT,
                                             verbose_name="Soil surface texture", help_text="")
    soil_colour = models.CharField(max_length=150, blank=True,
                                   verbose_name="Soil colour", help_text="")
    photos_taken = models.TextField(blank=True,
                                    verbose_name="Photos Taken", help_text="")
    historical_info = models.TextField(null=True, blank=True,
                                       verbose_name="Historical information")
    comments = models.TextField(null=True, blank=True,
                                verbose_name="Comments", help_text="")
    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True, editable=True,
                                    verbose_name="Geometry", help_text="")
    attributes = JSONField(null=True, blank=True)
    attributes_schema = JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('project', 'site_code')

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.site_code

    def save(self, *args, **kwargs):
        """
        Calculate and save the geometry from the quadrant attributes
        """
        if self.latitude and self.longitude:
            point = Point(self.longitude, self.latitude, srid=self.datum)
            self.geometry = point
        super(Site, self).save(*args, **kwargs)


class Visit(models.Model):
    project = models.ForeignKey('Project', null=False, blank=False,
                                verbose_name="Project", help_text="")
    sites = models.ManyToManyField('Site', blank=False,
                                   verbose_name="Sites", help_text="")
    name = models.CharField(max_length=150, blank=False,
                            verbose_name="Visit Name",
                            help_text="Enter a unique name for this visit to the sites listed above (required)")
    start_date = models.DateField(default=datetime.date.today, null=False, blank=False,
                                  verbose_name="Start Date",
                                  help_text="Enter the start date of the visit (required)")
    end_date = models.DateField(null=True, blank=True,
                                verbose_name="End Date",
                                help_text="Enter the actual end date of the visit")
    trap_nights = models.IntegerField(null=True, blank=True,
                                      verbose_name="Trap Nights",
                                      help_text="Enter the number of actual trapping nights that occurred.")
    comments = models.TextField(null=True, blank=True,
                                verbose_name="Comments",
                                help_text="")

    class Meta:
        pass

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.name

    def get_errors(self):
        """Returns the queryset of validation errors for SiteVisitDataFile
        objects related to this visit.
        """
        from upload.models import SiteVisitDataFileError

        return SiteVisitDataFileError.objects.filter(file__visit=self)


class SiteVisit(models.Model):
    visit = models.ForeignKey('Visit', null=False, blank=False,
                              verbose_name="Visit", help_text="")
    site = models.ForeignKey('Site', null=False, blank=False,
                             verbose_name="Site", help_text="")
    data_file = models.ForeignKey('SiteVisitDataFile', null=True, blank=False,
                                  verbose_name="Data File", help_text="")
    DATA_STATUS_CHOICES = [
        ('quarantined', 'Quarantined'),  # Uploader has imported data, work in progress.
        ('approved', 'Approved'),  # Data custodian checked off, but not published.
        ('invalid', 'Invalid'),
        # ('partial', 'Partial'),
        # ('published', 'Published'),  # Cannot be updated further
    ]
    # Assume that the choice values above might change, but that the label
    # for 'Approved' will remain as 'Approved'.
    DATA_STATUS_APPROVED = next(i for i in DATA_STATUS_CHOICES if i[1] == 'Approved')[0]
    DATA_STATUS_QUAR = next(i for i in DATA_STATUS_CHOICES if i[1] == 'Quarantined')[0]
    data_status = models.CharField(max_length=30, null=False, blank=False,
                                   choices=DATA_STATUS_CHOICES, default=DATA_STATUS_CHOICES[0][0],
                                   verbose_name="Data Status", help_text="")

    def __unicode__(self):
        return '{}, {}'.format(self.site, self.visit)

    @property
    def is_approved(self):
        return self.data_status == self.DATA_STATUS_APPROVED

    @property
    def is_quarantined(self):
        return self.data_status == self.DATA_STATUS_QUAR

    def approve(self):
        """Method to set the data_status field to the value for 'approved'.
        Attach a custom comment to the object Version.
        """
        if self.is_approved:
            return

        with transaction.atomic(), reversion.create_revision():
            self.data_status = self.DATA_STATUS_APPROVED
            self.save()
            reversion.set_comment('Status set to approved.')

    def quarantine(self):
        """Method to set the data_status field to the value for 'approved'.
        Attach a custom comment to the object Version.
        """
        if self.is_quarantined:
            return

        with transaction.atomic(), reversion.create_revision():
            self.data_status = self.DATA_STATUS_QUAR
            self.save()
            reversion.set_comment('Status set to quarantined.')


class AbstractSiteVisitObservation(models.Model):
    """
    This should be the base class of every model in the datasheet
    """
    site_visit = models.ForeignKey(SiteVisit, null=True, blank=True,
                                   verbose_name="Site Visit", help_text="")

    class Meta:
        abstract = True


class AbstractDataFile(models.Model):
    file = models.FileField(upload_to='%Y/%m/%d')
    uploaded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.file.name

    @property
    def path(self):
        return self.file.path

    @property
    def filename(self):
        return path.basename(self.path)

    class Meta:
        abstract = True


class SiteVisitDataFile(AbstractDataFile):
    visit = models.ForeignKey('Visit', null=False, blank=False,
                              verbose_name="Visit", help_text="")
    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.PROTECT,
                             verbose_name="User", help_text='User that uploaded the file')
    site = models.ForeignKey('Site', null=True, blank=True,
                             verbose_name="Site", help_text="")

    def errors(self):
        from upload.models import SiteVisitDataFileError

        return SiteVisitDataFileError.objects.filter(file=self)


class SiteVisitDataSheetTemplate(AbstractDataFile):
    version = models.CharField(max_length=50, verbose_name="Template Version", default="1.0")


class OldSpeciesObservation(AbstractSiteVisitObservation):
    """
    Species name as entered in the datasheet (input_name)
    If the input_name has been validated against the species database the name_id is populated with the value from the
    database
    """
    input_name = models.CharField(max_length=500, null=False, blank=False,
                                  verbose_name="Species", help_text="")
    name_id = models.IntegerField(default=-1,
                                  verbose_name="Name ID", help_text="The unique ID from the herbarium database")
    VALIDATION_STATUS_CHOICES = [
        ('', ''),
        ('do not validate', 'do not validate')
    ]
    validation_status = models.CharField(max_length=50, null=True, blank=True,
                                         choices=VALIDATION_STATUS_CHOICES, default=VALIDATION_STATUS_CHOICES[0][0],
                                         verbose_name="Species validation status")
    uncertainty = models.CharField(max_length=50, blank=True,
                                   verbose_name="Species uncertainty", help_text="")

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.input_name

    @property
    def valid(self):
        return self.name_id > 0


class SiteCharacteristic(models.Model):
    site_visit = models.ForeignKey('SiteVisit', null=True, blank=True,
                                   verbose_name="Site Visit", help_text="")
    underlaying_geology = models.ForeignKey('GeologyLookup', null=True, blank=True, on_delete=models.PROTECT,
                                            verbose_name="Underlaying geology")
    closest_water_distance = models.IntegerField(null=True, blank=True,
                                                 verbose_name="Distance to closest water (m)", help_text="")
    closest_water_type = models.ForeignKey('WaterTypeLookup', null=True, blank=True, on_delete=models.PROTECT,
                                           verbose_name="Type of closest water", help_text="")
    landform_pattern = models.ForeignKey('LandformPatternLookup', null=True, blank=True, on_delete=models.PROTECT,
                                         verbose_name="Landform pattern (300m radius)", help_text="")
    landform_element = models.ForeignKey('LandformElementLookup', null=True, blank=True, on_delete=models.PROTECT,
                                         verbose_name="Landform element (20m radius)", help_text="")
    soil_surface_texture = models.ForeignKey('SoilSurfaceTextureLookup', null=True, blank=True,
                                             on_delete=models.PROTECT,
                                             verbose_name="Soil surface texture", help_text="")
    soil_colour = models.CharField(max_length=150, blank=True,
                                   verbose_name="Soil colour", help_text="")
    comments = models.TextField(null=True, blank=True,
                                verbose_name="Comments", help_text="")

    def __unicode__(self):
        return 'Site characteristic for {}'.format(self.site_visit)


#########################
# Lookups
#########################


class AbstractLookup(models.Model):
    value = models.CharField(max_length=500, blank=False,
                             verbose_name="Value", help_text="")
    code = models.CharField(max_length=10, blank=True,
                            verbose_name="Code", help_text="")
    deprecated = models.BooleanField(default=False,
                                     verbose_name="Deprecated", help_text="")
    strict = False

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.value

    class Meta:
        abstract = True
        ordering = ['value']


class GeologyGroupLookup(AbstractLookup):
    pass


class LocationLookup(AbstractLookup):
    pass


class VegetationGroupLookup(AbstractLookup):
    pass


class TenureLookup(AbstractLookup):
    pass


class SoilColourLookup(AbstractLookup):
    pass


class SoilSurfaceTextureLookup(AbstractLookup):
    strict = False


class LandformElementLookup(AbstractLookup):
    pass


class LandformPatternLookup(AbstractLookup):
    pass


class WaterTypeLookup(AbstractLookup):
    strict = False


class GeologyLookup(AbstractLookup):
    pass
