import re
from os import path
import datetime

from openpyxl import load_workbook

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.utils import timezone, six
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Project, Site, Dataset, Record
from main.tests.api import helpers
from main.tests.test_data_package import clone
from main.utils_auth import is_admin


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
        'test-observations'
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
        self.project_1 = Project.objects.filter(title="Project1").first()
        self.site_1 = Site.objects.filter(code="Site1").first()
        self.ds_1 = Dataset.objects.filter(name="Observation1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = self.ds_1.record_model.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(title="Project2").first()
        self.site_2 = Site.objects.filter(code="Site2").first()
        self.ds_2 = Dataset.objects.filter(name="Observation2", project=self.project_2).first()
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
        ds = self.ds_1
        rec = self.record_1
        data = {
            "dataset": rec.dataset.pk,
            "site": rec.site.pk,
            "data": rec.data,
            "datetime": rec.datetime,
            "geometry": rec.geometry.geojson
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
                count = ds.record_queryset.count()
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(ds.record_queryset.count(), count + 1)

    def test_bulk_create(self):
        """
        Cannot create bulk with this end point
        :return:
        """
        urls = [reverse('api:record-list')]
        rec = self.record_1
        ds = self.ds_1
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
                count = ds.record_queryset.count()
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(ds.record_queryset.count(), count + len(data))

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
        'test-observations'
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
        self.project_1 = Project.objects.filter(title="Project1").first()
        self.site_1 = Site.objects.filter(code="Site1").first()
        self.ds_1 = Dataset.objects.filter(name="Observation1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = self.ds_1.record_model.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(title="Project2").first()
        self.site_2 = Site.objects.filter(code="Site2").first()
        self.ds_2 = Dataset.objects.filter(name="Observation2", project=self.project_2).first()
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

    def test_create_one_happy_path(self):
        """
        Test the create of one record
        :return:
        """
        # grab one existing an re-inject it
        record = self.record_1
        ds = self.ds_1
        data = {
            "dataset": record.dataset.pk,
            "data": record.data
        }
        url = reverse('api:record-list')
        client = self.custodian_1_client
        count = ds.record_queryset.count()
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )
        self.assertEquals(ds.record_queryset.count(), count + 1)

    def test_empty_not_allowed(self):
        ds = self.ds_1
        record = self.record_1
        data = {
            "dataset": record.dataset.pk,
            "data": {}
        }
        url = reverse('api:record-list')
        client = self.custodian_1_client
        count = ds.record_queryset.count()
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(ds.record_queryset.count(), count)

    def test_create_column_not_in_schema(self):
        """
        Test that if we introduce a column not in the the dataset it will not validate
        :return:
        """
        ds = self.ds_1
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
        count = ds.record_queryset.count()
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(ds.record_queryset.count(), count)

    def test_update_column_not_in_schema(self):
        """
        Test that if we introduce a column not in the the dataset it will not validate
        :return:
        """
        ds = self.ds_1
        record = self.record_1
        incorrect_data = clone(record.data)
        incorrect_data['Extra Column'] = "Extra Value"
        data = {
            "dataset": record.dataset.pk,
            "data": incorrect_data
        }
        url = reverse('api:record-detail', kwargs={"pk": record.pk})
        client = self.custodian_1_client
        count = ds.record_queryset.count()
        # set strict mode
        url = helpers.set_strict_mode(url)
        self.assertEqual(
            client.put(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(ds.record_queryset.count(), count)
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEquals(ds.record_queryset.count(), count)

    def test_date_error(self):
        """
        An observation must have a date
        :return:
        """
        ds = self.ds_1
        record = self.record_1
        date_column = ds.schema.observation_date_field.name
        new_data = clone(record.data)
        url_post = reverse('api:record-list')
        url_update = reverse('api:record-detail', kwargs={'pk': record.pk})
        valid_values = ['15/08/2008']
        for value in valid_values:
            new_data[date_column] = value
            data = {
                "dataset": record.dataset.pk,
                "data": new_data
            }
            client = self.custodian_1_client
            count = ds.record_queryset.count()
            self.assertEqual(
                client.post(url_post, data, format='json').status_code,
                status.HTTP_201_CREATED
            )
            self.assertEquals(ds.record_queryset.count(), count + 1)

        invalid_values = [None, '', 'abcd']
        for value in invalid_values:
            new_data[date_column] = value
            data = {
                "dataset": record.dataset.pk,
                "data": new_data
            }

            client = self.custodian_1_client
            count = ds.record_queryset.count()
            self.assertEqual(
                client.post(url_post, data, format='json').status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                client.put(url_update, data, format='json').status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                client.patch(url_update, data, format='json').status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEquals(ds.record_queryset.count(), count)

    def test_geometry_error(self):
        """
        An observation must have a valid geometry
        :return:
        """
        ds = self.ds_1
        record = self.record_1
        lat_column = ds.schema.latitude_field.name
        new_data = clone(record.data)
        url_post = reverse('api:record-list')
        url_update = reverse('api:record-detail', kwargs={'pk': record.pk})
        valid_values = [-34.125]
        for value in valid_values:
            new_data[lat_column] = value
            data = {
                "dataset": record.dataset.pk,
                "data": new_data
            }
            client = self.custodian_1_client
            count = ds.record_queryset.count()
            self.assertEqual(
                client.post(url_post, data, format='json').status_code,
                status.HTTP_201_CREATED
            )
            self.assertEquals(ds.record_queryset.count(), count + 1)

        invalid_values = [None, '', 'abcd']
        for value in invalid_values:
            new_data[lat_column] = value
            data = {
                "dataset": record.dataset.pk,
                "data": new_data
            }

            client = self.custodian_1_client
            count = ds.record_queryset.count()
            self.assertEqual(
                client.post(url_post, data, format='json').status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                client.put(url_update, data, format='json').status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEqual(
                client.patch(url_update, data, format='json').status_code,
                status.HTTP_400_BAD_REQUEST
            )
            self.assertEquals(ds.record_queryset.count(), count)


class TestSiteExtraction(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-observations'
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
        self.project_1 = Project.objects.filter(title="Project1").first()
        self.site_1 = Site.objects.filter(code="Adolphus").first()
        self.ds_1 = Dataset.objects.filter(name="Observation1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = self.ds_1.record_model.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))
        self.assertTrue(self.record_1.site, self.site_1)

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(title="Project2").first()
        self.site_2 = Site.objects.filter(code="Site2").first()
        self.ds_2 = Dataset.objects.filter(name="Observation2", project=self.project_2).first()
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

    def test_create_with_site(self):
        """
        The descriptor contains a foreign key to the site.
        Test that the site is extracted from the data
        :return:
        """
        # clear all records
        ds = self.ds_1
        ds.record_queryset.delete()
        self.assertEquals(ds.record_queryset.count(), 0)
        record = self.record_1
        data = {
            "dataset": record.dataset.pk,
            "data": record.data
        }
        schema = ds.schema
        self.assertTrue(schema.has_fk_for_model('Site'))
        expected_site = record.site
        url = reverse('api:record-list')
        client = self.custodian_1_client
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )
        self.assertEquals(ds.record_queryset.count(), 1)
        self.assertEquals(ds.record_queryset.first().site, expected_site)

    def test_update_site(self):
        ds = self.ds_1
        record = ds.record_queryset.filter(site=self.site_1).first()
        self.assertIsNotNone(record)
        site = Site.objects.filter(name="Site1").first()
        # need to test if the site belongs to the dataset project or the update won't happen
        self.assertIsNotNone(site)
        self.assertEquals(site.project, record.dataset.project)
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


class TestDateTimeAndGeometryExtraction(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-observations'
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
        self.project_1 = Project.objects.filter(title="Project1").first()
        self.site_1 = Site.objects.filter(code="Adolphus").first()
        self.ds_1 = Dataset.objects.filter(name="Observation1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = self.ds_1.record_model.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertIsNotNone(self.record_1.datetime)
        self.assertIsNotNone(self.record_1.geometry)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))
        self.assertTrue(self.record_1.site, self.site_1)

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(title="Project2").first()
        self.site_2 = Site.objects.filter(code="Site2").first()
        self.ds_2 = Dataset.objects.filter(name="Observation2", project=self.project_2).first()
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

    def test_create(self):
        """
        Test that the date and geometry are extracted from the data
        and saved in DB
        :return:
        """
        # clear all records
        ds = self.ds_1
        ds.record_queryset.delete()
        self.assertEquals(ds.record_queryset.count(), 0)
        record = self.record_1
        data = {
            "dataset": record.dataset.pk,
            "data": record.data
        }
        expected_datetime = record.datetime
        expected_geojson = record.geometry.geojson
        url = reverse('api:record-list')
        client = self.custodian_1_client
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )
        self.assertEquals(ds.record_queryset.count(), 1)
        self.assertEquals(ds.record_queryset.first().datetime, expected_datetime)
        self.assertEquals(ds.record_queryset.first().geometry.geojson, expected_geojson)

    def test_update(self):
        """
        Test that the date and geometry are extracted from the data
        and saved in DB
        :return:
        """
        # clear all records
        ds = self.ds_1
        record = self.record_1
        new_data = clone(record.data)
        # change date
        date = '20/4/2016'
        expected_date = datetime.date(2016, 4, 20)
        new_data[ds.schema.observation_date_field.name] = date

        # change lat/lon
        lon = 111.111
        lat = 22.222
        new_data[ds.schema.longitude_field.name] = lon
        new_data[ds.schema.latitude_field.name] = lat
        expected_geojson = Point(lon, lat).geojson

        data = {
            "dataset": record.dataset.pk,
            "data": new_data
        }
        url = reverse('api:record-detail', kwargs={"pk": record.pk})
        client = self.custodian_1_client
        count = ds.record_queryset.count()
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_200_OK
        )
        self.assertEquals(ds.record_queryset.count(), count)
        dtz = timezone.localtime(ds.record_queryset.first().datetime)
        self.assertEquals(dtz.date(), expected_date)
        self.assertEquals(ds.record_queryset.first().geometry.geojson, expected_geojson)


class TestSerialization(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-observations'
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
        self.project_1 = Project.objects.filter(title="Project1").first()
        self.site_1 = Site.objects.filter(code="Adolphus").first()
        self.ds_1 = Dataset.objects.filter(name="Observation1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = self.ds_1.record_model.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))
        self.assertTrue(self.record_1.site, self.site_1)

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(title="Project2").first()
        self.site_2 = Site.objects.filter(code="Site2").first()
        self.ds_2 = Dataset.objects.filter(name="Observation2", project=self.project_2).first()
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

    def test_date_serialization_uses_project_timezone(self):
        # TODO: implement this
        pass


class TestExport(helpers.BaseUserTestCase):
    fixtures = helpers.BaseUserTestCase.fixtures + [
        'test-sites',
        'test-datasets',
        'test-observations'
    ]

    def _more_setup(self):
        self.ds_1 = Dataset.objects.filter(name="Observation1", project=self.project_1).first()
        self.assertIsNotNone(self.ds_1)
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))
        self.record_1 = Record.objects.filter(dataset=self.ds_1).first()
        self.assertIsNotNone(self.record_1)
        self.assertTrue(self.record_1.is_custodian(self.custodian_1_user))

        self.ds_2 = Dataset.objects.filter(name="Bats2", project=self.project_2).first()
        self.assertTrue(self.ds_2.is_custodian(self.custodian_2_user))
        self.assertFalse(self.ds_1.is_custodian(self.custodian_2_user))

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
        self.assertEquals(resp.status_code, status.HTTP_403_FORBIDDEN)
