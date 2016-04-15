"""
Usage with django-extensions runscript command: ./manage.py runscript legacy.LCI.import_legacy_data
"""

from __future__ import unicode_literals, print_function

import logging
import re

from openpyxl import load_workbook

from main.models import *
from vegetation.models import *
from main.utils import get_field
from upload.utils_openpyxl import TableData
from upload.validation import to_integer_raise, to_float_raise, to_model_choice, \
    to_lookup_raise, to_string, to_date_raise

logger = logging.getLogger('import_lci')

# DATA_FILE = 'LCI_NC_MonSiteData_15Jan2016.xlsx'
DATA_FILE = 'working.xlsx'


def build_model_arguments(row_data, mapping):
    """
    mapping = {
        'Project': {
            'field': 'project',
            'map': lambda x: str(x),
            'reference': True,
        },
        'Parent Site': {
            'field': 'parent_site',
            'map': None
        },
    :param row_data:
    :param mapping:
    :return:
    """
    kwargs = {}
    defaults = {}
    errors = []
    for col_name, map_desc in mapping.iteritems():
        col_value = row_data.get(col_name, None)
        field = map_desc.get('field', None)
        if field:
            try:
                map_func = map_desc.get('map', None)
                field_value = map_func(col_value, row_data) if callable(map_func) else col_value
                if map_desc.get('reference', False):
                    kwargs[field] = field_value
                else:
                    defaults[field] = field_value
            except Exception as e:
                msg = "Col: '{}' Value '{}': {}".format(col_name, col_value, e)
                # logger.warning(msg)
                errors.append(msg)
    return kwargs, defaults, errors


def get_or_create_project(row_data):
    mapping = {
        'Project': {
            'field': 'title',
            'reference': True,
        },
        'Datum': {
            'field': 'datum',
            'map': lambda x, r: to_model_choice(DATUM_CHOICES, x) if x else None
        }
    }
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    return Project.objects.update_or_create(defaults=defaults, **kwargs)


def only_digit(x):
    return re.sub('\D', '', str(x))


