from __future__ import absolute_import, unicode_literals, print_function, division

import io
import json
import re
from os import listdir
from os.path import join

import jsontableschema
from dateutil.parser import parse as date_parse
from django.contrib.gis.geos import Point
from django.utils import six
from django.utils.encoding import python_2_unicode_compatible
from future.utils import raise_with_traceback
from jsontableschema.exceptions import InvalidDateType
from jsontableschema.model import SchemaModel, types
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.writer.write_only import WriteOnlyCell

from main.constants import MODEL_SRID, SUPPORTED_DATUMS, get_datum_srid, is_supported_datum, get_australian_zone_srid

COLUMN_HEADER_FONT = Font(bold=True)
YYYY_MM_DD_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}')


def is_blank_value(value):
    return value is None or is_empty_string(value)


def is_empty_string(value):
    return isinstance(value, six.string_types) and len(value.strip()) == 0


class ObservationSchemaError(Exception):
    # don't  extend InvalidSchemaError (problem with message not showing in the str method)
    pass


class SpeciesObservationSchemaError(Exception):
    pass


class GeometrySchemaError(Exception):
    pass


class InvalidDatumError(Exception):
    pass


class FieldSchemaError(Exception):
    pass


def parse_datetime_day_first(value):
    """
    use the dateutil.parse() to parse a date/datetime with the date first (dd/mm/yyyy) (not month first mm/dd/yyyy)
    in case of ambiguity
    :param value:
    :return:
    """
    # there's a 'bug' in dateutil.parser.parse (2.5.3). If you are using
    # dayfirst=True. It will parse YYYY-MM-DD as YYYY-DD-MM !!
    # https://github.com/dateutil/dateutil/issues/268
    dayfirst = not YYYY_MM_DD_REGEX.match(value)
    return date_parse(value, dayfirst=dayfirst)


class DayFirstDateType(types.DateType):
    """
    Extend the jsontableschema DateType which use the mm/dd/yyyy date model for the 'any' format
    to use dd/mm/yyyy
    """

    def cast_any(self, value, fmt=None):
        if isinstance(value, self.python_type):
            return value
        try:
            return parse_datetime_day_first(value).date()
        except (TypeError, ValueError) as e:
            raise_with_traceback(InvalidDateType(e))


class DayFirstDateTimeType(types.DateTimeType):
    """
    Extend the jsontableschema DateType which use the mm/dd/yyyy date model for the 'any' format
    to use dd/mm/yyyy
    """

    def cast_any(self, value, fmt=None):
        if isinstance(value, self.python_type):
            return value
        try:
            return parse_datetime_day_first(value)
        except (TypeError, ValueError) as e:
            raise_with_traceback(InvalidDateType(e))


class NotBlankStringType(types.StringType):
    """
    The default StringType accepts empty string when required = True
    """
    null_values = ['null', 'none', 'nil', 'nan', '-', '']


@python_2_unicode_compatible
class BiosysSchema:
    """
    The utility class for the biosys data within a schema field

    {
      name: "...."
      constraints: ....
      biosys: {
                type: [observationDate]
              }
    }
    """
    OBSERVATION_DATE_TYPE_NAME = 'observationDate'
    LATITUDE_TYPE_NAME = 'latitude'
    LONGITUDE_TYPE_NAME = 'longitude'
    DATUM_TYPE_NAME = 'datum'
    ZONE_TYPE_NAME = 'zone'
    SPECIES_NAME_TYPE_NAME = 'speciesName'
    SPECIES_NAME_ID_TYPE_NAME = 'speciesNameId'

    BIOSYS_TYPE_MAP = {
        OBSERVATION_DATE_TYPE_NAME: DayFirstDateType,
    }

    def __init__(self, data):
        self.data = data or {}

    # implement some dict like methods
    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __str__(self):
        return "BiosysSchema: {}".format(self.data)

    @property
    def type(self):
        return self.get('type')

    def get(self, k, d=None):
        return self.data.get(k, d)

    def is_observation_date(self):
        return self.type == self.OBSERVATION_DATE_TYPE_NAME

    def is_latitude(self):
        return self.type == self.LATITUDE_TYPE_NAME

    def is_longitude(self):
        return self.type == self.LONGITUDE_TYPE_NAME

    def is_datum(self):
        return self.type == self.DATUM_TYPE_NAME

    def is_zone(self):
        return self.type == self.ZONE_TYPE_NAME

    def is_species_name(self):
        return self.type == self.SPECIES_NAME_TYPE_NAME

    def is_species_name_id(self):
        return self.type == self.SPECIES_NAME_ID_TYPE_NAME


