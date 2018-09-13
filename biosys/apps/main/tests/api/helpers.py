import copy
import csv
import tempfile

from django.conf import settings
from django.shortcuts import reverse
from django.test import TestCase, override_settings
from openpyxl import Workbook
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Dataset, Record
from main.tests import factories
from main.utils_auth import is_admin
from main.utils_species import SpeciesFacade

SOME_SPECIES_NAME_NAME_ID_MAP = {
    "Canis lupus subsp. familiaris": 30883,
    "Canis lupus": 25454,
    "Vespadelus douglasorum": 24204
}

REST_FRAMEWORK_TEST_SETTINGS = settings.REST_FRAMEWORK
if 'rest_framework.authentication.SessionAuthentication' \
        not in REST_FRAMEWORK_TEST_SETTINGS['DEFAULT_AUTHENTICATION_CLASSES']:
    REST_FRAMEWORK_TEST_SETTINGS['DEFAULT_AUTHENTICATION_CLASSES'] \
        .append('rest_framework.authentication.SessionAuthentication')


def rows_to_workbook(rows, sheet_title=None):
    wb = Workbook(write_only=True)
    ws = wb.create_sheet(title=sheet_title)
    for row in rows:
        ws.append(row)
    return wb


def workbook_to_xlsx_file(wb):
    h, f = tempfile.mkstemp(suffix='.xlsx')
    wb.save(f)
    return f


def rows_to_xlsx_file(rows):
    return workbook_to_xlsx_file(rows_to_workbook(rows))


def rows_to_csv_file(rows):
    h, f = tempfile.mkstemp(text=True, suffix='.csv')
    with open(f, 'wt') as csvfile:
        writer = csv.writer(csvfile)
        for row in rows:
            writer.writerow(row)
    return f


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


