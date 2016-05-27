import csv
from openpyxl import Workbook
from openpyxl.styles import Font
from slugify import Slugify
from jsontableschema.model import SchemaModel

from django.utils.encoding import python_2_unicode_compatible
from upload.utils_openpyxl import write_values

COLUMN_HEADER_FONT = Font(bold=True)

FIELD_SLUGIFY = Slugify(to_lower=True)


def write_headers(dataset, ws):
    schema = dataset.schema
    headers = [field.get('name', 'No name') for field in schema.get('fields', [])]
    write_values(ws, 1, 1, headers, direction='right', font=COLUMN_HEADER_FONT)


def to_template_workbook(dataset):
    wb = Workbook()
    ws = wb.active
    ws.title = dataset.name
    write_headers(dataset, wb.active)
    return wb


@python_2_unicode_compatible
class SchemaField:
    def __init__(self, data):
        self.data = data
        self.name = data['name']  # We want to throw an exception if there is no name
        self.biosys = data.get('biosys', {})

    @property
    def column_name(self):
        return self.name

    def slugify(self):
        return FIELD_SLUGIFY(self.name)

    def __str__(self):
        return '{}'.format(self.name)


class Schema:
    """
    A class derived from the SchemaModel of the frictionless jsontableschema
    https://github.com/frictionlessdata/jsontableschema-py#model
    """

    def __init__(self, dataset):
        self.schema_model = SchemaModel(dataset.schema)

    @property
    def headers(self):
        return self.schema_model.headers

    @property
    def fields(self):
        return list(self.fields_it())

    def fields_it(self):
        for f in self.schema_model.fields:
            yield SchemaField(f)

    def get_species_field(self):
        pass

    def get_latitude_field(self):
        pass

    def get_longitude_field(self):
        pass


class Exporter:
    def __init__(self, dataset, records=None):
        self.ds = dataset
        self.schema = Schema(dataset)
        self.headers = self.schema.headers
        self.warnings = []
        self.errors = []
        self.records = records if records else []

    def to_csv(self):
        pass

    def to_worksheet(self, ws):
        pass

    def to_workbook(self):
        pass

    # def _row_it(self):
    #     for record in self.records:
    #         pass

    def _to_row(self, record):
        for field in self.schema.fields:
            pass