@python_2_unicode_compatible
class SchemaField:
    """
    Utility class for a field in a schema.
    It uses the schema types of
    https://github.com/frictionlessdata/jsontableschema-py#types
    for validation.
    """
    # For most of the type we use the jsontableschema ones
    BASE_TYPE_MAP = SchemaModel._type_map()
    # except for the date we use our custom one.
    BASE_TYPE_MAP['date'] = DayFirstDateType
    BASE_TYPE_MAP['datetime'] = DayFirstDateTimeType
    BASE_TYPE_MAP['string'] = NotBlankStringType

    BIOSYS_TYPE_MAP = {
    }

    def __init__(self, data):
        self.data = data
        self.name = self.data.get('name')
        # We want to throw an exception if there is no name
        if not self.name:
            raise FieldSchemaError("A field without a name: {}".format(json.dumps(data)))
        # biosys specific
        self.biosys = BiosysSchema(self.data.get('biosys'))
        # set the type: biosys type as precedence
        type_class = self.BIOSYS_TYPE_MAP.get(self.biosys.type) or self.BASE_TYPE_MAP.get(self.data.get('type'))
        self.type = type_class(self.data)
        self.constraints = SchemaConstraints(self.data.get('constraints', {}))

    # implement some dict like methods
    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get(self, k, d=None):
        return self.data.get(k, d)

    @property
    def title(self):
        return self.data.get('title')

    @property
    def column_name(self):
        return self.name

    @property
    def required(self):
        return self.constraints.required

    @property
    def aliases(self):
        return self.data['aliases'] if 'aliases' in self.data else []

    def has_alias(self, name, icase=False):
        for alias in self.aliases:
            if (alias == name) or (icase and alias.lower() == name.lower()):
                return True
        return False

    def has_name_or_alias(self, name, alias, icase=False):
        """
        Test is the field has a name name or an alias alias
        :param name:
        :param alias:
        :param icase:
        :return:
        """
        has_name = (self.name == name) or (icase and self.name.lower() == name.lower())
        return has_name or self.has_alias(alias, icase=icase)

    def cast(self, value):
        """
        Returns o native Python object of the expected format. Will throw an exception
        if the value doesn't complies with any constraints. See for details:
        https://github.com/frictionlessdata/jsontableschema-py#types
        This method is mainly a helper for the validation_error
        :param value:
        :return:
        """
        # TODO: remove that when running in Python3
        if isinstance(value, six.string_types) and not isinstance(value, six.text_type):
            # the StringType accepts only unicode
            value = six.u(value)
        return self.type.cast(value)

    def validation_error(self, value):
        """
        Return an error message if the value is not valid according to the schema.
        It relies on exception thrown by the 'cast1 method of Type method.
        :param value:
        :return: None if value is valid or an error message string
        """
        error = None
        # override the integer validation. The default message is a bit cryptic if there's an error casting a string
        # like '1.2' into an int.
        if isinstance(self.type, types.IntegerType):
            if not is_blank_value(value):
                not_integer = False
                try:
                    casted = self.cast(value)
                    # there's also the case where the case where a float 1.2 is successfully casted in 1
                    # (ex: int(1.2) = 1)
                    if str(casted) != str(value):
                        not_integer = True
                except Exception:
                    not_integer = True
                if not_integer:
                    return 'The field "{}" must be a whole number.'.format(self.name)
        try:
            self.cast(value)
        except Exception as e:
            error = "{}".format(e)
            # Override the default enum exception message to include all possible values
            if error.find('enum array') and self.constraints.enum:
                values = [str(v) for v in self.constraints.enum]
                error = "The value must be one the following: {}".format(values)
        return error

    def __str__(self):
        return '{}'.format(self.name)


class SchemaConstraints:
    """
    A helper class for a schema field constraints
    """

    def __init__(self, data):
        self.data = data or {}

    # implement some dict like methods
    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get(self, k, d=None):
        return self.data.get(k, d)

    @property
    def required(self):
        return self.get('required', False)

    @property
    def enum(self):
        return self.get('enum')


