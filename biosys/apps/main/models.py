from __future__ import absolute_import, unicode_literals, print_function, division

import logging
from os import path

import datapackage
import jsontableschema
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from timezone_field import TimeZoneField

from main.constants import DATUM_CHOICES, MODEL_SRID
from main.utils_auth import is_admin
from main.utils_data_package import GenericSchema, ObservationSchema, SpeciesObservationSchema

logger = logging.getLogger(__name__)


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
    def record_queryset(self):
        return self.record_model.objects.filter(dataset=self)

    @property
    def schema_class(self):
        if self.type == Dataset.TYPE_SPECIES_OBSERVATION:
            return SpeciesObservationSchema
        elif self.type == Dataset.TYPE_OBSERVATION:
            return ObservationSchema
        else:
            return GenericSchema

    @property
    def schema_data(self):
        return self.resource.get('schema', {})

    @property
    def schema(self):
        return self.schema_class(self.schema_data)

    @property
    def resource(self):
        return self.resources[0]

    @property
    def resources(self):
        return self.data_package.get('resources', [])

    @staticmethod
    def validate_data_package(data_package, dataset_type):
        """
        Will throw a validation error if any problem
        :param data_package:
        :param dataset_type:
        :return:
        """
        validator = datapackage.DataPackage(data_package)
        try:
            validator.validate()
        except Exception:
            raise ValidationError('Data package errors:<br>{}'.format(
                "<br>".join([e.message for e in validator.iter_errors()])
            ))
        # Check that there is at least one resources defined (not required by the standard)
        resources = data_package.get('resources', [])
        if len(resources) == 0:
            raise ValidationError('You must define at least one resource')
        if len(resources) > 1:
            raise ValidationError('Only one resource per DataSet')
        # Validate the schema
        resource = resources[0]
        if 'schema' not in resource:
            raise ValidationError("Resource without a 'schema'.")
        else:
            schema = resource.get('schema', {})
            try:
                # use frictionless validator
                jsontableschema.validate(schema)
            except Exception:
                raise ValidationError(
                    'Schema errors for resource "{}":<br>{}'.format(
                        resource.get('name'),
                        "<br>".join([e.message for e in jsontableschema.validator.iter_errors(schema)])
                    ))
            try:
                # use our own schema class to validate.
                # The constructor should raise an exception if error
                if dataset_type == Dataset.TYPE_SPECIES_OBSERVATION:
                    SpeciesObservationSchema(schema)
                elif dataset_type == Dataset.TYPE_OBSERVATION:
                    ObservationSchema(schema)
                else:
                    GenericSchema(schema)
            except Exception as e:
                raise ValidationError(
                    'Schema errors for resource "{}": {}'.format(
                        resource.get('name'),
                        e))

    def validate_data(self, data):
        if not data:
            msg = "field 'data' cannot be null or empty"
            raise ValidationError(msg)
        try:
            field_errors = self.schema.get_error_fields(data)
            if len(field_errors) > 0:
                for field_name, data in field_errors:
                    msg = "'{}': {}".format(field_name, data.get('error'))
                    raise ValidationError(msg)
        except Exception as e:
            raise ValidationError(e)

    def clean(self):
        """
        Validate the data descriptor
        """
        # Validate the data package
        self.validate_data_package(self.data_package, self.type)

    def is_custodian(self, user):
        return self.project.is_custodian(user)

    # API permissions
    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_metadata_permission(request):
        return True

    def has_object_metadata_permission(self, request):
        return True

    @staticmethod
    def has_create_permission(request):
        """
        Custodian and admin only
        Check that the user is a custodian of the project pk passed in the POST data
        :param request:
        :return:
        """
        result = False
        if is_admin(request.user):
            result = True
        elif 'project' in request.data:
            project = Project.objects.filter(pk=request.data['project']).first()
            result = project is not None and project.is_custodian(request.user)
        return result

    @staticmethod
    def has_update_permission(request):
        """
        The update is managed at the object level (see below)
        :param request:
        :return:
        """
        return True

    def has_object_update_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    class Meta:
        unique_together = ('project', 'name')