def get_or_create_site(project, row_data):
    mapping = {
        'Project': {
            'field': 'project',
            'map': lambda x, r: project,
        },
        'Parent Site': {
            'field': 'parent_site',
            'map': lambda x, r: Site.objects.get_or_create(project=project, site_code=x)[0]
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
        'Datum': {
            'field': 'datum',
            'map': lambda x, r: to_model_choice(DATUM_CHOICES, x) if x else None
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
            'map': lambda v, r: only_digit(v)
        },
        'Collector': {
            'field': 'established_by',
            'map': lambda v, r: to_string(v)
        },
        'Bearing (degree)': {
            'field': 'bearing',
            'map': lambda v, r: to_float_raise(v)
        },
        'Width': {
            'field': 'width',
            'map': lambda v, r: only_digit(v)
        },
        'Hight': {
            'field': 'height',
            'map': lambda v, r: only_digit(v)
        },
        'Aspect': {
            'field': 'aspect',
            'map': lambda x, r: to_model_choice(Site.ASPECT_CHOICES, x) if x else None
        },
        'Slope (degree)': {
            'field': 'slope',
            'map': lambda x, r: to_integer_raise(only_digit(x), None)
        },
        'Altitude': {
            'field': 'altitude',
            'map': lambda x, r: to_float_raise(only_digit(x), None)
        },
        'Location': {
            'field': 'location',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'location'), x)
        },
        'Geology Group': {
            'field': 'geology_group',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'geology_group'), x)
        },
        'Vegetation Group': {
            'field': 'vegetation_group',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'vegetation_group'), x)
        },
        'Tenure': {
            'field': 'tenure',
            'map': lambda v, r: to_string(v)
        },
        'Underlaying geology ': {
            'field': 'underlaying_geology',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'underlaying_geology'), x)
        },
        'Distance to closest water (m)': {
            'field': 'closest_water_distance',
            'map': lambda x, r: to_integer_raise(only_digit(x), None)
        },
        'Type of closest water': {
            'field': 'closest_water_type',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'closest_water_type'), x)
        },
        'Landform pattern (300m radius)': {
            'field': 'landform_pattern',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'landform_pattern'), x)
        },
        'Landform element (20m radius)': {
            'field': 'landform_element',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'landform_element'), x)
        },
        'Soil surface texture': {
            'field': 'soil_surface_texture',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'soil_surface_texture'), x)
        },
        'Soil colour': {
            'field': 'soil_colour',
            'map': lambda v, r: to_string(v)
        },
        'Photos taken': {
            'field': 'photos_taken',
            'map': lambda v, r: to_string(v)
        },
        'Historical Information': {
            'field': 'historical_info',
            'map': lambda v, r: to_string(v)
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    site, created = Site.objects.update_or_create(defaults=defaults, **kwargs)
    return site, created, errors


def load_sites(ws):
    table_reader = TableData(ws)
    row_count = 2
    for row in list(table_reader.rows_as_dict_it()):
        try:
            project, created = get_or_create_project(row)
            if created:
                logger.info("New project: {}".format(project))
            site, created, errors = get_or_create_site(project, row)
            if errors:
                logger.warning('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.exception('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def get_or_create_visit(project, site, row_data):
    mapping = {
        'Project': {
            'field': 'project',
            'map': lambda x, r: project,
        },
        'Visit Name': {
            'field': 'name',
            'map': lambda v, r: to_string(v),
            'reference': True,
        },
        'Start Date': {
            'field': 'start_date',
            'map': lambda v, r: to_date_raise(v),
        },
        'End Date': {
            'field': 'end_date',
            'map': lambda v, r: to_date_raise(v),
        },
        'Trap Nights': {
            'field': 'trap_nights',
            'map': lambda v, r: to_integer_raise(only_digit(v)),
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    visit, created = Visit.objects.update_or_create(defaults=defaults, **kwargs)
    # add the site to this visit
    visit.sites.add(site)
    visit.save()
    return site, created, errors


def load_visits(ws):
    table_reader = TableData(ws)
    row_count = 2
    for row_data in list(table_reader.rows_as_dict_it()):
        try:
            project_title = row_data.get('Project', None)
            project = Project.objects.get(title=project_title)
            site_code = row_data.get('Sites', None)
            site = Site.objects.get(site_code=site_code)
            get_or_create_visit(project, site, row_data)
        except Exception as e:
            logger.exception('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def get_or_create_site_visit(row_data):
    model = SiteVisit
    mapping = {
        'Visit Name': {
            'field': 'visit',
            'map': lambda v, r: Visit.objects.get(name=v),
            'reference': True,
        },
        'Site Code': {
            'field': 'site',
            'map': lambda v, r: Site.objects.get(site_code=v),
            'reference': True,
        },
    }
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    obj, created = model.objects.update_or_create(defaults=defaults, **kwargs)
    return obj, created, errors


def get_or_create_site_characteristic(row_data):
    model = SiteCharacteristic
    mapping = {
        'Visit Name': {
            'field': 'site_visit',
            'map': lambda v, r: get_or_create_site_visit(r)[0],
            'reference': True,
        },
        'Underlaying geology ': {
            'field': 'underlaying_geology',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'underlaying_geology'), x)
        },
        'Distance to closest water (m)': {
            'field': 'closest_water_distance',
            'map': lambda x, r: to_integer_raise(only_digit(x), None)
        },
        'Type of closest water': {
            'field': 'closest_water_type',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'closest_water_type'), x)
        },
        'Landform pattern (300m radius)': {
            'field': 'landform_pattern',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'landform_pattern'), x)
        },
        'Landform element (20m radius)': {
            'field': 'landform_element',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'landform_element'), x)
        },
        'Soil surface texture': {
            'field': 'soil_surface_texture',
            'map': lambda x, r: to_lookup_raise(get_field(Site, 'soil_surface_texture'), x)
        },
        'Soil colour': {
            'field': 'soil_colour',
            'map': lambda v, r: to_string(v)
        },
        'Comments': {
            'field': 'comments',
            'map': lambda v, r: to_string(v)
        },
    }
    kwargs, defaults, errors = build_model_arguments(row_data, mapping)
    obj, created = model.objects.update_or_create(defaults=defaults, **kwargs)
    return obj, created, errors


def load_site_characteristics(ws):
    table_reader = TableData(ws)
    row_count = 2
    for row_data in list(table_reader.rows_as_dict_it()):
        try:
            # get site visit
            obj, created, errors = get_or_create_site_characteristic(row_data)
            if errors:
                logger.warning('{} Row# {}: {}'.format(ws.title, row_count, "\n\t".join(errors)))
        except Exception as e:
            logger.exception('{} Row# {}: {}'.format(ws.title, row_count, e))
        finally:
            row_count += 1


def load_data(file_path=None):
    if not file_path:
        file_path = path.join(path.dirname(__file__), 'data', DATA_FILE)
    logger.info('Load workbook {}'.format(file_path))
    wb = load_workbook(file_path)
    logger.info('Load workbook done')

    # logger.info('Parse Sites worksheet')
    # # Sites datasheet
    # load_sites(wb.get_sheet_by_name('Sites'))

    # logger.info('Parse Visit worksheet')
    # # Sites datasheet
    # load_visits(wb.get_sheet_by_name('Visit'))

    logger.info('Parse Site Characteristics')
    # Sites datasheet
    load_site_characteristics(wb.get_sheet_by_name('Site Characteristics'))

    logger.info('Import Done')


def run():
    """
    The method called by django-extension runscript
    """
    load_data()
