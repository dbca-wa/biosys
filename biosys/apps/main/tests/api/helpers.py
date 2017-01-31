import copy
import csv
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from openpyxl import Workbook
from rest_framework.test import APIClient

from main.models import Project
from main.utils_auth import is_admin
from main.utils_species import SpeciesFacade

SOME_SPECIES_NAME_NAME_ID_MAP = {
    "Canis lupus subsp. familiaris": 30883,
    "Canis lupus": 25454,
    "Vespadelus douglasorum": 24204
}

REST_FRAMEWORK_TEST_SETTINGS = settings.REST_FRAMEWORK
REST_FRAMEWORK_TEST_SETTINGS['DEFAULT_AUTHENTICATION_CLASSES'] += [
    'rest_framework.authentication.SessionAuthentication',
]


def to_xlsx_file(rows):
    h, f = tempfile.mkstemp(suffix='.xlsx')
    wb = Workbook(write_only=True)
    ws = wb.create_sheet()
    for row in rows:
        ws.append(row)
    wb.save(f)
    return f


def to_csv_file(rows):
    h, f = tempfile.mkstemp(text=True, suffix='.csv')
    with open(f, 'wt') as csvfile:
        writer = csv.writer(csvfile)
        for row in rows:
            writer.writerow(row)
    return f


class BaseUserTestCase(TestCase):
    """
    A test case that provides some users and authenticated clients
    """
    fixtures = [
        'test-users',
        'test-projects'
    ]

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        password = 'password'
        user_model = get_user_model()
        self.admin_user = user_model.objects.filter(username="admin").first()
        self.assertIsNotNone(self.admin_user)
        self.assertTrue(is_admin(self.admin_user))
        self.admin_user.set_password(password)
        self.admin_user.save()
        self.admin_client = APIClient()
        self.assertTrue(self.admin_client.login(username=self.admin_user.username, password=password))

        self.custodian_1_user = user_model.objects.filter(username="custodian1").first()
        self.assertIsNotNone(self.custodian_1_user)
        self.custodian_1_user.set_password(password)
        self.custodian_1_user.save()
        self.custodian_1_client = APIClient()
        self.assertTrue(self.custodian_1_client.login(username=self.custodian_1_user.username, password=password))
        self.project_1 = Project.objects.filter(title="Project1").first()

        self.custodian_2_user = user_model.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(title="Project2").first()

        self.readonly_user = user_model.objects.filter(username="readonly").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.readonly_user.set_password(password)
        self.readonly_user.save()
        self.readonly_client = APIClient()
        self.assertTrue(self.readonly_client.login(username=self.readonly_user.username, password=password))

        self.anonymous_client = APIClient()

        if hasattr(self, '_more_setup') and callable(self._more_setup):
            self._more_setup()


class LightSpeciesFacade(SpeciesFacade):
    def name_id_by_species_name(self):
        """
        :return: a dict where key is species_name and the value is name_id
        """
        return SOME_SPECIES_NAME_NAME_ID_MAP

    def get_all_species(self, properties=None):
        """
        :param properties: a sequence of Property, e.g [PROPERTY_SPECIES_NAME, PROPERTY_NAME_ID] or None for all
        attributes
        :return: Return a list of species properties (see structure above) but with only the specified attributes.
        NOTE: limiting the number of properties speed-up the request.
        """
        return []


def set_site(record_data, dataset, site):
    """
    Update the 'Site' column value with the given site code
    :param record_data:
    :param dataset:
    :param site:
    :return:
    """
    schema = dataset.schema
    site_column = schema.get_fk_for_model('Site').data_field
    record_data[site_column] = site.code
    return record_data


def clone(dic):
    return copy.deepcopy(dic)


BASE_CONSTRAINTS = {
    "required": False
}

NOT_REQUIRED_CONSTRAINTS = {
    "required": False
}

REQUIRED_CONSTRAINTS = {
    "required": True
}

BASE_FIELD = {
    "name": "Name",
    "tile": "Title",
    "type": "string",
    "format": "default",
    "constraints": clone(BASE_CONSTRAINTS)
}

GENERIC_SCHEMA = {
    "fields": [
        clone(BASE_FIELD)
    ]
}

GENERIC_DATA_PACKAGE = {
    "name": "test",
    "resources": [
        {
            "name": "test",
            "format": "CSV",
            "title": "test",
            "bytes": 0,
            "mediatype": "text/csv",
            "path": "test.csv",
            "schema": clone(GENERIC_SCHEMA)
        }
    ],
    "title": "Test"
}

SPECIES_NAME_FIELD = {
    "name": "Species Name",
    "type": "string",
    "format": "default",
    "constraints": {
        "required": True
    },
    "biosys": {
        "type": "speciesName"
    }
}

LAT_LONG_OBSERVATION_SCHEMA = {
    "fields": [
        {
            "name": "Observation Date",
            "type": "date",
            "format": "any",
            "constraints": {
                "required": True,
            }
        },
        {
            "name": "Latitude",
            "type": "number",
            "format": "default",
            "constraints": {
                "required": True,
                "minimum": -90.0,
                "maximum": 90.0,
            }
        },
        {
            "name": "Longitude",
            "type": "number",
            "format": "default",
            "constraints": {
                "required": True,
                "minimum": -180.0,
                "maximum": 180.0,
            }
        },
    ]
}

SPECIES_SCHEMA = clone(LAT_LONG_OBSERVATION_SCHEMA)
SPECIES_SCHEMA['fields'].append(clone(SPECIES_NAME_FIELD))

SPECIES_DATA_PACKAGE = clone(GENERIC_DATA_PACKAGE)
SPECIES_DATA_PACKAGE['resources'][0]['schema'] = clone(SPECIES_SCHEMA)


def create_data_package_from_fields(fields):
    result = clone(GENERIC_DATA_PACKAGE)
    result['resources'][0]['schema']['fields'] = fields
    return result