@override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                   REST_FRAMEWORK_TEST_SETTINGS=REST_FRAMEWORK_TEST_SETTINGS)
class BaseUserTestCase(TestCase):
    """
    A test case that provides some users and authenticated clients.
    This class also set the species facade to be the test one (not real herbie).
    Also provide some high level API utility function
    """
    species_facade_class = LightSpeciesFacade

    @staticmethod
    def observation_schema_with_with_all_possible_geometry_fields():
        schema_fields = [
            {
                "name": "What",
                "type": "string",
                "constraints": NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "When",
                "type": "date",
                "constraints": REQUIRED_CONSTRAINTS,
                "format": "any",
                "biosys": {
                    'type': 'observationDate'
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'latitude'
                }
            },
            {
                "name": "Longitude",
                "type": "number",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'longitude'
                }
            },
            {
                "name": "Site Code",
                "type": "string",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": "siteCode"
                }
            },
            {
                "name": "Easting",
                "type": "number",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'easting'
                }
            },
            {
                "name": "Northing",
                "type": "number",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'northing'
                }
            },
            {
                "name": "Datum",
                "type": "string",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'datum'
                }
            },
            {
                "name": "Zone",
                "type": "integer",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'zone'
                }
            },
        ]
        schema = create_schema_from_fields(schema_fields)
        # add Site Code foreign key
        schema = add_model_field_foreign_key_to_schema(schema, {
            'schema_field': 'Site Code',
            'model': 'Site',
            'model_field': 'code'
        })
        return schema

    def setUp(self):
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class

        password = 'password'
        self.admin_user = factories.UserFactory.create(username='admin', is_superuser=True)
        self.assertTrue(is_admin(self.admin_user))
        self.admin_user.set_password(password)
        self.admin_user.save()
        self.admin_client = APIClient()
        self.assertTrue(self.admin_client.login(username=self.admin_user.username, password=password))

        self.program_1 = factories.ProgramFactory.create(name='program_1')
        self.program_2 = factories.ProgramFactory.create(name='program_2')

        self.data_engineer_1_user = factories.UserFactory.create(username='data_engineer_1')
        self.data_engineer_1_user.set_password(password)
        self.data_engineer_1_user.save()
        self.program_1.data_engineers.add(self.data_engineer_1_user)
        self.data_engineer_1_client = APIClient()
        self.assertTrue(self.data_engineer_1_client.login(username=self.data_engineer_1_user.username, password=password))

        self.data_engineer_2_user = factories.UserFactory.create(username='data_engineer_2')
        self.data_engineer_2_user.set_password(password)
        self.data_engineer_2_user.save()
        self.program_2.data_engineers.add(self.data_engineer_2_user)
        self.data_engineer_2_client = APIClient()
        self.assertTrue(self.data_engineer_2_client.login(username=self.data_engineer_2_user.username, password=password))

        self.project_1 = factories.ProjectFactory.create(name="Project_1", program=self.program_1)
        self.custodian_1_user = factories.UserFactory.create(username="custodian_1")
        self.project_1.custodians.add(self.custodian_1_user)
        self.custodian_1_user.set_password(password)
        self.custodian_1_user.save()
        self.custodian_1_client = APIClient()
        self.assertTrue(self.custodian_1_client.login(username=self.custodian_1_user.username, password=password))

        self.project_2 = factories.ProjectFactory.create(name="Project_2", program=self.program_2)
        self.custodian_2_user = factories.UserFactory.create(username="custodian_2")
        self.project_2.custodians.add(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))

        self.readonly_user = factories.UserFactory.create(username='readonly')
        self.assertIsNotNone(self.custodian_2_user)
        self.readonly_user.set_password(password)
        self.readonly_user.save()
        self.readonly_client = APIClient()
        self.assertTrue(self.readonly_client.login(username=self.readonly_user.username, password=password))

        self.anonymous_client = APIClient()

        if hasattr(self, '_more_setup') and callable(self._more_setup):
            self._more_setup()

    def _create_dataset_with_schema(self, project, client, schema, dataset_type=Dataset.TYPE_GENERIC,
                                    dataset_name="Test site code geometry"):
        if isinstance(schema, list):
            # a list of fields instead of a schema?
            schema = create_schema_from_fields(schema)
        resp = client.post(
            reverse('api:dataset-list'),
            data={
                "name": dataset_name,
                "type": dataset_type,
                "project": project.pk,
                'data_package': create_data_package_from_schema(schema)
            },
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        dataset = Dataset.objects.filter(id=resp.json().get('id')).first()
        self.assertIsNotNone(dataset)
        return dataset

    def _create_record(self, client, dataset, record_data):
        payload = {
            'dataset': dataset.pk,
            'data': record_data
        }
        url = reverse('api:record-list')
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        record = Record.objects.filter(id=resp.json().get('id')).first()
        self.assertIsNotNone(record)
        return record

    def _create_dataset_from_rows(self, rows):
        """
        Use the infer end-point and create the dataset
        :param rows: list of lists e.g: [['What', 'When'], ['A bird', '2018-01-24'],...]
        :return: the dataset object
        """
        project = self.project_1
        client = self.data_engineer_1_client
        infer_url = reverse('api:infer-dataset')
        file_ = rows_to_xlsx_file(rows)
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp,
            }
            resp = client.post(infer_url, data=payload, format='multipart')
            self.assertEqual(status.HTTP_200_OK, resp.status_code)
            # create the dataset. We should have to just add the project id from the returned data
            payload = resp.json()
            payload['project'] = project.pk
            resp = client.post(
                reverse('api:dataset-list'),
                data=payload,
                format='json')
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            dataset = Dataset.objects.filter(id=resp.json().get('id')).first()
            self.assertIsNotNone(dataset)
            return dataset

    def _upload_records_from_rows(self, rows, dataset_pk, strict=True):
        """
        Use the the upload end-point
        :param rows same format as _create_dataset_from_rows
        :param dataset_pk:
        :return: the response
        """
        file_ = rows_to_xlsx_file(rows)
        client = self.custodian_1_client
        with open(file_, 'rb') as fp:
            url = reverse('api:dataset-upload', kwargs={'pk': dataset_pk})
            payload = {
                'file': fp,
            }
            if strict:
                payload['strict'] = True
            resp = client.post(url, data=payload, format='multipart')
            return resp

    def _create_dataset_and_records_from_rows(self, rows):
        """
        Combine _create_dataset_from_rows and _create_records_from_rows
        :param rows: see _create_dataset_from_rows
        :return: the dataset object
        """
        dataset = self._create_dataset_from_rows(rows)
        resp = self._upload_records_from_rows(rows, dataset.pk)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        return dataset


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


def create_schema_from_fields(fields):
    result = clone(GENERIC_SCHEMA)
    result['fields'] = fields
    return result


def create_data_package_from_schema(schema):
    result = clone(GENERIC_DATA_PACKAGE)
    result['resources'][0]['schema'] = schema
    return result


def create_data_package_from_fields(fields):
    schema = create_schema_from_fields(fields)
    return create_data_package_from_schema(schema)


def add_model_field_foreign_key_to_schema(schema, options):
    """
    :param schema:
    :param options: expected format, e.g for a Site code foreign key:
    {
        'schema_field': 'Site Code',  # the schema field name (or column name)
        'model': 'Site',
        'model_field': 'code'
    }
    :return:
    """
    foreign_keys = schema.get('foreignKeys', [])
    foreign_keys.append(
        {
            'reference': {
                'resource': options['model'],
                'fields': [
                    options['model_field']
                ]
            },
            'fields': [
                options['schema_field']
            ]
        }
    )
    schema['foreignKeys'] = foreign_keys
    return schema


def set_strict_mode(url):
    return url + '?strict'


def url_post_record_strict():
    return set_strict_mode(reverse('api:record-list'))
