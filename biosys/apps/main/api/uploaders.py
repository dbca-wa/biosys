import codecs
import csv

from django.utils import six
from openpyxl import load_workbook

from main.api.utils_geom import PointParser
from main.models import Site
from main.utils_misc import get_value


class SiteUploader:
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
    COLUMN_MAP = {
        'code': ['code', 'site code'],
        'name': ['name', 'site name'],
        'comments': ['comments'],
        'parent_site': ['parent site', 'parent']
    }

    def __init__(self, file, project):
        if file.content_type not in self.SUPPORTED_TYPES:
            msg = "Wrong file type {}. Should be one of: {}".format(file.content_type, self.SUPPORTED_TYPES)
            raise Exception(msg)

        self.file = file
        if file.content_type in self.XLSX_TYPES:
            self.file = self._to_csv(file)
            self.reader = csv.DictReader(self.file)
        else:
            self.reader = csv.DictReader(codecs.iterdecode(self.file, 'utf-8'))
        self.project = project

    def __iter__(self):
        for row in self.reader:
            yield self._create_or_update_site(row)

    def close(self):
        self.file.close()

    def _create_or_update_site(self, row):
        # we need the code at minimum
        site, error = (None, None)
        code = get_value(self.COLUMN_MAP.get('code'), row)
        if not code:
            error = "Site Code is missing"
        else:
            kwargs = {
                'name': get_value(self.COLUMN_MAP.get('name'), row, ''),
                'comments': get_value(self.COLUMN_MAP.get('comments'), row, ''),
                'attributes': self._get_attributes(row)
            }
            # geometry
            try:
                geo_parser = PointParser(row, self.project.datum)
                kwargs['geometry'] = geo_parser.to_geom()
            except:
                # not an error (warning?)
                pass
            # parent site
            parent_site_code = get_value(self.COLUMN_MAP.get('parent_site'), row)
            if parent_site_code:
                kwargs['parent_site'] = self._get_or_create_parent_site(parent_site_code)
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

    @staticmethod
    def _get_or_create_parent_site(parent_code):
        site, _ = Site.objects.get_or_create(code=parent_code)
        return site

    def _to_csv(self, file):
        output = six.StringIO()
        writer = csv.writer(output)
        wb = load_workbook(filename=file, read_only=True)
        ws = wb.active
        for row in ws.rows:
            r = [cell.value for cell in row]
            writer.writerow(r)
        # rewind
        output.seek(0)
        return output
