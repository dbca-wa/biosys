import codecs
import datetime
from os import path

import datapackage
from django.conf import settings
from django.utils import six, timezone
from django.utils.text import slugify
from openpyxl import load_workbook

from main.api.validators import get_record_validator_for_dataset
from main.constants import MODEL_SRID
from main.models import Site, Dataset
from main.utils_data_package import GeometryParser, ObservationSchema, SpeciesObservationSchema, BiosysSchema, \
    SpeciesNameParser
from main.utils_misc import get_value
from main.utils_species import HerbieFacade, get_key_for_value

# TODO: remove when python3
if six.PY2:
    import unicodecsv as csv
else:
    import csv


def xlsx_to_csv(file_):

    def _format(cell_):
        result = cell_.value
        if isinstance(result, datetime.datetime):
            result = result.strftime(settings.DATE_FORMAT)
        return result

    output = six.StringIO()
    writer = csv.writer(output)
    wb = load_workbook(filename=file_, read_only=True)
    # use the first sheet
    if len(wb.worksheets) > 0:
        ws = wb.worksheets[0]
        for row in ws.rows:
            r = [_format(cell) for cell in row]
            writer.writerow(r)
    # rewind
    output.seek(0)
    return output


# TODO: investigate the use frictionless tabulator.Stream as a xlsx/csv reader instead of this class
class FileReader(object):
    """
    Accept a csv or a xlsx as file and provide a row generator.
    Each row is a dictionary of (column_name, value)
    """
    CSV_TYPES = [
        'text/csv',
        'text/comma-separated-values',
        'application/csv'
    ]
    XLSX_TYPES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'application/vnd.msexcel',
    ]
    SUPPORTED_TYPES = CSV_TYPES + XLSX_TYPES

    CSV_FORMAT = 'csv'
    XLSX_FORMAT = 'xlsx'
    NOT_SUPPORTED_FORMAT = 'not supported'

    @staticmethod
    def get_uploaded_file_format(uploaded_file):
        """
        Return 'csv', 'xlsx' or 'not supported'
        :param uploaded_file: a Django uploaded file
        :return:
        """
        if not hasattr(uploaded_file, 'name') or not hasattr(uploaded_file, 'content_type'):
            raise Exception("The given file is not a django managed uploaded file: {}".format(uploaded_file))
        # check extension first
        # Note: on Windows the content-type for a csv file can be sent with an excel mime type.
        file_name = uploaded_file.name
        content_type = uploaded_file.content_type
        extension = path.splitext(file_name)[1].lower()
        if extension == '.csv' or content_type in FileReader.CSV_TYPES:
            result = FileReader.CSV_FORMAT
        elif extension == '.xlsx' or content_type in FileReader.XLSX_FORMAT:
            result = FileReader.XLSX_FORMAT
        else:
            result = FileReader.NOT_SUPPORTED_FORMAT
        return result

    def __init__(self, file_):
        self.file = file_
        if hasattr(file_, 'name'):
            self.file_name = file_.name
        file_format = self.get_uploaded_file_format(self.file)
        if file_format == self.NOT_SUPPORTED_FORMAT:
            msg = "Wrong file type {}. Should be one of: {}".format(file_.content_type, self.SUPPORTED_TYPES)
            raise Exception(msg)
        if file_format == self.XLSX_FORMAT:
            self.file = xlsx_to_csv(file_)
            self.reader = csv.DictReader(self.file)
        else:
            if six.PY3:
                self.reader = csv.DictReader(codecs.iterdecode(self.file, 'utf-8'))
            else:
                self.reader = csv.DictReader(self.file)
        # because users are stupid we want to trim/strip the headers (fieldnames).
        self.reader.fieldnames = [f.strip() for f in self.reader.fieldnames]
        if six.PY2 and hasattr(self.reader, 'unicode_fieldnames'):
            # we're using the unicode csv reader.
            self.reader.unicode_fieldnames = [f.strip() for f in self.reader.unicode_fieldnames]

    def __iter__(self):
        for row in self.reader:
            # remove 'blank' column
            for column in list(row.keys()):
                if not column.strip():
                    del row[column]
            yield row
        self.close()

    def close(self):
        self.file.close()


