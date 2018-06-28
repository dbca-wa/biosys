from __future__ import absolute_import, unicode_literals, print_function, division

import logging
from os import path

from datapackage import validate as datapackage_validate
from datapackage import exceptions as datapackage_exceptions
from tableschema import validate as tableschema_validate
from tableschema import exceptions as tableschema_exceptions
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import Truncator
from django.db.models.query_utils import Q
from timezone_field import TimeZoneField

from main.constants import DATUM_CHOICES, MODEL_SRID
from main.utils_auth import is_admin
from main.utils_data_package import GenericSchema, ObservationSchema, SpeciesObservationSchema

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class Program(models.Model):
    name = models.CharField(max_length=300, null=False, blank=False, unique=True,
                            verbose_name="Name", help_text="Enter a name for the program (required).")
    code = models.CharField(max_length=30, null=True, blank=True,
                            verbose_name="Code",
                            help_text="Provide a brief code or acronym for this program.")

    description = models.TextField(null=True, blank=True,
                                   verbose_name="Description", help_text="")

    data_engineers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        help_text="Users that can create/update projects and dataset schema within this program."
    )

    def is_data_engineer(self, user):
        return user in self.data_engineers.all()

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
        return is_admin(request.user)

    @staticmethod
    def has_destroy_permission(request):
        return is_admin(request.user)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Project(models.Model):
    DEFAULT_TIMEZONE = settings.TIME_ZONE

    program = models.ForeignKey(Program, blank=False, null=False, on_delete=models.CASCADE,
                                help_text="The program this project belongs to.")

    name = models.CharField(max_length=300, null=False, blank=False, unique=True,
                            verbose_name="Name", help_text="Enter a name for the project (required).")
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
    description = models.TextField(null=True, blank=True,
                                   verbose_name="Description", help_text="")

    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True, editable=True,
                                    verbose_name="Extent",
                                    help_text="The boundary of your project (not required). "
                                              "Can also be calculated from the extents of the project sites")
    site_data_package = JSONField(null=True, blank=True,
                                  verbose_name='Site attributes schema',
                                  help_text='Define here the attributes that all your sites will share. '
                                            'This allows validation when importing sites.')

    custodians = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=False,
                                        help_text="Users that have write/upload access to the data of this project.")

    def is_custodian(self, user):
        return user in self.custodians.all()

    def is_data_engineer(self, user):
        return self.program.is_data_engineer(user)

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
        Admin or data_engineer of the program the project would belong to.
        Check that the user is a data_engineer of the program pk passed in the POST data.
        :param request:
        :return:
        """
        result = False
        if is_admin(request.user):
            result = True
        elif 'program' in request.data:
            program = Program.objects.filter(pk=request.data['program']).first()
            result = program is not None and program.is_data_engineer(request.user)
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
        """
        Admin or program data_engineer or project custodian
        :param request:
        :return:
        """
        user = request.user
        return is_admin(user) or self.program.is_data_engineer(user) or self.is_custodian(user)

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        """
        Admin or program data_engineer or project custodian
        :param request:
        :return:
        """
        user = request.user
        return is_admin(user) or self.program.is_data_engineer(user) or self.is_custodian(user)

    @property
    def centroid(self):
        return self.geometry.centroid if self.geometry else None

    @property
    def dataset_count(self):
        return self.projects.count()

    @property
    def site_count(self):
        return self.site_set.count()

    @property
    def record_count(self):
        return Record.objects.filter(dataset__project=self).count()

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Site(models.Model):
    project = models.ForeignKey('Project', null=False, blank=False,
                                verbose_name="Project", help_text="Select the project this site is part of (required)",
                                on_delete=models.CASCADE)
    name = models.CharField(max_length=150, blank=True,
                            verbose_name="Name",
                            help_text="Enter a more descriptive name for this site, if one exists.")
    code = models.CharField(max_length=100, null=False, blank=False,
                            verbose_name="Code",
                            help_text="Local site code must be unique to this project. e.g. LCI123 (required)")
    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True, editable=True,
                                    verbose_name="Location", help_text="")
    description = models.TextField(null=True, blank=True,
                                   verbose_name="Description", help_text="")
    attributes = JSONField(null=True, blank=True)

    def is_custodian(self, user):
        return self.project.is_custodian(user)

    def is_data_engineer(self, user):
        return self.project.is_data_engineer(user)

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
        Custodian and admin and data engineer
        Check that the user is a custodian of the project pk passed in the POST data.
        :param request:
        :return:
        """
        result = False
        user = request.user
        if is_admin(user):
            result = True
        elif 'project' in request.data:
            project = Project.objects.filter(pk=request.data['project']).first()
            result = project is not None and project.is_custodian(user) or project.is_data_engineer(user)
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
        user = request.user
        return is_admin(user) or self.is_custodian(user) or self.project.is_data_engineer(user)

    @property
    def centroid(self):
        return self.geometry.centroid if self.geometry else None

    class Meta:
        unique_together = ('project', 'code')
        ordering = ['code']

    def __str__(self):
        return self.code


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
                                related_query_name='project', on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=False, blank=False)
    code = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=100, null=False, blank=False, choices=TYPE_CHOICES, default=TYPE_GENERIC)
    #  data_package should follow the Tabular Data Package format described at:
    #  https://frictionlessdata.io/specs/data-package/
    #  The schema inside the 'resources' must follow the JSON Table Schema defined at:
    #  https://frictionlessdata.io/specs/table-schema/
    # IMPORTANT! The data_package should contain only one resources
    data_package = JSONField()
    description = models.TextField(null=True, blank=True,
                                   verbose_name="Description", help_text="")

    def __str__(self):
        return '{}'.format(self.name)

    @property
    def record_model(self):
        """
        This is a legacy method from the time where there were 3 different models
        (generic, observation, species_observation)
        :return:
        """
        return Record

    @property
    def record_queryset(self):
        return self.record_model.objects.filter(dataset=self)

    @property
    def record_count(self):
        return self.record_model.objects.filter(dataset=self).count()

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
    def resource_name(self):
        return self.resource['name']

    @property
    def resources(self):
        return self.data_package.get('resources', [])

    @property
    def foreign_keys(self):
        # note: don't use the self.schema (schema object) it is too slow.
        return self.schema_data.get('foreignKeys', [])

    @property
    def has_foreign_keys(self):
        return bool(self.foreign_keys)

    @property
    def foreign_keys_resource_names(self):
        """
        Return a list of all the resource names referenced as foreign key in the schema
        :return:
        """
        # note: don't use the self.schema (schema object) it is too slow.
        result = []
        for fk in (self.foreign_keys or []):
            resource_name = fk.get('reference', {}).get('resource')
            if resource_name:
                result.append(resource_name)
        return result

    @property
    def get_parent_dataset(self):
        """
        If the schema declared some foreign keys, lookup for the first dataset that matches a foreign key.
        Rules:
        - it must belong to the same project
        - the resource name referenced in the foreign key must match a dataset name, code or datapackage
        first resource name.
        :return: a matching dataset or None
        """
        fk_resource_names = self.foreign_keys_resource_names
        if fk_resource_names:
            initial_queryset = Dataset.objects.filter(project=self.project)
            resource_name_query = Q(name__in=fk_resource_names) | \
                                  Q(code__in=fk_resource_names) | \
                                  Q(data_package__resources__0__name__in=fk_resource_names)
            # TODO: we support only one FK
            return initial_queryset.filter(resource_name_query).first()
        else:
            return None

    @property
    def has_primary_key(self):
        """
        Check uf this dataset has a declared primaryKey in its schema
        :return:
        """
        return bool(self.schema_data.get('primaryKey'))

    @staticmethod
    def validate_data_package(data_package, dataset_type, project=None):
        """
        Will throw a validation error if any problem
        :param data_package:
        :param dataset_type:
        :param project:
        :return:
        """
        try:
            datapackage_validate(data_package)
        except datapackage_exceptions.ValidationError as exception:
            raise ValidationError('Data package errors:<br>{}'.format(
                "<br>".join([str(e) for e in exception.errors])
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
                tableschema_validate(schema)
            except tableschema_exceptions.ValidationError as exception:
                raise ValidationError(
                    'Schema errors for resource "{}":<br>{}'.format(
                        resource.get('name'),
                        "<br>".join([str(e) for e in exception.errors])
                    ))
            try:
                # use our own schema class to validate.
                # The constructor should raise an exception if error
                if dataset_type == Dataset.TYPE_SPECIES_OBSERVATION:
                    SpeciesObservationSchema(schema, project)
                elif dataset_type == Dataset.TYPE_OBSERVATION:
                    ObservationSchema(schema, project)
                else:
                    GenericSchema(schema, project)
            except Exception as e:
                raise ValidationError(
                    'Schema errors for resource "{}": {}'.format(
                        resource.get('name'),
                        e))

    def clean(self):
        """
        Validate the data descriptor
        """
        # Validate the data package
        self.validate_data_package(self.data_package, self.type)

    def is_custodian(self, user):
        return self.project.is_custodian(user)

    def is_data_engineer(self, user):
        return self.project.is_data_engineer(user)

    def has_foreign_key_to(self, dataset):
        """
        Check if this dataset has declared a foreign key to the given dataset
        We check the resources name against the dataset name, code and resource name
        :return: True if FK found.
        """
        for resource_name in self.foreign_keys_resource_names:
            if resource_name in [dataset.name, dataset.code, dataset.resource_name]:
                return True
        return False

    def get_children_datasets(self):
        """
        Return all the datasets within the project that have declared a foreign key to this dataset.
        :return: a list (NOT a QuerySet) of dataset
        """
        # TODO: use a proper json field lookup for foreign key to return a queryset
        return [ds for ds in Dataset.objects.filter(project=self.project) if ds.has_foreign_key_to(self)]

    def get_fk_lookup_fields_for_dataset(self, dataset):
        """
        Traverse this dataset declared foreign keys and find the first one that matches the given dataset.
        If found it will return a tuple (parent_field, child_field) for a mapping between the child_field (our field)
        and it's parent (from the given dataset)
        :return: a tuple (parent_field, child_field) if a fk to the given dataset is found or (None, None)
        """
        for fk in self.schema.foreign_keys:
            if fk.reference_resource in [dataset.name, dataset.code, dataset.resource_name]:
                parent_field = fk.parent_data_field_name
                child_field = fk.data_field
                return parent_field, child_field
        return None, None

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
        user = request.user
        if is_admin(user):
            result = True
        elif 'project' in request.data:
            project = Project.objects.filter(pk=request.data['project']).first()
            result = project is not None and project.is_custodian(user) or project.is_data_engineer(user)
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
        user = request.user
        return is_admin(user) or self.is_custodian(user) or self.is_data_engineer(user)

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        user = request.user
        return is_admin(user) or self.is_custodian(user) or self.project.is_data_engineer(user)

    class Meta:
        unique_together = ('project', 'name')
        ordering = ['name']


@python_2_unicode_compatible
class Record(models.Model):
    dataset = models.ForeignKey(Dataset, null=False, blank=False, on_delete=models.CASCADE)
    data = JSONField()
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.SET_NULL)
    # Fields for Observation and Species Observation
    datetime = models.DateTimeField(null=True, blank=True)
    geometry = models.GeometryField(srid=MODEL_SRID, spatial_index=True, null=True, blank=True)
    # Fields specific for Species Observation
    species_name = models.CharField(max_length=500, null=True, blank=True,
                                    verbose_name="Species Name", help_text="Species Name (as imported)")
    name_id = models.IntegerField(default=-1,
                                  verbose_name="Name ID", help_text="The unique ID from the species database")
    # to store information about the source of the record, like excel filename, row number in file etc...
    source_info = JSONField(null=True, blank=True)

    # flags about publishing status
    published = models.BooleanField(default=False)
    consumed = models.BooleanField(default=False)

    # client id
    client_id = models.CharField(max_length=1024, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{0}: {1}".format(self.dataset.name, Truncator(self.data).chars(100))

    @property
    def data_with_id(self):
        return dict({'id': self.id}, **self.data)

    @property
    def parents(self):
        """
        If the record dataset schema has a declared foreign key, look for the parents of this record.
        :return: a Record queryset or Record.objects.none()
        """
        if self.dataset.has_foreign_keys:
            parent_dataset = self.dataset.get_parent_dataset
            if parent_dataset:
                parent_field, child_field = self.dataset.get_fk_lookup_fields_for_dataset(parent_dataset)
                if parent_field and child_field:
                    child_value = self.data[child_field]
                    if child_value:
                        query = Q(dataset=parent_dataset) & Q(data__contains={parent_field: child_value})
                        return Record.objects.filter(query)
            return Record.objects.none()
        else:
            return None

    @property
    def children(self):
        """
        If a dataset schema has a declared foreign key to the dataset of this record, look for children
        Important note: Only a dataset with a declared 'primaryKey' in schema can be used for children lookup.
        :return: a Record queryset or None if the dataset has no declared primaryKey
        """
        if self.dataset.has_primary_key:
            children_datasets = self.dataset.get_children_datasets()
            if children_datasets:
                query = None
                for ds in children_datasets:
                    parent_field, child_field = ds.get_fk_lookup_fields_for_dataset(self.dataset)
                    if parent_field and child_field:
                        parent_value = self.data[parent_field]
                        if parent_value:
                            dataset_query = Q(dataset=ds, data__contains={child_field: parent_value})
                            query = query | dataset_query if query else dataset_query
                if query:
                    return Record.objects.filter(query)
            return Record.objects.none()
        else:
            return None

    def is_custodian(self, user):
        return self.dataset.is_custodian(user)

    def is_data_engineer(self, user):
        return self.dataset.data_engineer(user)

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
        user = request.user
        if is_admin(user):
            result = True
        elif 'dataset' in request.data:
            ds = Dataset.objects.filter(pk=request.data['dataset']).first()
            result = ds is not None and ds.is_custodian(user) or ds.is_data_engineer(user)
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
        user = request.user
        return is_admin(user) or self.is_custodian(user) or self.is_data_engineer(user)

    class Meta:
        ordering = ['id']


def get_media_path(instance, filename):
    """
    The function used in Media file field to build the path of the uploaded file.
    see model below
    https://docs.djangoproject.com/en/1.11/ref/models/fields/#filefield
    :param instance:
    :param filename:
    :return: string
    """
    try:
        return 'project_{project}/dataset_{dataset}/record_{record}/{filename}'.format(
            project=instance.project.id,
            dataset=instance.dataset.id,
            record=instance.record.id,
            filename=filename
        )
    except Exception as e:
        logger.exception('Error while building the media file name')
        return 'unknown/{}'.format(filename)


@python_2_unicode_compatible
class Media(models.Model):
    file = models.FileField(upload_to=get_media_path)
    record = models.ForeignKey(Record, blank=False, null=False, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "media"

    def __str__(self):
        return self.filename

    @property
    def path(self):
        return self.file.path

    @property
    def filename(self):
        return path.basename(self.path)

    @property
    def dataset(self):
        return self.record.dataset

    @property
    def project(self):
        return self.dataset.project

    def is_custodian(self, user):
        return self.record.is_custodian(user)

    def is_data_engineer(self, user):
        return self.record.is_data_engineer(user)

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
        user = request.user
        if is_admin(user):
            result = True
        elif 'record' in request.data:
            record = Record.objects.filter(pk=request.data['record']).first()
            result = record is not None and record.is_custodian(user) or record.is_data_engineer(user)
        return result

    @staticmethod
    def has_update_permission(request):
        """
        Update not allowed
        :param request:
        :return:
        """
        return False

    @staticmethod
    def has_destroy_permission(request):
        return True

    def has_object_destroy_permission(self, request):
        return is_admin(request.user) or self.is_custodian(request.user) or self.is_data_engineer(request.user)
