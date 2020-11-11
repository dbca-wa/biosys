import io

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.cell import WriteOnlyCell

from main.utils_data_package import GenericSchema

COLUMN_HEADER_FONT = Font(bold=True)


class DefaultExporter:
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
                    except Exception:
                        pass

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

    def to_csv(self, output):
        import csv

        output = output or io.StringIO()
        writer = csv.writer(output, dialect='excel')
        for row in self.csv_it():
            writer.writerow(row)


class BionetExporter(DefaultExporter):
    """
    Same as default but spit two blank lines at the top when using csv
    """
    def to_csv(self, output):
        import csv

        output = output or io.StringIO()
        writer = csv.writer(output, dialect='excel')
        writer.writerow(['Bionet Ignored Line'])
        writer.writerow(['Bionet Ignored Line'])
        for row in self.csv_it():
            writer.writerow(row)
