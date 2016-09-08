from __future__ import absolute_import, unicode_literals, print_function, division

from os import path

import datapackage
import jsontableschema
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from timezone_field import TimeZoneField

from main.constants import DATUM_CHOICES, MODEL_SRID, DEFAULT_SITE_ID
from main.utils_data_package import GenericSchema, ObservationSchema, SpeciesObservationSchema


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
        # Validate the data package
        validator = datapackage.DataPackage(self.data_package)
        try:
            validator.validate()
        except Exception:
            raise ValidationError('Data package errors:<br>{}'.format(
                "<br>".join([e.message for e in validator.iter_errors()])
            ))
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
            except Exception:
                raise ValidationError(
                    'Schema errors for resource "{}":<br>{}'.format(
                        self.resource.get('name'),
                        "<br>".join([e.message for e in jsontableschema.validator.iter_errors(schema)])
                    ))
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
    datetime = models.DateTimeField(null=False, blank=False)
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
                                  verbose_name="Species Name", help_text="Species Name (as imported)")
    name_id = models.IntegerField(default=-1,
                                  verbose_name="Name ID", help_text="The unique ID from the species database")

    def __str__(self):
        return self.input_name

    @property
    def valid(self):
        return self.name_id > 0


@python_2_unicode_compatible
class Project(models.Model):
    DEFAULT_TIMEZONE = settings.TIME_ZONE

    title = models.CharField(max_length=300, null=False, blank=False, unique=True,
                             verbose_name="Title", help_text="Enter a name for the project (required).")
    code = models.CharField(max_length=30, null=True, blank=True,
                            verbose_name="Code",
                            help_text="Provide a brief code or acronym for this project. This code could be used for prefixing site codes.")
    datum = models.IntegerField(null=True, blank=True, choices=DATUM_CHOICES, default=MODEL_SRID,
                                verbose_name="Default Datum",
                                help_text="The datum all locations will be assumed to have unless otherwise specified.")

    timezone = TimeZoneField(default=DEFAULT_TIMEZONE)

    attributes = JSONField(null=True, blank=True,
                           help_text="Define here all specific attributes of your project in the form of json "
                                     "'attribute name': 'attribute value")
    comments = models.TextField(null=True, blank=True,
                                verbose_name="Comments", help_text="")

    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True, editable=True,
                                    verbose_name="Extent",
                                    help_text="The boundary of your project (not required). "
                                              "Can also be calculated from the extents of the project sites")
    site_data_package = JSONField(null=True, blank=True,
                                  verbose_name='Site attributes schema',
                                  help_text='Define here the attributes that all your sites will share.')

    class Meta:
        pass

    def __str__(self):
        return self.title


def _calculate_site_ID():  # @NoSelf
    if Site.objects.count() == 0:
        return DEFAULT_SITE_ID
    else:
        return Site.objects.aggregate(Max('site_ID'))['site_ID__max'] + 1


@python_2_unicode_compatible
class Site(models.Model):
    project = models.ForeignKey('Project', null=False, blank=False,
                                verbose_name="Project", help_text="Select the project this site is part of (required)")
    parent_site = models.ForeignKey('self', null=True, blank=True,
                                    verbose_name="Parent Site",
                                    help_text="Sites can be grouped together. "
                                              "If you have a subregion within the project that contains a number "
                                              "of sites, create that region as a parent site first, "
                                              "then select that parent when you're creating this site.")
    name = models.CharField(max_length=150, blank=True,
                            verbose_name="Name",
                            help_text="Enter a more descriptive name for this site, if one exists.")
    code = models.CharField(max_length=100, null=False, blank=False,
                            verbose_name="Code",
                            help_text="Local site code must be unique to this project. e.g. LCI123 (required)")
    site_ID = models.IntegerField(null=False, blank=False, unique=True, default=_calculate_site_ID,
                                  verbose_name="Site ID", help_text="Site ID from Scientific Site Register.")
    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True, editable=True,
                                    verbose_name="Location", help_text="")
    comments = models.TextField(null=True, blank=True,
                                verbose_name="Comments", help_text="")
    attributes = JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('project', 'code')

    def __str__(self):
        return self.code
