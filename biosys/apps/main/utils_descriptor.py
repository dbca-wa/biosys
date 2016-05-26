from openpyxl import Workbook
from openpyxl.styles import Font

from upload.utils_openpyxl import write_values

COLUMN_HEADER_FONT = Font(bold=True)


def write_headers(descriptor, ws):
    schema = descriptor.schema
    headers = [field.get('name', 'No name') for field in schema.get('fields', [])]
    write_values(ws, 1, 1, headers, direction='right', font=COLUMN_HEADER_FONT)


def to_template_workbook(descriptor):
    wb = Workbook()
    ws = wb.active
    ws.title = descriptor.name
    write_headers(descriptor, wb.active)
    return wb
