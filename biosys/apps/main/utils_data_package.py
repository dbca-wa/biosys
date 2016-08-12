from __future__ import print_function

import io
import json
from os import listdir
from os.path import join

import jsontableschema
from dateutil.parser import parse as date_parse
from django.utils.encoding import python_2_unicode_compatible
from future.utils import raise_with_traceback
from jsontableschema.exceptions import InvalidDateType
from jsontableschema.model import SchemaModel, types
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.writer.write_only import WriteOnlyCell

from django.contrib.gis.geos import Point

from main.constants import MODEL_SRID, DATUM_CHOICES

COLUMN_HEADER_FONT = Font(bold=True)


class ObservationSchemaError(Exception):
    # don't  extend InvalidSchemaError (problem with message not showing in the str method)
    pass


class SpeciesSchemaError(Exception):
    pass


class GeometrySchemaError(Exception):
    pass


class InvalidDatumError(Exception):
    pass


class FieldSchemaError(Exception):
    pass


class DayFirstDateType(types.DateType):
    """
    Extend the jsontableschema DateType which use the mm/dd/yyyy date model for the 'any' format
    to use dd/mm/yyyy
    """

    def cast_any(self, value, fmt=None):
        if isinstance(value, self.python_type):
            return value
        try:
            return date_parse(value, dayfirst=True).date()
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
            return date_parse(value, dayfirst=True).date()
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
        # TODO: delete in python3
        if isinstance(value, basestring):
            # the StringType accepts only unicode
            value = unicode(value)
        return self.type.cast(value)

    def validation_error(self, value):
        """
        Try to cast and catch the exception if any
        :param value:
        :return: None if value is valid or an error message string
        """
        error = None
        try:
            self.cast(value)
        except Exception as e:
            error = e.message
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
        elif isinstance(value, basestring):
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
class GenericSchema:
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

    def __str__(self):
        return self.get('name')


class ObservationSchema(GenericSchema):
    """
    A schema specific to an Observation Dataset.
    It's main job is to deal with the observation date and it's geometry
    (lat/long or geojson)
    """
    OBSERVATION_DATE_FIELD_NAME = 'Observation Date'
    LATITUDE_FIELD_NAME = 'Latitude'
    LONGITUDE_FIELD_NAME = 'Longitude'
    DATUM_FIELD_NAME = 'Datum'

    def __init__(self, schema):
        GenericSchema.__init__(self, schema)
        self.observation_date_field = self.find_observation_date_field_or_throw(self)
        self.latitude_field = self.find_latitude_field_or_throw(self)
        self.longitude_field = self.find_longitude_field_or_throw(self)
        self.datum_field = self.find_datum_field_or_none(self)

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
        :return: the SchemaField
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
                  "It must have a field named {} or with biosys type {}". \
                format(ObservationSchema.OBSERVATION_DATE_FIELD_NAME, BiosysSchema.OBSERVATION_DATE_TYPE_NAME)
            raise ObservationSchemaError(msg)

    @staticmethod
    def find_latitude_field_or_throw(schema):
        """
        Precedence Rules:
        2- Look for biosys.type = 'latitude'
        3- Look for a field with name 'Latitude' case insensitive
        :param schema: a dict descriptor or a Schema instance
        :return: None if not found or raise an exception if more than one
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_latitude()]
        if len(fields) > 1:
            msg = "More than one Biosys latitude field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if not field.required:
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
            if not field.required:
                msg = "The Latitude field must be set as 'required'. {}".format(field)
                raise ObservationSchemaError(msg)
            else:
                return field
        msg = "The schema doesn't include a required latitude field. " \
              "It must have a field named {} or with biosys type {}". \
            format(ObservationSchema.LATITUDE_FIELD_NAME, BiosysSchema.LATITUDE_TYPE_NAME)
        raise ObservationSchemaError(msg)

    @staticmethod
    def find_longitude_field_or_throw(schema):
        """
        Precedence Rules:
        1- Look for biosys.type = 'longitude'
        2- Look for a field with name 'Longitude' case insensitive
        :param schema: a dict descriptor or a Schema instance
        :return: None if not found or raise an exception if more than one
        """
        if not isinstance(schema, GenericSchema):
            schema = GenericSchema(schema)
        fields = [f for f in schema.fields if f.biosys.is_longitude()]
        if len(fields) > 1:
            msg = "More than one Biosys longitude field found!. {}".format(fields)
            raise ObservationSchemaError(msg)
        if len(fields) == 1:
            field = fields[0]
            if not field.required:
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
            if not field.required:
                msg = "The Longitude field must be set as 'required'. {}".format(field)
                raise ObservationSchemaError(msg)
            else:
                return field
        msg = "The schema doesn't include a required longitude field. " \
              "It must have a field named {} or with biosys type {}". \
            format(ObservationSchema.LONGITUDE_FIELD_NAME, BiosysSchema.LONGITUDE_TYPE_NAME)
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

    def get_record_observation_date_value(self, record):
        return record.get(self.observation_date_field.name)

    def cast_record_observation_date(self, record):
        field = self.observation_date_field
        return field.cast(record.get(field.name))

    def cast_geometry(self, record, default_srid=MODEL_SRID):
        lat_val = record.get(self.latitude_field.name)
        lon_val = record.get(self.longitude_field.name)
        lat = self.latitude_field.cast(lat_val)
        lon = self.longitude_field.cast(lon_val)
        srid = default_srid
        if self.datum_field is not None:
            datum_val = record.get(self.datum_field.name)
            valid_datums = dict(DATUM_CHOICES).values()
            if datum_val:
                if datum_val.upper() not in valid_datums:
                    msg = "Invalid Datum '{}'. Should be one of: {}".format(datum_val, valid_datums)
                    raise InvalidDatumError(msg)
                else:
                    srid = dict(DATUM_CHOICES).get(datum_val, default_srid)
        return Point(x=float(lon), y=float(lat), srid=srid)


class SpeciesObservationSchema(ObservationSchema):
    """
    An ObservationSchema with a Species Name
    """
    # TODO: implement the species stuff
    pass


class Exporter:
    def __init__(self, dataset, records=None):
        self.ds = dataset
        self.schema = GenericSchema(dataset.schema)
        self.headers = self.schema.headers
        self.warnings = []
        self.errors = []
        self.records = records if records else []

    def row_it(self):
        for record in self.records:
            row = []
            for field in self.schema.field_names:
                row.append(unicode(record.data.get(field, '')))
            yield row

    def to_csv(self):
        rows = list()
        rows.append(self.headers)
        rows += list(self.row_it())
        return rows

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
        # TODO: implement version in write_only mode.
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
            fp.write(unicode(json.dumps(schema, indent=2, ensure_ascii=False)))


def infer_csvs(path, row_limit=0):
    for filename in listdir(path):
        if filename.endswith('.csv'):
            infer_csv(join(path, filename), join(path, filename) + '.json', row_limit)