class SiteUploader(FileReader):
    COLUMN_MAP = {
        'code': ['code', 'site code', 'site_code'],
        'name': ['name', 'site name'],
        'description': ['description']
    }
    GEO_PARSER_SCHEMA = {
        "fields": [
            {
                "name": "Northing",
                "type": "number",
                "biosys": {
                    "type": "northing"
                }
            },
            {
                "name": "Easting",
                "type": "number",
                "biosys": {
                    "type": "easting"
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "biosys": {
                    "type": "latitude"
                },
                "constraints": {
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Longitude",
                "type": "number",
                "biosys": {
                    "type": "longitude"
                },
                "constraints": {
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            },
            {
                "type": "string",
                "name": "Datum",
            },
            {
                "type": "integer",
                "name": "Zone",
            }
        ]
    }

    def __init__(self, file_, project):
        super(SiteUploader, self).__init__(file_)
        self.project = project
        self.geo_parser = GeometryParser(self.GEO_PARSER_SCHEMA)

    def __iter__(self):
        for row in self.reader:
            yield self._create_or_update_site(row)

    def _create_or_update_site(self, row):
        # we need the code at minimum
        site, error = (None, None)
        code = get_value(self.COLUMN_MAP.get('code'), row)
        if not code:
            error = "Site Code is missing"
        else:
            kwargs = {
                'name': get_value(self.COLUMN_MAP.get('name'), row, ''),
                'description': get_value(self.COLUMN_MAP.get('description'), row, ''),
                'attributes': self._get_attributes(row)
            }
            # geometry
            try:
                kwargs['geometry'] = self.geo_parser.cast_geometry(row)
            except:
                # not an error (warning?)
                pass
            try:
                site, _ = Site.objects.update_or_create(code=code, project=self.project, defaults=kwargs)
            except Exception as e:
                error = str(e)
        return site, error

    def _get_attributes(self, row):
        """
        Everything not in the COLUMN_MAP is an attribute
        :return: a dict
        """
        attributes = {}
        non_attributes_keys = [k.lower() for sublist in self.COLUMN_MAP.values() for k in sublist]
        for k, v in row.items():
            if k.lower() not in non_attributes_keys:
                attributes[k] = v
        return attributes


class RecordCreator:
    def __init__(self, dataset, data_generator,
                 commit=True, create_site=False, validator=None, species_facade_class=HerbieFacade):
        self.dataset = dataset
        self.generator = data_generator
        self.create_site = create_site
        self.dataset = dataset
        self.schema = dataset.schema
        self.record_model = dataset.record_model
        self.validator = validator if validator else get_record_validator_for_dataset(dataset)
        # if species. First load species list from herbie. Should raise an exception if problem.
        self.species_id_by_name = {}
        if dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
            self.species_id_by_name = species_facade_class().name_id_by_species_name()
        # Schema foreign key for site.
        self.site_fk = self.schema.get_fk_for_model('Site')
        self.commit = commit
        self.file_name = self.generator.file_name if hasattr(self.generator, 'file_name') else None
        # Trick: use GeometryParser to get the site code
        self.geo_parser = GeometryParser(self.schema)

    def __iter__(self):
        counter = 0
        for data in self.generator:
            counter += 1
            yield self._create_record(data, counter)

    def _create_record(self, row, counter):
        """
        :param row: a {column(string): value(string)} dictionary
        :return: record, RecordValidatorResult
        """
        validator_result = self.validator.validate(row)
        record = None
        # The row values comes as string but we want to save numeric field as json number not string to allow a
        # correct ordering. The next call will cast the numeric field into python int or float.
        row = self.schema.cast_numbers(row)
        try:
            if validator_result.is_valid:
                site = self._get_or_create_site(row)
                record = self.record_model(
                    site=site,
                    dataset=self.dataset,
                    data=row,
                    source_info={
                        'file_name': self.file_name,
                        'row': counter + 1  # add one to match excel/csv row id
                    }
                )
                # specific fields
                if self.dataset.type == Dataset.TYPE_OBSERVATION or self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                    observation_date = self.schema.cast_record_observation_date(row)
                    if observation_date:
                        # convert to datetime with timezone awareness
                        if isinstance(observation_date, datetime.date):
                            observation_date = datetime.datetime.combine(observation_date, datetime.time.min)
                        tz = self.dataset.project.timezone or timezone.get_current_timezone()
                        record.datetime = timezone.make_aware(observation_date, tz)

                    # geometry
                    geometry = self.schema.cast_geometry(row, default_srid=self.dataset.project.datum or MODEL_SRID)
                    record.geometry = geometry
                    if self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                        # species stuff. Lookup for species match in herbie.
                        # either a species name or a nameId
                        species_name = self.schema.cast_species_name(row)
                        name_id = self.schema.cast_species_name_id(row)
                        # name id takes precedence
                        if name_id:
                            species_name = get_key_for_value(self.species_id_by_name, int(name_id), None)
                            if not species_name:
                                column_name = self.schema.species_name_parser.name_id_field.name
                                message = "Cannot find a species with nameId={}".format(name_id)
                                validator_result.add_column_error(column_name, message)
                                return record, validator_result
                        elif species_name:
                            name_id = int(self.species_id_by_name.get(species_name, -1))
                        record.species_name = species_name
                        record.name_id = name_id
                if self.commit:
                    record.save()
        except Exception as e:
            # catch all errors
            message = str(e)
            validator_result.add_column_error('unknown', message)
        return record, validator_result

    def _get_or_create_site(self, row):
        site = None
        if self.geo_parser.is_valid() and self.geo_parser.is_site_code:
            site_code = self.geo_parser.get_site_code(row)
            kwargs = {
                "project": self.dataset.project,
                "code": site_code
            }
            site = Site.objects.filter(**kwargs).first()
            if site is None and self.create_site:
                site = Site.objects.create(**kwargs)
        return site


class DataPackageBuilder:

    @staticmethod
    def infer_from_file(file_path, format_='xlsx', name=None):
        dir_name = path.dirname(file_path)
        builder = DataPackageBuilder(base_path=dir_name, title=name)
        builder._add_resource_from_file(file_path, format_=format_, name=name)
        return builder

    @staticmethod
    def set_type(type_, field):
        field['type'] = type_

    @staticmethod
    def set_required(field, required=True):
        constraints = field.get('constraints', {})
        constraints['required'] = required
        field['constraints'] = constraints

    @staticmethod
    def set_biosys_type(field, type_):
        biosys_tag = field.get(BiosysSchema.BIOSYS_KEY_NAME, {})
        biosys_tag['type'] = type_
        field[BiosysSchema.BIOSYS_KEY_NAME] = biosys_tag

    def __init__(self, descriptor=None, title=None, **kwargs):
        descriptor = descriptor or {}
        if title:
            descriptor['title'] = title
            descriptor['name'] = slugify(title)
        self.package = datapackage.Package(descriptor, **kwargs)
        self.biosys_errors = []

    def _add_resource_from_file(self, file_path, format_='xlsx', name=None):
        try:
            file_name = path.basename(file_path)
            name = slugify(name or path.splitext(file_name)[0])
            resource = self.package.add_resource({
                'path': path.basename(file_path),
                'name': name,
                'format': format_
            })
            self.package.infer()
            self._biosys_infer()
            # biosys support only one resources by package
            if len(self.resources) > 1:
                self.biosys_errors.append(
                    Exception('More than one resources. Biosys supports only one resources per data-package.')
                )
            return resource.descriptor
        except Exception as e:
            self.biosys_errors.append(e)
            return None

    def infer_biosys_type(self):
        """
        Use the schema models in utils to infer the type.
        The constructor should throw an exception if something is not correct
        :return:
        """
        # TODO: use a better control workflow than exception
        try:
            SpeciesObservationSchema(self.schema)
            return Dataset.TYPE_SPECIES_OBSERVATION
        except Exception:
            try:
                ObservationSchema(self.schema)
                return Dataset.TYPE_OBSERVATION
            except Exception:
                return Dataset.TYPE_GENERIC

    @property
    def valid(self):
        return self.package.valid and not bool(self.biosys_errors)

    @property
    def errors(self):
        return self.package.errors + self.biosys_errors

    @property
    def descriptor(self):
        return self.package.descriptor

    @property
    def title(self):
        return self.descriptor.get('title')

    @property
    def resources(self):
        return self.package.resources

    @property
    def schema(self):
        return self.package.descriptor.get('resources')[0].get('schema') if len(self.resources) > 0 else None

    @property
    def fields(self):
        return self.schema.get('fields') if self.schema else []

    def get_fields_by_name(self, name):
        return [f for f in self.fields if f.get('name') == name]

    def _biosys_infer(self):
        """
        Rules:
        - Fields of type 'any' should be converted to type 'string'
        - Fields of type 'date' or 'datetime' should have format = 'any' instead of default
          (the 'any' makes the date parser more flexible)
        - infer observation type
        - infer species observation type.
        """
        for field in self.fields:
            type_ = field.get('type')
            format_ = field.get('format')

            if type_ == 'any':
                field['type'] = 'string'

            if type_ in ['date', 'datetime'] and format_ == 'default':
                field['format'] = 'any'

        is_observation = self._infer_observation()
        if is_observation:
            self._infer_species_observation()
        self.package.commit()

    def _infer_observation(self):
        """
        Try to infer an Observation from column names and modify field attributes to match the schema specification.

        Scenarios:
        - If it contains a latitude/longitude fields set the lat/long columns type='number' with constraint required
          and they should be tagged with the correct biosys tag.
        - If it contains a easting/northing fields set the easting/northing columns type='number' with constraint required
          and they should be tagged with the correct biosys tag.

        see tests.api.test_schema_inference.TestObservation for full specs.

        :return: True if successfully inferred an observation
        """
        success = False
        try:
            # geometry inference
            geo_parser = GeometryParser(self.schema)
            # Lat/Long
            if geo_parser.is_lat_long:
                lat_field = self.get_fields_by_name(geo_parser.latitude_field.name)[0]
                lon_field = self.get_fields_by_name(geo_parser.longitude_field.name)[0]
                self.set_type('number', lat_field)
                self.set_type('number', lon_field)
                self.set_biosys_type(lat_field, BiosysSchema.LATITUDE_TYPE_NAME)
                self.set_biosys_type(lon_field, BiosysSchema.LONGITUDE_TYPE_NAME)
                if geo_parser.is_lat_long_only:
                    self.set_required(lat_field)
                    self.set_required(lon_field)
                if geo_parser.has_datum:
                    datum_field = self.get_fields_by_name(geo_parser.datum_field.name)[0]
                    self.set_type('string', datum_field)
                    self.set_biosys_type(datum_field, BiosysSchema.DATUM_TYPE_NAME)
                success = True

            # Easting/Northing
            if geo_parser.is_easting_northing:
                easting_field = self.get_fields_by_name(geo_parser.easting_field.name)[0]
                northing_field = self.get_fields_by_name(geo_parser.northing_field.name)[0]
                self.set_type('number', easting_field)
                self.set_type('number', northing_field)
                self.set_biosys_type(easting_field, BiosysSchema.EASTING_TYPE_NAME)
                self.set_biosys_type(northing_field, BiosysSchema.NORTHING_TYPE_NAME)
                if geo_parser.is_easting_northing_only:
                    self.set_required(easting_field)
                    self.set_required(northing_field)
                if geo_parser.has_datum:
                    datum_field = self.get_fields_by_name(geo_parser.datum_field.name)[0]
                    self.set_type('string', datum_field)
                    self.set_biosys_type(datum_field, BiosysSchema.DATUM_TYPE_NAME)
                    if not geo_parser.has_zone:
                        self.set_required(datum_field)
                if geo_parser.has_zone:
                    zone_field = self.get_fields_by_name(geo_parser.zone_field.name)[0]
                    self.set_type('integer', zone_field)
                    self.set_biosys_type(zone_field, BiosysSchema.ZONE_TYPE_NAME)
                    if not geo_parser.has_datum:
                        self.set_required(zone_field)
                success = True
        except Exception as e:
            self.errors.append(str(e))
            success = False

        return success

    def _infer_species_observation(self):
        """
        Try to infer a Species Observation from column names and modify field attributes to match the schema
        specification.
        Warning: this method assumes that the Observation inference part has been done.
        Scenarios:
        - If it contains a column 'Species Name' it should be a string and they should be tagged
        with the correct biosys tag. If it's the only species column it should be set as required
        - Same for columns 'genus' and 'species'.

        see tests.api.test_schema_inference.TestSpeciesObservation for full specs.

        :return: True if successfully inferred an observation
        """
        success = False
        try:
            parser = SpeciesNameParser(self.schema)
            if parser.has_species_name:
                species_name_field = self.get_fields_by_name(parser.species_name_field.name)[0]
                self.set_type('string', species_name_field)
                self.set_biosys_type(species_name_field, BiosysSchema.SPECIES_NAME_TYPE_NAME)
                if parser.is_species_name_only:
                    self.set_required(species_name_field)
                success = True
            if parser.has_genus_and_species:
                genus_field = self.get_fields_by_name(parser.genus_field.name)[0]
                self.set_type('string', genus_field)
                self.set_biosys_type(genus_field, BiosysSchema.GENUS_TYPE_NAME)

                species_field = self.get_fields_by_name(parser.species_field.name)[0]
                self.set_type('string', species_field)
                self.set_biosys_type(species_field, BiosysSchema.SPECIES_TYPE_NAME)
                if parser.is_genus_and_species_only:
                    self.set_required(genus_field)
                    self.set_required(species_field)
                if parser.infra_rank_field:
                    infra_rank_field = self.get_fields_by_name(parser.infra_rank_field.name)[0]
                    self.set_type('string', infra_rank_field)
                    self.set_biosys_type(infra_rank_field, BiosysSchema.INFRA_SPECIFIC_RANK_TYPE_NAME)
                if parser.infra_name_field:
                    infra_name_field = self.get_fields_by_name(parser.infra_name_field.name)[0]
                    self.set_type('string', infra_name_field)
                    self.set_biosys_type(infra_name_field, BiosysSchema.INFRA_SPECIFIC_NAME_TYPE_NAME)
                success = True

        except Exception as e:
            self.errors.append(str(e))
            success = False

        return success
