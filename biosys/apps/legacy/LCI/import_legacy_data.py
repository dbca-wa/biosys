"""
Usage with django-extensions runscript command: ./manage.py runscript legacy.LCI.import_legacy_data
"""

from __future__ import unicode_literals, print_function

import logging
import re

from openpyxl import load_workbook

from main.models import *
from main.utils import get_field
from upload.utils_openpyxl import TableData
from upload.validation import to_integer_raise, to_float_raise, to_model_choice, to_lookup_raise

logger = logging.getLogger('import_lci')

# DATA_FILE = 'LCI_NC_MonSiteData_15Jan2016.xlsx'
DATA_FILE = 'working.xlsx'


def get_or_create_project(row):
    mapping = {
        'title': 'Project',
        'code': 'Project',
        'datum': 'Datum'
    }
    project, created = Project.objects.update_or_create(
        title=row['Project'],
        defaults={
            'code': row['Project'],
            'datum': [datum[0] for datum in DATUM_CHOICES if datum[1].lower() == row['Datum'].lower()][0],
            'custodian': None
        }
    )
    return project, created


def only_digit(x):
    return re.sub('\D', '', str(x))


def get_or_create_site(project, row_data):
    mapping = {
        'Project': {
            'field': 'project',
            'map': lambda x: project,
        },
        'Parent Site': {
            'field': 'parent_site',
            'map': lambda x: Site.objects.get_or_create(project=project, site_code=x)[0]
        },
        'Site Code': {
            'field': 'site_code',
            'reference': True,
            'map': None

        },
        'Site Name': {
            'field': 'site_name',
            'map': None
        },
        'Date established': {
            'field': 'date_established'
        },
        'Latitude': {
            'field': 'latitude'
        },
        'Longitude': {
            'field': 'longitude'
        },
        'Accuracy': {
            'field': 'accuracy',
            # turn '50m' into 50.0
            'map': only_digit
        },
        'Collector': {
            'field': 'established_by'
        },
        'Bearing (degree)': {
            'field': 'bearing',
            'map': to_float_raise
        },
        'Width': {
            'field': 'width',
            'map': only_digit
        },
        'Hight': {
            'field': 'height',
            'map': only_digit
        },
        'Aspect': {
            'field': 'aspect',
            'map': lambda x: to_model_choice(Site.ASPECT_CHOICES, x) if x else None
        },
        'Slope (degree)': {
            'field': 'slope',
            'map': lambda x: to_integer_raise(only_digit(x), None)
        },
        'Altitude': {
            'field': 'altitude',
            'map': lambda x: to_float_raise(only_digit(x), None)
        },
        'Location': {
            'field': 'location',
            'map': lambda x: to_lookup_raise(get_field(Site, 'location'), x)
        },
    }

    kwargs = {}
    defaults = {}
    for col_name, data in mapping.iteritems():
        legacy_value = row_data[col_name]
        field = data.get('field', None)
        if field:
            map_func = data.get('map', None)
            field_value = map_func(legacy_value) if callable(map_func) else legacy_value
            if data.get('reference', False):
                kwargs[field] = field_value
            else:
                defaults[field] = field_value
    logger.debug('update_or_create Site: kwargs {} defaults {}'.format(kwargs, defaults))
    return Site.objects.update_or_create(defaults=defaults, **kwargs)


def load_sites(ws):
    table_reader = TableData(ws)
    row_count = 2
    for row in table_reader.rows_as_dict_it():
        try:
            project, created = get_or_create_project(row)
            if created:
                logger.info("New project: {}".format(project))
            site, created = get_or_create_site(project, row)
            if created:
                logger.info("New Site: {}".format(site))
        except Exception as e:
            logger.warning('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def import_data(file_path=None):
    if not file_path:
        file_path = path.join(path.dirname(__file__), 'data', DATA_FILE)
    logger.info('Load workbook {}'.format(file_path))
    wb = load_workbook(file_path)
    logger.info('Load workbook done')
    logger.info('Parse Sites worksheet')
    # Sites datasheet
    load_sites(wb.get_sheet_by_name('Sites'))

    logger.info('Import Done')


def run():
    """
    The method called by django-extension runscript
    """
    import_data()