@python_2_unicode_compatible
class DatasetFile(models.Model):
    file = models.FileField(upload_to='%Y/%m/%d')
    uploaded_date = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
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

    def is_custodian(self, user):
        return self.dataset.is_custodian(user)

    # API permissions
    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_metadata_permission(request):
        return True

    def has_object_metadata_permission(self, request):
        return True

    @staticmethod
    def has_create_permission(request):
        """
        Custodian and admin only
        Check that the user is a custodian of the dataset pk passed in the POST data.
        :param request:
        :return:
        """
        result = False
        if is_admin(request.user):
            result = True
        elif 'dataset' in request.data:
            ds = Dataset.objects.filter(pk=request.data['dataset']).first()
            result = ds is not None and ds.is_custodian(request.user)
        return result

    @staticmethod
    def has_update_permission(request):
        """
        The update is managed at the object level (see below)
        :param request:
        :return:
        """
        return True

    def has_object_update_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    def clean(self):
        self.dataset.validate_data(self.data)

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
    If the species_name has been validated against the species database the name_id is populated with the value from the
    databasedate
    """
    site = models.ForeignKey('Site', null=True, blank=True)
    species_name = models.CharField(max_length=500, null=True, blank=True,
                                    verbose_name="Species Name", help_text="Species Name (as imported)")
    name_id = models.IntegerField(default=-1,
                                  verbose_name="Name ID", help_text="The unique ID from the species database")

    def __str__(self):
        return self.species_name

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
                            help_text="Provide a brief code or acronym for this project. "
                                      "This code could be used for prefixing site codes.")

    datum = models.IntegerField(null=True, blank=True, choices=DATUM_CHOICES, default=MODEL_SRID,
                                verbose_name="Default Datum",
                                help_text="The datum all locations will be assumed to have unless otherwise specified.")

    timezone = TimeZoneField(blank=True, default=DEFAULT_TIMEZONE,
                             help_text="The Timezone of your project e.g 'Australia/Perth.")

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
                                  help_text='Define here the attributes that all your sites will share. '
                                            'This allows validation when importing sites.')

    custodians = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                        help_text="Users that have write/upload access to the data of this project.")

    def is_custodian(self, user):
        return user in self.custodians.all()

    # API permissions
    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_metadata_permission(request):
        return True

    def has_object_metadata_permission(self, request):
        return True

    @staticmethod
    def has_create_permission(request):
        return is_admin(request.user)

    @staticmethod
    def has_update_permission(request):
        """
        The update is managed at the object level (see below)
        :param request:
        :return:
        """
        return True

    def has_object_update_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    class Meta:
        pass

    def __str__(self):
        return self.title


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
    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True, editable=True,
                                    verbose_name="Location", help_text="")
    comments = models.TextField(null=True, blank=True,
                                verbose_name="Comments", help_text="")
    attributes = JSONField(null=True, blank=True)

    def is_custodian(self, user):
        return self.project.is_custodian(user)

    # API permissions
    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True

    @staticmethod
    def has_metadata_permission(request):
        return True

    def has_object_metadata_permission(self, request):
        return True

    @staticmethod
    def has_create_permission(request):
        """
        Custodian and admin only
        Check that the user is a custodian of the project pk passed in the POST data.
        :param request:
        :return:
        """
        result = False
        if is_admin(request.user):
            result = True
        elif 'project' in request.data:
            project = Project.objects.filter(pk=request.data['project']).first()
            result = project is not None and project.is_custodian(request.user)
        return result

    @staticmethod
    def has_update_permission(request):
        """
        The update is managed at the object level (see below)
        :param request:
        :return:
        """
        return True

    def has_object_update_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user)

    class Meta:
        unique_together = ('project', 'code')

    def __str__(self):
        return self.code