@python_2_unicode_compatible
class SchemaForeignKey:
    """
    A utility class for foreign key in schema
    """

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return 'Foreign Key {}'.format(self.data)

    # implement some dict like methods
    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get(self, k, d=None):
        return self.data.get(k, d)

    @staticmethod
    def _as_list(value):
        if isinstance(value, list):
            return value
        elif isinstance(value, six.string_types):
            return [value]
        else:
            return list(value)

    @property
    def fields(self):
        return self._as_list(self.data.get('fields', []))

    @property
    def data_field(self):
        return self.fields[0] if self.fields else None

    @property
    def reference(self):
        return self.data.get('reference', {})

    @property
    def reference_fields(self):
        return self._as_list(self.reference.get('fields', []))

    @property
    def reference_resource(self):
        return self.reference.get('resource')

    @property
    def model(self):
        return self.reference_resource

    @property
    def model_field(self):
        return self.reference_fields[0] if self.reference_fields else None


@python_2_unicode_compatible
class GenericSchema(object):
    """
    A utility class for schema.
    It uses internally an instance SchemaModel of the frictionless jsontableschema for help.
    https://github.com/frictionlessdata/jsontableschema-py#model
    Will throw an exception if the schema is not valid
    """

    def __init__(self, schema):
        self.data = schema
        self.schema_model = SchemaModel(schema)
        self.fields = [SchemaField(f) for f in self.schema_model.fields]
        self.foreign_keys = [SchemaForeignKey(fk) for fk in
                             self.schema_model.foreignKeys] if self.schema_model.foreignKeys else []

    # implement some dict like methods
    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def get(self, k, d=None):
        return self.data.get(k, d)

    @property
    def headers(self):
        return self.field_names

    @property
    def field_names(self):
        return [f.name for f in self.fields]

    @property
    def required_fields(self):
        return [f for f in self.fields if f.required]

    def get_field_by_mame(self, name):
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def field_validation_error(self, field_name, value):
        field = self.get_field_by_mame(field_name)
        if field is not None:
            return field.validation_error(value)
        else:
            raise Exception("The field '{}' doesn't exists in the schema. Should be one of {}"
                            .format(field_name, self.field_names))

    def is_field_valid(self, field_name, value):
        return self.field_validation_error(field_name, value) is None

    def validate_row(self, row):
        """
        The row must be a dictionary or a list of key => value
        :param row:
        :return: return a dictionary with an error added to the field
        {
            field_name: {
                value: value (as given)
                error: None or error message
        }
        """
        row = dict(row)
        result = {}
        for field_name, value in row.items():
            error = self.field_validation_error(field_name, value)
            result[field_name] = {
                'value': value,
                'error': error
            }
        return result

    def rows_validator(self, rows):
        for row in rows:
            yield self.validate_row(row)

    def get_error_fields(self, row):
        """
        Return the field that does not validate
        :param row: a key value dict or tuple
        :return: [(field_name, {'value':value, 'error':error_string}]
        """
        validated_row = self.validate_row(row)
        errors = []
        for field, data in validated_row.items():
            if data.get('error'):
                errors.append((field, data))
        return errors

    def is_row_valid(self, row):
        return len(self.get_error_fields(row)) == 0

    def is_all_valid(self, rows):
        for row in rows:
            if not self.is_row_valid(row):
                return False
        return True

    def has_fk_for_model(self, model_name):
        return self.get_fk_for_model(model_name) is not None

    def get_fk_for_model(self, model_name):
        for fk in self.foreign_keys:
            if fk.model == model_name:
                return fk
        return None

    def has_fk_for_model_field(self, model_name, model_field):
        return self.get_fk_for_model_field(model_name, model_field) is not None

    def get_fk_for_model_field(self, model_name, model_field):
        for fk in self.foreign_keys:
            if fk.model == model_name and fk.model_field == model_field:
                return fk
        return None

    def __str__(self):
        return self.get('name')


