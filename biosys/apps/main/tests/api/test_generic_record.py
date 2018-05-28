import re
from os import path
import unittest

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.utils import six
from openpyxl import load_workbook
from openpyxl.cell import Cell
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Project, Site, Dataset, Record
from main.tests.api import helpers
from main.tests.test_data_package import clone
from main.utils_auth import is_admin


# TODO Use the helpers.BaseUserTestCase as base class for all tests and methods for generating schema (no fixtures)
class TestPermissions(TestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin, custodians
    Create: admin, custodians
    Delete: admin, custodians
    """
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-generic-records'
    ]

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        password = 'password'
        self.admin_user = User.objects.filter(username="admin").first()
        self.assertIsNotNone(self.admin_user)
        self.assertTrue(is_admin(self.admin_user))
        self.admin_user.set_password(password)
        self.admin_user.save()
        self.admin_client = APIClient()
        self.assertTrue(self.admin_client.login(username=self.admin_user.username, password=password))

        self.custodian_1_user = User.objects.filter(username="custodian1").first()
        self.assertIsNotNone(self.custodian_1_user)
        self.custodian_1_user.set_password(password)
        self.custodian_1_user.save()
        self.custodian_1_client = APIClient()
        self.assertTrue(self.custodian_1_client.login(username=self.custodian_1_user.username, password=password))
        self.project_1 = Project.objects.filter(name="Project1").first()
        self.site_1 = Site.objects.filter(code="Site1").first()
        self.ds_1 = Dataset.objects.filter(name="Generic1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = Record.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(name="Project2").first()
        self.site_2 = Site.objects.filter(code="Site2").first()
        self.ds_2 = Dataset.objects.filter(name="Bats2", project=self.project_2).first()
        self.assertTrue(self.ds_2.is_custodian(self.custodian_2_user))
        self.assertFalse(self.ds_1.is_custodian(self.custodian_2_user))

        self.readonly_user = User.objects.filter(username="readonly").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.assertFalse(self.site_2.is_custodian(self.readonly_user))
        self.assertFalse(self.site_1.is_custodian(self.readonly_user))
        self.readonly_user.set_password(password)
        self.readonly_user.save()
        self.readonly_client = APIClient()
        self.assertTrue(self.readonly_client.login(username=self.readonly_user.username, password=password))

        self.anonymous_client = APIClient()

    def test_get(self):
        urls = [
            reverse('api:record-list'),
            reverse('api:record-detail', kwargs={'pk': 1})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.get(url).status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.get(url).status_code,
                    status.HTTP_200_OK
                )

    def test_create(self):
        """
        Admin and custodians
        :return:
        """
        urls = [reverse('api:record-list')]
        rec = self.record_1
        data = {
            "dataset": rec.dataset.pk,
            "site": rec.site.pk,
            "data": rec.data
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                count = Record.objects.count()
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(Record.objects.count(), count + 1)

    def test_bulk_create(self):
        """
        Cannot create bulk with this end point
        :return:
        """
        urls = [reverse('api:record-list')]
        rec = self.record_1
        data = [
            {
                "dataset": rec.dataset.pk,
                "site": rec.site.pk,
                "data": rec.data
            },
            {
                "dataset": rec.dataset.pk,
                "site": rec.site.pk,
                "data": rec.data
            }
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client,
                          self.admin_client, self.custodian_1_client],
            "allowed": []
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                count = Record.objects.count()
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(Record.objects.count(), count + len(data))

    def test_update(self):
        """
        admin + custodian of project for site 1
        :return:
        """
        rec = self.record_1
        previous_data = clone(rec.data)
        updated_data = clone(previous_data)
        updated_data['Longitude'] = '118.78'
        urls = [reverse('api:record-detail', kwargs={'pk': rec.pk})]
        data = {
            "data": updated_data,
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                rec.data = previous_data
                rec.save()
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                rec.refresh_from_db()
                self.assertEqual(rec.data, updated_data)

    def test_delete(self):
        """
        Currently admin + custodian
        :return:
        """
        rec = self.record_1
        urls = [reverse('api:record-detail', kwargs={'pk': rec.pk})]
        data = None
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                rec.save()
                count = Dataset.objects.count()
                self.assertEqual(
                    client.delete(url, data, format='json').status_code,
                    status.HTTP_204_NO_CONTENT
                )
                self.assertTrue(Dataset.objects.count(), count - 1)

    def test_options(self):
        urls = [
            reverse('api:record-list'),
            reverse('api:record-detail', kwargs={'pk': 1})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.options(url).status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        # authenticated
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.options(url).status_code,
                    status.HTTP_200_OK
                )


class TestDataValidation(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-generic-records'
    ]

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        password = 'password'
        self.admin_user = User.objects.filter(username="admin").first()
        self.assertIsNotNone(self.admin_user)
        self.assertTrue(is_admin(self.admin_user))
        self.admin_user.set_password(password)
        self.admin_user.save()
        self.admin_client = APIClient()
        self.assertTrue(self.admin_client.login(username=self.admin_user.username, password=password))

        self.custodian_1_user = User.objects.filter(username="custodian1").first()
        self.assertIsNotNone(self.custodian_1_user)
        self.custodian_1_user.set_password(password)
        self.custodian_1_user.save()
        self.custodian_1_client = APIClient()
        self.assertTrue(self.custodian_1_client.login(username=self.custodian_1_user.username, password=password))
        self.project_1 = Project.objects.filter(name="Project1").first()
        self.site_1 = Site.objects.filter(code="Adolphus").first()
        self.ds_1 = Dataset.objects.filter(name="Generic1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = Record.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))
        self.assertIsNotNone(self.record_1.site)
        self.assertEquals(self.site_1, self.record_1.site)

    def test_create_one_happy_path(self):
        """
        Test the create of one record
        :return:
        """
        # grab one existing an re-inject it
        record = self.record_1
        data = {
            "dataset": record.dataset.pk,
            "data": record.data
        }
        url = reverse('api:record-list')
        client = self.custodian_1_client
        count = Record.objects.count()
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )
        self.assertEquals(Record.objects.count(), count + 1)

    def test_empty_not_allowed(self):
        record = self.record_1
        data = {
            "dataset": record.dataset.pk,
            "data": {}
        }
        url = reverse('api:record-list')
        # set strict mode
        url = helpers.set_strict_mode(url)
        client = self.custodian_1_client
        count = Record.objects.count()
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(Record.objects.count(), count)

    def test_create_column_not_in_schema(self):
        """
        Test that if we introduce a column not in the the dataset it will not validate
        :return:
        """
        record = self.record_1
        incorrect_data = clone(record.data)
        incorrect_data['Extra Column'] = "Extra Value"
        data = {
            "dataset": record.dataset.pk,
            "data": incorrect_data
        }
        url = reverse('api:record-list')
        # set strict mode
        url = helpers.set_strict_mode(url)
        client = self.custodian_1_client
        count = Record.objects.count()
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(Record.objects.count(), count)

    def test_update_column_not_in_schema(self):
        """
        Test that if we introduce a column not in the the dataset it will not validate
        :return:
        """
        record = self.record_1
        incorrect_data = clone(record.data)
        incorrect_data['Extra Column'] = "Extra Value"
        data = {
            "dataset": record.dataset.pk,
            "data": incorrect_data
        }
        url = reverse('api:record-detail', kwargs={"pk": record.pk})
        # set strict mode
        url = helpers.set_strict_mode(url)
        client = self.custodian_1_client
        count = Record.objects.count()
        self.assertEqual(
            client.put(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(Record.objects.count(), count)
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(Record.objects.count(), count)


class TestSiteExtraction(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-generic-records'
    ]

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        password = 'password'
        self.admin_user = User.objects.filter(username="admin").first()
        self.assertIsNotNone(self.admin_user)
        self.assertTrue(is_admin(self.admin_user))
        self.admin_user.set_password(password)
        self.admin_user.save()
        self.admin_client = APIClient()
        self.assertTrue(self.admin_client.login(username=self.admin_user.username, password=password))

        self.custodian_1_user = User.objects.filter(username="custodian1").first()
        self.assertIsNotNone(self.custodian_1_user)
        self.custodian_1_user.set_password(password)
        self.custodian_1_user.save()
        self.custodian_1_client = APIClient()
        self.assertTrue(self.custodian_1_client.login(username=self.custodian_1_user.username, password=password))
        self.project_1 = Project.objects.filter(name="Project1").first()
        self.site_1 = Site.objects.filter(code="Adolphus").first()
        self.ds_1 = Dataset.objects.filter(name="Generic1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = Record.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))
        self.assertIsNotNone(self.record_1.site)
        self.assertEquals(self.site_1, self.record_1.site)

    def test_create_with_site(self):
        """
        The descriptor contains a foreign key to the site.
        Test that the site is extracted from the data
        :return:
        """
        # clear all records
        Record.objects.all().delete()
        self.assertEquals(Record.objects.count(), 0)
        record = self.record_1
        data = {
            "dataset": record.dataset.pk,
            "data": record.data
        }
        schema = self.ds_1.schema
        self.assertTrue(schema.has_fk_for_model('Site'))
        expected_site = self.site_1
        url = reverse('api:record-list')
        client = self.custodian_1_client
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )
        self.assertEquals(Record.objects.count(), 1)
        self.assertEquals(Record.objects.first().site, expected_site)

    def test_update_site(self):
        record = Record.objects.filter(site=self.site_1).first()
        self.assertIsNotNone(record)
        site = Site.objects.filter(name="Site1").first()
        # need to test if the site belongs to the dataset project or the update won't happen
        self.assertIsNotNone(site)
        self.assertTrue(site.project == record.dataset.project)
        self.assertNotEquals(record.site, site)
        # update site value
        schema = record.dataset.schema
        site_column = schema.get_fk_for_model('Site').data_field
        r_data = record.data
        r_data[site_column] = site.code
        data = {
            "data": r_data
        }
        url = reverse('api:record-detail', kwargs={"pk": record.pk})
        client = self.custodian_1_client
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_200_OK
        )
        record.refresh_from_db()
        self.assertEqual(record.site, site)


class TestExport(helpers.BaseUserTestCase):
    fixtures = helpers.BaseUserTestCase.fixtures + [
        'test-sites',
        'test-datasets',
        'test-generic-records'
    ]

    def _more_setup(self):
        self.ds_1 = Dataset.objects.filter(name="Generic1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = Record.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))

        self.ds_2 = Dataset.objects.filter(name="Bats2", project=self.project_2).first()
        self.assertTrue(self.ds_2.is_custodian(self.custodian_2_user))
        self.assertFalse(self.ds_1.is_custodian(self.custodian_2_user))

    def _create_dataset_with_schema(self, project, client, schema):
        resp = client.post(
            reverse('api:dataset-list'),
            data={
                "name": "Test site code geometry",
                "type": Dataset.TYPE_GENERIC,
                "project": project.pk,
                'data_package': helpers.create_data_package_from_schema(schema)
            },
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        dataset = Dataset.objects.filter(id=resp.json().get('id')).first()
        self.assertIsNotNone(dataset)
        return dataset

    def test_happy_path_no_filter(self):
        client = self.custodian_1_client
        dataset = self.ds_1
        all_records = Record.objects.filter(dataset=dataset)
        self.assertTrue(all_records.count() > 0)
        url = reverse('api:record-list')
        query = {
            'dataset__id': dataset.pk,
            'output': 'xlsx'
        }
        try:
            resp = client.get(url, query)
        except Exception as e:
            self.fail("Export should not raise an exception: {}".format(e))
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        # check headers
        self.assertEqual(resp.get('content-type'),
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        content_disposition = resp.get('content-disposition')
        # should be something like:
        # 'attachment; filename=DatasetName_YYYY_MM_DD-HHMMSS.xlsx
        match = re.match('attachment; filename=(.+)', content_disposition)
        self.assertIsNotNone(match)
        filename, ext = path.splitext(match.group(1))
        self.assertEquals(ext, '.xlsx')
        filename.startswith(dataset.name)
        # read content
        wb = load_workbook(six.BytesIO(resp.content), read_only=True)
        # one datasheet named from dataset
        sheet_names = wb.get_sheet_names()
        self.assertEquals(1, len(sheet_names))
        self.assertEquals(dataset.name, sheet_names[0])
        ws = wb.get_sheet_by_name(dataset.name)
        rows = list(ws.rows)
        expected_records = Record.objects.filter(dataset=dataset)
        self.assertEquals(len(rows), expected_records.count() + 1)
        headers = [c.value for c in rows[0]]
        schema = dataset.schema
        # all the columns of the schema should be in the excel
        self.assertEquals(schema.headers, headers)

    def test_permission_ok_for_not_custodian(self):
        """Export is a read action. Should be authorised for every logged-in user."""
        client = self.custodian_2_client
        dataset = self.ds_1
        url = reverse('api:record-list')
        query = {
            'dataset__id': dataset.pk,
            'output': 'xlsx'
        }
        try:
            resp = client.get(url, query)
        except Exception as e:
            self.fail("Export should not raise an exception: {}".format(e))
        self.assertEquals(resp.status_code, status.HTTP_200_OK)

    def test_permission_denied_if_not_logged_in(self):
        """Must be logged-in."""
        client = self.anonymous_client
        dataset = self.ds_1
        url = reverse('api:record-list')
        query = {
            'dataset__id': dataset.pk,
            'output': 'xlsx'
        }
        try:
            resp = client.get(url, query)
        except Exception as e:
            self.fail("Export should not raise an exception: {}".format(e))
        self.assertEquals(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_excel_type(self):
        schema_fields = [
            {
                "name": "string",
                "type": "string",
                "format": "default"
            },
            {
                "name": "number",
                "type": "number",
                "format": "default"
            },
            {
                "name": "integer",
                "type": "integer",
                "format": "default"
            },
            {
                "name": "date",
                "type": "date",
                "format": "any"
            },
            {
                "name": "datetime",
                "type": "datetime",
                "format": "any"
            },
            {
                "name": "boolean",
                "type": "boolean",
                "format": "default"
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        project = self.project_1
        client = self.custodian_1_client
        dataset = self._create_dataset_with_schema(project, client, schema)

        # create one record
        record_data = {
            "string": "string",
            "number": 12.3,
            "integer": 456,
            "date": "21/06/2017",
            "datetime": "13/04/2017 15:55",
            "boolean": 'yes'
        }
        payload = {
            'dataset': dataset.pk,
            'data': record_data
        }
        url = reverse('api:record-list')
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        record = Record.objects.filter(id=resp.json().get('id')).first()
        self.assertIsNotNone(record)
        url = reverse('api:record-list')
        query = {
            'dataset__id': dataset.pk,
            'output': 'xlsx'
        }
        try:
            resp = client.get(url, query)
        except Exception as e:
            self.fail("Export should not raise an exception: {}".format(e))
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        # load workbook
        wb = load_workbook(six.BytesIO(resp.content))
        ws = wb.get_sheet_by_name(dataset.name)
        rows = list(ws.rows)
        self.assertEqual(len(rows), 2)
        cells = rows[1]
        string, number, integer, date, datetime, boolean = cells
        # excel type are string, number or boolean
        self.assertEqual(string.data_type, Cell.TYPE_STRING)
        self.assertEqual(number.data_type, Cell.TYPE_NUMERIC)
        self.assertEqual(integer.data_type, Cell.TYPE_NUMERIC)
        self.assertEqual(date.data_type, Cell.TYPE_NUMERIC)
        self.assertEqual(datetime.data_type, Cell.TYPE_NUMERIC)
        self.assertEqual(boolean.data_type, Cell.TYPE_BOOL)


class TestFilteringAndOrdering(helpers.BaseUserTestCase):

    def test_filter_dataset(self):
        dataset1 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Who'],
            ['Crashed the db', '2018-02-14', 'Serge'],
            ['Restored the db', '2018-02-14', 'Shay']
        ])

        dataset2 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-02-14', -32.0, 115.75],
            ['Chubby bat', '2017-05-18', -34.4, 116.78]
        ])

        client = self.custodian_1_client
        url = reverse('api:record-list')

        # no filters
        resp = client.get(url)
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 4)
        expected_whats = sorted(['Crashed the db', 'Restored the db', 'Canis lupus', 'Chubby bat'])
        self.assertEquals(sorted([r['data']['What'] for r in records]), expected_whats)

        # dataset__id
        expected_dataset = dataset1
        url = reverse('api:record-list')
        resp = client.get(url, {'dataset__id': expected_dataset.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 2)
        expected_whats = sorted(['Crashed the db', 'Restored the db'])
        self.assertEquals(sorted([r['data']['What'] for r in records]), expected_whats)

        # dataset__name
        expected_dataset = dataset2
        resp = client.get(url, {'dataset__name': expected_dataset.name})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 2)
        expected_whats = sorted(['Canis lupus', 'Chubby bat'])
        self.assertEquals(sorted([r['data']['What'] for r in records]), expected_whats)

    def test_search_in_json_data(self):
        """
        Test that if we provide a dataset and a search parameters we can search through the data json field
        :return:
        """
        dataset1 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Who'],
            ['Crashed the db', '2018-02-14', 'Serge'],
            ['Restored the db', '2018-02-14', 'Shay']
        ])

        dataset2 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-02-14', -32.0, 115.75],
            ['Chubby bat', '2017-05-18', -34.4, 116.78],
            ['Chubby Serge', '2017-05-18', -34.4, 116.78]
        ])

        client = self.custodian_1_client
        url = reverse('api:record-list')

        # search Serge in dataset1
        resp = client.get(url, {'search': 'Serge', 'dataset__id': dataset1.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 1)
        record = records[0]
        expected_data = sorted(['Crashed the db', '2018-02-14', 'Serge'])
        self.assertEquals(sorted(list(record['data'].values())), expected_data)

        # search serge in dataset2 case insensitive
        resp = client.get(url, {'search': 'Serge', 'dataset__id': dataset2.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 1)
        record = records[0]
        expected_data = sorted(['Chubby Serge', '2017-05-18', '-34.4', '116.78'])
        record_values_as_string = [str(v) for v in record['data'].values()]
        self.assertEquals(sorted(list(record_values_as_string)), expected_data)

    def test_string_ordering_in_json_data(self):
        """
        Test that if we provide a dataset and an order parameter (field) we can order through the data json field
        for string
        :return:
        """
        dataset = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-02-14', -32.0, 115.75],
            ['Zebra', '2017-01-01', -34.7, 115.75],
            ['Chubby bat', '2017-05-18', -34.4, 116.78],
            ['Alligator', '2017-05-18', -34.4, 116.78]
        ])

        client = self.custodian_1_client
        url = reverse('api:record-list')

        # order by What asc
        ordering = 'What'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 4)
        expected_whats = sorted(['Alligator', 'Canis lupus', 'Chubby bat', 'Zebra'])
        self.assertEquals([r['data']['What'] for r in records], expected_whats)

        # order by What desc
        ordering = '-What'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 4)
        expected_whats = sorted(['Alligator', 'Canis lupus', 'Chubby bat', 'Zebra'], reverse=True)
        self.assertEquals([r['data']['What'] for r in records], expected_whats)

        # test that the ordering is case sensitive
        ordering = 'what'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 4)
        expected_whats = sorted(['Alligator', 'Canis lupus', 'Chubby bat', 'Zebra'])
        self.assertNotEquals([r['data']['What'] for r in records], expected_whats)

    def test_server_side_ordering_row_number(self):
        """
        Test that we can order by the source_info['row'] (row number in the csv or xlsx) and that the
        sort in numeric based not char based (10 is after 9)
        """
        # create 11 records (data not important)
        rows = [
            ['When', 'Species', 'How Many', 'Latitude', 'Longitude', 'Comments'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-10', 'Unknown', 2, -32.0, 115.75, 'Canis?'],
            ['2018-02-02', 'Canis dingo', 2, -32.0, 115.75, 'Watch out kids'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-10', 'Unknown', 2, -32.0, 115.75, 'Canis?'],
            ['2018-02-02', 'Canis dingo', 2, -32.0, 115.75, 'Watch out kids'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-10', 'Unknown', 2, -32.0, 115.75, 'Canis?'],
        ]
        dataset = self._create_dataset_and_records_from_rows(rows)
        client = self.custodian_1_client
        url = reverse('api:record-list')
        ordering = 'row'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_response = resp.json()
        self.assertEquals(len(json_response), 11)

        # row start at 2
        sorted_rows = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        record_rows = [record['source_info']['row'] for record in json_response]
        self.assertEqual(record_rows, sorted_rows)

        # check is request ordered by family in descending order is ordered by family in reverse alphabetical order
        ordering = '-row'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_response = resp.json()
        self.assertEquals(len(json_response), 11)

        record_rows = [record['source_info']['row'] for record in json_response]
        self.assertEqual(record_rows, list(reversed(sorted_rows)))

    def test_numeric_ordering_in_json_data_from_upload_end_point(self):
        """
        Assuming we have a schema that contains a numeric field (integer or number types).
        Querying an order on this field should return a numerical order not string (10, after 9)
        This test uses the upload end_point
        """
        dataset = self._create_dataset_and_records_from_rows([
            ['What', 'How Many'],
            ['Canis lupus', 7],
            ['Zebra', 1],
            ['Chubby bat', 9],
            ['Alligator', 10]
        ])
        # check that we have a field of type integer
        self.assertEquals(dataset.schema.get_field_by_name('How Many').type, 'integer')

        client = self.custodian_1_client
        url = reverse('api:record-list')

        ordering = 'How Many'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 4)
        expected = [('Zebra', 1), ('Canis lupus', 7), ('Chubby bat', 9), ('Alligator', 10)]
        self.assertEquals([(r['data']['What'], r['data']['How Many']) for r in records], expected)

    def test_numeric_ordering_in_json_data_from_post_end_point(self):
        """
        Assuming we have a schema that contains a numeric field (integer or number types).
        Querying an order on this field should return a numerical order not string (10, after 9)
        This test uses the api POST record/ end_point with floats instead of integers.
        """
        weights = [23.6, 123.4, 2.6, 203.4]
        # sorted float list should return [2.6, 23.6, 123.4, 203.4]
        # while a string sorted should return ['123.4', '2.6', '203.4', '23.6']
        float_sorted = sorted(weights)
        string_sorted = sorted([str(w) for w in weights])
        self.assertNotEquals(float_sorted, [float(s) for s in string_sorted])

        dataset = self._create_dataset_from_rows([
            ['What', 'Weight'],
            ['Canis lupus', weights[0]],
            ['Zebra', weights[1]],
            ['Chubby bat', weights[2]],
            ['Alligator', weights[3]]
        ])
        # check that we have a field of type integer
        self.assertEquals(dataset.schema.get_field_by_name('Weight').type, 'number')
        # post some records
        records_data = [
            {
                'What': 'Canis lupus',
                'Weight': weights[0]
            },
            {
                'What': 'Zebra',
                'Weight': weights[1]
            },
            {
                'What': 'Chubby bat',
                'Weight': weights[2]
            },
            {
                'What': 'Alligator',
                'Weight': weights[3]
            },
        ]
        records = []
        for record_data in records_data:
            records.append(self._create_record(self.custodian_1_client, dataset, record_data))
        client = self.custodian_1_client
        url = reverse('api:record-list')

        ordering = 'Weight'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 4)
        expected = [('Chubby bat', 2.6), ('Canis lupus', 23.6), ('Zebra', 123.4), ('Alligator', 203.4)]
        self.assertEquals([(r['data']['What'], r['data']['Weight']) for r in records], expected)

        # revert ordering
        ordering = '-Weight'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEquals(len(records), 4)
        # reverse expected
        expected = expected[::-1]
        self.assertEquals([(r['data']['What'], r['data']['Weight']) for r in records], expected)


class TestSchemaValidation(helpers.BaseUserTestCase):

    def assert_create_dataset(self, schema):
        try:
            return self._create_dataset_with_schema(
                self.project_1,
                self.custodian_1_client,
                schema,
                dataset_type=Dataset.TYPE_GENERIC
            )
        except Exception as e:
            self.fail('Species Observation dataset creation failed for schema {schema}'.format(
                schema=schema
            ))

    def test_not_required_date_with_format_any(self):
        """
        field of type date, not required with format any should not raise an error when received a empty string
        see https://decbugs.com/view.php?id=6928
        """
        schema_fields = [
            {
                "name": "DateAny",
                "type": "date",
                "format": "any",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "DateTimeAny",
                "type": "datetime",
                "format": "any",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "DateDefault",
                "type": "date",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "DateTimeDefault",
                "type": "datetime",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        dataset = self.assert_create_dataset(schema)
        records = [
            ['DateAny', 'DateTimeAny', 'DateDefault', 'DateTimeDefault'],
            [None, None, None, None],
            ['', '', '', ''],
            ['  ', '   ', '  ', '  '],
        ]
        resp = self._upload_records_from_rows(records, dataset_pk=dataset.pk, strict=True)
        self.assertEquals(resp.status_code, status.HTTP_200_OK)

    def test_required_date_with_format_any(self):
        """
        field of type date, required with format should
        """
        schema_fields = [
            {
                "name": "DateAny",
                "type": "date",
                "format": "any",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "What",
                "type": "string",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        dataset = self.assert_create_dataset(schema)
        records = [
            ['DateAny', 'What'],
            [None, 'something'],
            ['', 'something'],
            ['   ', 'something'],
        ]
        resp = self._upload_records_from_rows(records, dataset_pk=dataset.pk, strict=True)
        self.assertEquals(resp.status_code, status.HTTP_400_BAD_REQUEST)
        received = resp.json()
        self.assertIsInstance(received, list)
        self.assertEquals(len(received), 3)
        # this what an report should look like
        expected_row_report = {
            'row': 3,
            'errors': {'DateAny': 'Field "DateAny" has constraint "required" which is not satisfied for value "None"'},
            'warnings': {}}
        for row_report in received:
            self.assertIn('errors', row_report)
            errors = row_report.get('errors')
            self.assertIn('DateAny', errors)
            msg = errors.get('DateAny')
            self.assertEquals(msg, expected_row_report['errors']['DateAny'])

