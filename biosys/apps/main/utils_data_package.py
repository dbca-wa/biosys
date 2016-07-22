import io
import json
from os import listdir
from os.path import join

import jsontableschema
from jsontableschema.model import SchemaModel, types
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.writer.write_only import WriteOnlyCell
from django.utils.encoding import python_2_unicode_compatible

from upload.utils_openpyxl import is_blank_value

COLUMN_HEADER_FONT = Font(bold=True)


@python_2_unicode_compatible
class SchemaField:
    """
    Utility class for a field in a schema.
    It uses the schema types of
    https://github.com/frictionlessdata/jsontableschema-py#types
    for validation.
    """

    def __init__(self, data):
        self.data = data
        self.name = data['name']  # We want to throw an exception if there is no name
        # use of jsontableschema.types to help constraint validation
        self.type = SchemaModel._type_map()[data.get('type')](data)

    @property
    def column_name(self):
        return self.name

    @property
    def constraints(self):
        return self.data.get('constraints', {})

    @property
    def required(self):
        return self.constraints.get('required', False)

    @property
    def aliases(self):
        return self.data['aliases'] if 'aliases' in self.data else []

    def has_alias(self, name, icase=False):
        for alias in self.aliases:
            if alias == name or (icase and alias.lower() == name.lower()):
                return True
        return False

    def has_name_or_alias(self, name, icase=False):
        has_name = self.name == name or (icase and self.name.lower() == name.lower())
        return has_name or self.has_alias(name, icase=icase)

    def cast(self, value):
        """
        Returns o native Python object of the expected format. Will throw an exception
        if the value doesn't complies with any constraints. See for details:
        https://github.com/frictionlessdata/jsontableschema-py#types
        This method is mainly a helper for the validation_error
        :param value:
        :return:
        """
        if is_blank_value(value):
            # must do that because an empty string is considered as valid even if required by the StringType
            value = None
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


@python_2_unicode_compatible
class SchemaForeignKey:
    """
    A utility class for foreign key in schema
    """

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return 'Foreign Key {}'.format(self.data)

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


class Schema:
    """
    A utility class for schema.
    It uses internally an instance SchemaModel of the frictionless jsontableschema for help.
    https://github.com/frictionlessdata/jsontableschema-py#model
    """

    def __init__(self, schema):
        self.data = schema
        self.schema_model = SchemaModel(schema)
        self.fields = [SchemaField(f) for f in self.schema_model.fields]
        self.foreign_keys = [SchemaForeignKey(fk) for fk in
                             self.schema_model.foreignKeys] if self.schema_model.foreignKeys else []

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
        The row must be a dictionary or a list of key value
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


class ObservationSchema(Schema):
    """
    A schema specific to an Observation Dataset.
    It's main job is to deal with the observation date and it's geometry
    (lat/long or geojson)
    """

    def _get_observation_date_field_or_throw(self):
        """
        Rules:
        1- If there's only one field of type date it's this one.
        2- More than one date field, look for name or alisases 'Observation Date'
        3- Throw exception if not found
        :return: the SchemaField
        """
        date_fields = [field for field in self.fields
                       if isinstance(field.type, types.DateType) or isinstance(field.type, types.DateTimeType)]
        dates_count = len(date_fields)
        if dates_count == 0:
            msg = 'One field must be of type date to be a valid Observation schema.'
            raise Exception(msg)
        if dates_count == 1:
            return date_fields[0]
        else:
            # more than one date. Look for the Observation Date field
            lname = 'Observation Date'.lower()
            observation_dates = [field for field in date_fields
                                 if field.has_name_or_alias(lname, icase=True)]
            count = len(observation_dates)
            if count == 0:
                msg = "The schema contains more than one date. One must be named or alias as 'Observation Date'."
                raise Exception(msg)
            if count > 1:
                msg = "The schema contains more than one 'Observation Date' field (as name or alias)."
                raise Exception(msg)
            return observation_dates[0]


    def _valid_geometry_or_throw(self):
        """
        Rules:
        1 - look for type geojson. If one only use it
        2 - look for type geopoint. If one only use it
        3 - look for latitude/longitude
        :return:
        """
        geometry_fields = [field for field in self.fields
                           if isinstance(field.type, types.GeoJSONType) or isinstance(field.type, types.GeoPointType)]
        # TODO: implement latitude/longitude
        return False


class SpeciesObservation(ObservationSchema):
    """
    An ObservationSchema with a Species Name
    """

    SPECIES_NAME_FIELD = 'Species Name'

    def _get_species_name_field_or_throw(self):
        """
        Rules:
        One and only string field with a name or alias 'Species Name' (case insensitive)
        :return: the field or throw an exception
        """
        species_fields = [field for field in self.fields if field.has_name_or_alias(self.SPECIES_NAME_FIELD)]
        count = len(species_fields)
        if count == 0:
            msg = "No 'Species Name' field found. One field must have a name or alias '{}' ".format(
                self.SPECIES_NAME_FIELD)
            raise Exception(msg)
        if count > 1:
            msg = "More than one '{}' field found (in name or aliases).".format(self.SPECIES_NAME_FIELD)
            raise Exception(msg)
        return species_fields[0]


class Exporter:
    def __init__(self, dataset, records=None):
        self.ds = dataset
        self.schema = Schema(dataset.schema)
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


def infer_csv(csvfile, outfile, row_limit = 0):
    with io.open(outfile, 'w') as fp:
        with io.open(csvfile) as stream:
            headers = stream.readline().rstrip('\n').split(',')
            values = jsontableschema.compat.csv_reader(stream)
            schema = jsontableschema.infer(headers, values, row_limit=row_limit)
            fp.write(unicode(json.dumps(schema, indent=2, ensure_ascii=False)))


def infer_csvs(path, row_limit = 0):
    for filename in listdir(path):
	if filename.endswith( 'csv' ):
	    infer_csv(join(path, filename), join(path, filename) + '.json', row_limit)