class ObservationSchema(GenericSchema):
    """
     A schema specific to an Observation Dataset.
     Its main job is to deal with the observation date and its geometry
     (lat/long or geojson)
     There's a special case: a lat/long or geometry field can be omitted if there's a reference (foreign key)
     to a site code (only)
    """
    OBSERVATION_DATE_FIELD_NAME = 'Observation Date'
    LATITUDE_FIELD_NAME = 'Latitude'
    LONGITUDE_FIELD_NAME = 'Longitude'
    DATUM_FIELD_NAME = 'Datum'
    ZONE_FIELD_NAME = 'Zone'
    SITE_CODE_FOREIGN_KEY_EXAMPLE = """
        "foreignKeys": [
            {
                "fields": ["Site Code"],
                "reference": {
                    "fields": ["code"],
                    "resource": "Site"
                }
            }
        ]
     """

    def __init__(self, schema):
        super(ObservationSchema, self).__init__(schema)
        self.observation_date_field = self.find_observation_date_field_or_throw(self)
        site_code_fk = self.get_fk_for_model_field('Site', 'code')
        self.site_code_field = self.get_field_by_mame(site_code_fk.data_field) if site_code_fk else None
        if self.site_code_field is None:
            self.latitude_field = self.find_latitude_field_or_throw(self)
            self.longitude_field = self.find_longitude_field_or_throw(self)
        else:
            # we have a site code foreign key but we also can have lat/long field to overwrite the geometry
            try:
                self.latitude_field = self.find_latitude_field_or_throw(self, enforce_required=False)
            except ObservationSchemaError:
                self.latitude_field = None
            try:
                self.longitude_field = self.find_longitude_field_or_throw(self, enforce_required=False)
            except ObservationSchemaError:
                self.longitude_field = None
        self.datum_field = self.find_datum_field_or_none(self)
        self.zone_field = self.find_zone_field_or_none(self)

    # The following methods are static for testing purposes.
    @staticmethod
    def find_observation_date_field_or_throw(schema):
        """
        Precedence Rules:
        1- Look for a single date field with required = true
        2- Look for biosys.type = 'observationDate'
        3- Look for a field with name 'Observation Date' case insensitive
        4- If there's only one field of type date it's this one.
        5- Throw exception if not found
        :param schema: a dict descriptor or a Schema instance
        :return: The SchemaField or raise an exception if none or more than one
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        # edge case: a biosys observationDate set as not required
        if len([field for field in schema.fields
                if field.biosys.is_observation_date() and not field.required]) > 0:
            msg = "A biosys observationDate with required=false detected. It must be set required=true"
            raise ObservationSchemaError(msg)
        # normal cases
        required_date_fields = [field for field in schema.fields
                                if
                                (isinstance(field.type, types.DateType) or isinstance(field.type,
                                                                                      types.DateTimeType)) and
                                field.required
                                ]
        dates_count = len(required_date_fields)
        if dates_count == 0:
            msg = "One field must be of type 'date' with 'required': true to be a valid Observation schema."
            raise ObservationSchemaError(msg)
        if dates_count == 1:
            return required_date_fields[0]
        else:
            # more than one date fields. Look the the biosys type
            fields = [field for field in required_date_fields if field.biosys.is_observation_date()]
            count = len(fields)
            if count == 1:
                return fields[0]
            if count > 1:
                msg = "The schema contains more than one field tagged as a biosys type=observationDate"
                raise ObservationSchemaError(msg)
            # no biosys observation date. Look for field name
            fields = [field for field in required_date_fields if
                      field.name == ObservationSchema.OBSERVATION_DATE_FIELD_NAME]
            count = len(fields)
            if count == 1:
                return fields[0]
            if count > 1:
                msg = "The schema contains more than one field named Observation Date. " \
                      "One should be tagged as a biosys type=observationDate "
                raise ObservationSchemaError(msg)
            msg = "The schema doesn't include a required Observation Date field. " \
                  "It must have a field named {} or tagged with biosys type {}". \
                format(ObservationSchema.OBSERVATION_DATE_FIELD_NAME, BiosysSchema.OBSERVATION_DATE_TYPE_NAME)
            raise ObservationSchemaError(msg)

    @staticmethod
    def find_latitude_field_or_throw(schema, enforce_required=True):
        """
        Precedence Rules:
        2- Look for biosys.type = 'latitude'
        3- Look for a field with name 'Latitude' case insensitive
        :param enforce_required: if True the field must have a required constraints
        :param schema: a dict descriptor or a Schema instance
        :return: The SchemaField or raise an exception if none or more than one
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_latitude()]
        if len(fields) > 1:
            msg = "More than one Biosys latitude field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if enforce_required and not field.required:
                msg = "The Biosys latitude field must be set as 'required'. {}".format(field)
                raise ObservationSchemaError(msg)
            else:
                return field
        # no Biosys latitude field found
        fields = [f for f in schema.fields if f.name.lower() == ObservationSchema.LATITUDE_FIELD_NAME.lower()]
        if len(fields) > 1:
            msg = "More than one Latitude field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if enforce_required and not field.required:
                msg = "The Latitude field must be set as 'required'. {}".format(field)
                raise ObservationSchemaError(msg)
            else:
                return field
        msg = "The schema doesn't include a required latitude field. " \
              "It must have a field named {} or tagged with biosys type {}. " \
              "Alternatively you can add a foreign key the site code to extract the geometry from it. " \
              "To create site code foreign key, add the following to you schema:{}". \
            format(ObservationSchema.LATITUDE_FIELD_NAME,
                   BiosysSchema.LATITUDE_TYPE_NAME,
                   ObservationSchema.SITE_CODE_FOREIGN_KEY_EXAMPLE)
        raise ObservationSchemaError(msg)

    @staticmethod
    def find_longitude_field_or_throw(schema, enforce_required=True):
        """
        Precedence Rules:
        1- Look for biosys.type = 'longitude'
        2- Look for a field with name 'Longitude' case insensitive
        :param schema: a dict descriptor or a Schema instance
        :param enforce_required: if True the field must have a required constraints
        :return: The SchemaField or raise an exception if none or more than one
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_longitude()]
        if len(fields) > 1:
            msg = "More than one Biosys longitude field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if enforce_required and not field.required:
                msg = "The Biosys longitude field must be set as 'required'. {}".format(field)
                raise ObservationSchemaError(msg)
            else:
                return field
        # no Biosys longitude field found look for column name
        fields = [f for f in schema.fields if f.name.lower() == ObservationSchema.LONGITUDE_FIELD_NAME.lower()]
        if len(fields) > 1:
            msg = "More than one Longitude field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if enforce_required and not field.required:
                msg = "The Longitude field must be set as 'required'. {}".format(field)
                raise ObservationSchemaError(msg)
            else:
                return field
        msg = "The schema doesn't include a required longitude field. " \
              "It must have a field named {} or tagged with biosys type {}" \
              "Alternatively you can add a foreign key the site code to extract the geometry from it. " \
              "To create site code foreign key, add the following to you schema:{}". \
            format(ObservationSchema.LONGITUDE_FIELD_NAME,
                   BiosysSchema.LONGITUDE_TYPE_NAME,
                   ObservationSchema.SITE_CODE_FOREIGN_KEY_EXAMPLE)
        raise ObservationSchemaError(msg)

    @staticmethod
    def find_datum_field_or_none(schema):
        """
        Precedence Rules:
        1- Look for biosys.type = 'datum'
        2- Look for a field with name 'Datum' case insensitive
        :param schema: a dict descriptor or a Schema instance
        :return: None if not found
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_datum()]
        if len(fields) > 1:
            msg = "More than one Biosys datum field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            return fields[0]
        # no Biosys datum field found look for column name
        fields = [f for f in schema.fields if f.name.lower() == ObservationSchema.DATUM_FIELD_NAME.lower()]
        if len(fields) > 1:
            msg = "More than one Datum field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            return fields[0]
        return None

    @staticmethod
    def find_zone_field_or_none(schema):
        """
        Precedence Rules:
        1- Look for biosys.type = 'zone'
        2- Look for a field with name 'Zone' case insensitive
        :param schema: a dict descriptor or a Schema instance
        :return: None if not found
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_zone()]
        if len(fields) > 1:
            msg = "More than one Biosys zone type field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            return fields[0]
        # no Biosys zone type field found look for column name
        fields = [f for f in schema.fields if f.name.lower() == ObservationSchema.ZONE_FIELD_NAME.lower()]
        if len(fields) > 1:
            msg = "More than one Zone field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            return fields[0]
        return None

    def find_site_code_foreign(self):
        return self.get_fk_for_model_field('Site', 'code')

    def get_record_observation_date_value(self, record):
        return record.get(self.observation_date_field.name)

    def cast_record_observation_date(self, record):
        field = self.observation_date_field
        return field.cast(record.get(field.name))

    def cast_srid(self, record, default_srid=MODEL_SRID):
        """
        Two cases:
        Datum only or datum + zone
        :param record:
        :param default_srid:
        :return:
        """
        result = default_srid
        if self.datum_field:
            datum_val = record.get(self.datum_field.name)
            if self.zone_field:
                zone_val = record.get(self.zone_field.name)
                try:
                    int(zone_val)
                except:
                    msg = "Invalid Zone '{}'. Should be an integer.".format(zone_val)
                    raise InvalidDatumError(msg)
                try:
                    result = get_australian_zone_srid(datum_val, zone_val)
                except Exception as e:
                    raise InvalidDatumError(e)
            else:
                if not is_supported_datum(datum_val):
                    msg = "Invalid Datum '{}'. Should be one of: {}".format(datum_val, SUPPORTED_DATUMS)
                    raise InvalidDatumError(msg)
                else:
                    result = get_datum_srid(datum_val)
        return result

    def cast_geometry(self, record, default_srid=MODEL_SRID):
        """
        Two cases: either a lat/lon or a site code foreign key.
        The lat/lon values take precedence over the site.
        :param record:
        :param default_srid:
        :return:
        """
        lat_val = record.get(self.latitude_field.name) if self.latitude_field is not None else None
        lon_val = record.get(self.longitude_field.name) if self.longitude_field is not None else None
        if lat_val and lon_val:
            lat = self.latitude_field.cast(lat_val)
            lon = self.longitude_field.cast(lon_val)
            srid = self.cast_srid(record, default_srid=default_srid)
            return Point(x=float(lon), y=float(lat), srid=srid)
        elif self.site_code_field:
            from main.models import Site  # import here to avoid cyclic import problem
            site_code = record.get(self.site_code_field.name)
            site = Site.objects.filter(code=site_code, geometry__isnull=False).first()
            if site is None:
                raise Exception('The site {} does not exist or has no geometry'.format(site_code))
            else:
                return site.geometry
        else:
            # problem.
            raise Exception('No lat/long or site code found!')


class SpeciesObservationSchema(ObservationSchema):
    """
    An ObservationSchema with a Species Name
    """
    SPECIES_NAME_FIELD_NAME = 'Species Name'
    SPECIES_NAME_ID_FIELD_NAMES_LOWER = ['name id', 'nameid', 'species nameid', 'species name id']

    def __init__(self, schema):
        """
        An ObservationSchema with a field for species name or species nameid
        :param schema:
        """
        super(SpeciesObservationSchema, self).__init__(schema)
        try:
            self.species_name_field = self.find_species_name_field_or_throws(self, enforce_required=False)
        except SpeciesObservationSchemaError:
            self.species_name_field = None
        try:
            self.species_name_id_field = self.find_species_name_id_field(self)
        except SpeciesObservationSchemaError:
            self.species_name_field = None
        if not self.species_name_field and not self.species_name_id_field:
            msg = "The schema doesn't include a 'Species Name' field or a 'NameId' field. " \
                  "In order to be a valid Species Observation one of these fields must be specified. " \
                  "Alternatively you can 'tag' a field by adding a biosys type {} or {}" \
                .format(BiosysSchema.SPECIES_NAME_TYPE_NAME, BiosysSchema.SPECIES_NAME_ID_TYPE_NAME)
            raise SpeciesObservationSchemaError(msg)
        # if only one of the fields it must be required
        if self.species_name_field and not self.species_name_id_field and not self.species_name_field.required:
            msg = 'The {field_name} field must be set as "required" (add "required": true in the constraints)'.format(
                field_name=self.species_name_field.name
            )
            raise SpeciesObservationSchemaError(msg)
        if not self.species_name_field and self.species_name_id_field and not self.species_name_id_field.required:
            msg = 'The {field_name} field must be set as "required" (add "required": true in the constraints)'.format(
                field_name=self.species_name_id_field.name
            )
            raise SpeciesObservationSchemaError(msg)

    @staticmethod
    def find_species_name_field_or_throws(schema, enforce_required=True):
        """
        Precedence Rules:
        2- Look for biosys.type = 'speciesName'
        3- Look for a field with name 'Species Name' case insensitive
        :param schema: a dict descriptor or a Schema instance
        :return: The SchemaField or raise an exception if none or more than one
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_species_name()]
        if len(fields) > 1:
            msg = "More than one Biosys speciesName field found!. {}".format(fields)
            raise SpeciesObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if enforce_required and not field.required:
                msg = "The Biosys speciesName field must be set as 'required'. {}".format(field)
                raise SpeciesObservationSchemaError(msg)
            else:
                return field
        # no Biosys species_name field found look for column name
        fields = [f for f in schema.fields if
                  f.name.lower() == SpeciesObservationSchema.SPECIES_NAME_FIELD_NAME.lower()]
        if len(fields) > 1:
            msg = "More than one 'Species Name' field found!. {}".format(fields)
            raise SpeciesObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if enforce_required and not field.required:
                msg = "The 'Species Name' field must be set as 'required'. {}".format(field)
                raise SpeciesObservationSchemaError(msg)
            else:
                return field
        msg = "The schema doesn't include a required 'Species Name' field. " \
              "It must have a field named {} or tagged with biosys type {}". \
            format(SpeciesObservationSchema.SPECIES_NAME_FIELD_NAME, BiosysSchema.SPECIES_NAME_TYPE_NAME)
        raise SpeciesObservationSchemaError(msg)

    @staticmethod
    def find_species_name_id_field(schema):
        """
        Precedence Rules:
        2- Look for biosys.type = 'speciesNameId'
        3- Look for a field with name 'NameId' or one the the possible names, case insensitive
        Note:
            the method will raise an SpeciesObservationSchemaError if two or more fields match either of the two rules.
        """

        result = None
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_species_name_id()]
        if len(fields) > 1:
            msg = "More than one Biosys {} type field found!. {}".format(BiosysSchema.SPECIES_NAME_ID_TYPE_NAME, fields)
            raise SpeciesObservationSchemaError(msg)
        if len(fields) == 1:
            result = fields[0]

        fields = [f for f in schema.fields if
                  f.name.lower() in SpeciesObservationSchema.SPECIES_NAME_ID_FIELD_NAMES_LOWER]
        if len(fields) > 1:
            msg = "More than one 'Species NameId' field found!. {}".format(fields)
            raise SpeciesObservationSchemaError(msg)
        if len(fields) == 1:
            result = fields[0]
        return result

    def cast_species_name(self, record):
        field = self.species_name_field
        return field.cast(record.get(field.name)) if field is not None else None

    def cast_species_name_id(self, record):
        field = self.species_name_id_field
        return field.cast(record.get(field.name)) if field is not None else None


class Exporter:
    def __init__(self, dataset, records=None):
        self.ds = dataset
        self.schema = GenericSchema(dataset.schema_data)
        self.headers = self.schema.headers
        self.warnings = []
        self.errors = []
        self.records = records if records else []

    def row_it(self, cast=True):
        for record in self.records:
            row = []
            for field in self.schema.fields:
                value = record.data.get(field.name, '')
                if cast:
                    # Cast to native python type
                    try:
                        value = field.cast(value)
                    except:
                        pass
                # TODO: remove that when running in Python3
                if isinstance(value, six.string_types) and not isinstance(value, six.text_type):
                    value = six.u(value)
                row.append(value)
            yield row

    def csv_it(self):
        yield self.headers
        for row in self.row_it(cast=False):
            yield row

    def _to_worksheet(self, ws):
        ws.title = self.ds.name
        # write headers
        headers = []
        for header in self.headers:
            cell = WriteOnlyCell(ws, value=header)
            cell.font = COLUMN_HEADER_FONT
            headers.append(cell)
        ws.append(headers)
        for row in self.row_it():
            ws.append(row)
        return ws

    def to_workbook(self):
        wb = Workbook(write_only=True)
        ws = wb.create_sheet()
        self._to_worksheet(ws)
        return wb


def infer_csv(csv_file, outfile, row_limit=0):
    with io.open(outfile, 'w') as fp:
        with io.open(csv_file) as stream:
            headers = stream.readline().rstrip('\n').split(',')
            values = jsontableschema.compat.csv_reader(stream)
            schema = jsontableschema.infer(headers, values, row_limit=row_limit)
            fp.write(six.u(json.dumps(schema, indent=2, ensure_ascii=False)))


def infer_csvs(path, row_limit=0):
    for filename in listdir(path):
        if filename.endswith('.csv'):
            infer_csv(join(path, filename), join(path, filename) + '.json', row_limit)
