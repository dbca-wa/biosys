import datetime
import re
from os import path

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.utils import timezone, six
from openpyxl import load_workbook
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Project, Site, Dataset, Record
from main.tests.api import helpers
from main.tests.test_data_package import clone
from main.utils_auth import is_admin
from main.utils_species import NoSpeciesFacade


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
        'test-species-observations'
    ]
    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
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
        ds = self.ds_1
        rec = self.record_1
        data = {
            "dataset": rec.dataset.pk,
            "data": rec.data,
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
        'test-species-observations'
    ]

    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
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
        # set strict mode
        url = helpers.set_strict_mode(url)
        client = self.custodian_1_client
        count = ds.record_queryset.count()
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

        invalid_values = [None, '', 'not a date']
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

        invalid_values = [None, '', 'not a valid latitude']
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

    def test_species_name(self):
        ds = self.ds_1
        record = self.record_1
        column = ds.schema.species_name_field.name
        new_data = clone(record.data)
        url_post = reverse('api:record-list')
        url_update = reverse('api:record-detail', kwargs={'pk': record.pk})
        valid_values = ['Canis Lupus', 'chubby bat', 'anything']
        for value in valid_values:
            new_data[column] = value
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

        invalid_values = [None, '', 125]
        for value in invalid_values:
            new_data[column] = value
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


class TestDateTimeAndGeometryExtraction(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
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
        count = ds.record_queryset.count()
        url = reverse('api:record-detail', kwargs={"pk": record.pk})
        client = self.custodian_1_client
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_200_OK
        )
        self.assertEquals(ds.record_queryset.count(), count)
        dtz = timezone.localtime(ds.record_queryset.first().datetime)
        self.assertEquals(dtz.date(), expected_date)
        self.assertEquals(ds.record_queryset.first().geometry.geojson, expected_geojson)


class TestSpeciesNameExtraction(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
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

    def test_create(self):
        """
        Test that the species name is extracted from the data and saved in DB
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
        expected_name = record.species_name
        url = reverse('api:record-list')
        client = self.custodian_1_client
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )
        self.assertEquals(ds.record_queryset.count(), 1)
        self.assertEquals(ds.record_queryset.first().species_name, expected_name)

    def test_update(self):
        """
        Test that the species name is extracted from the data and saved in DB
        :return:
        """
        # clear all records
        ds = self.ds_1
        record = self.record_1
        new_data = clone(record.data)
        # change species name
        name = 'Chubby Bat'
        self.assertEqual(ds.record_queryset.filter(species_name=name).count(), 0)
        new_data[ds.schema.species_name_field.name] = name
        data = {
            "dataset": record.dataset.pk,
            "data": new_data
        }
        count = ds.record_queryset.count()
        url = reverse('api:record-detail', kwargs={"pk": record.pk})
        client = self.custodian_1_client
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_200_OK
        )
        self.assertEquals(ds.record_queryset.count(), count)
        self.assertEqual(ds.record_queryset.filter(species_name=name).count(), 1)


class TestNameIDFromSpeciesName(TestCase):
    """
    Test that we retrieve the name id from the species facade
    """
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    species_facade_class = helpers.LightSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def setUp(self):
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
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

    def test_create(self):
        """
        Test that the name_id is retrieved from the species facade from the species_name
        :return:
        """
        ds = self.ds_1
        record = self.record_1
        column = ds.schema.species_name_field.name
        new_data = clone(record.data)
        for species_name, name_id in list(helpers.LightSpeciesFacade().name_id_by_species_name().items())[:2]:
            ds.record_queryset.delete()
            self.assertEquals(ds.record_queryset.count(), 0)
            new_data[column] = species_name
            data = {
                "dataset": record.dataset.pk,
                "data": new_data
            }
            url = reverse('api:record-list')
            client = self.custodian_1_client
            self.assertEqual(
                client.post(url, data, format='json').status_code,
                status.HTTP_201_CREATED
            )
            self.assertEquals(ds.record_queryset.count(), 1)
            self.assertEquals(ds.record_queryset.first().name_id, name_id)

    def test_update(self):
        """
        Test that the name_id is retrieved from the species facade from the species_name
        :return:
        """
        ds = self.ds_1
        record = self.record_1
        column = ds.schema.species_name_field.name
        new_data = clone(record.data)
        for species_name, name_id in list(helpers.LightSpeciesFacade().name_id_by_species_name().items())[:2]:
            new_data[column] = species_name
            data = {
                "dataset": record.dataset.pk,
                "data": new_data
            }
            url = reverse('api:record-detail', kwargs={"pk": record.pk})
            client = self.custodian_1_client
            self.assertEqual(
                client.put(url, data, format='json').status_code,
                status.HTTP_200_OK
            )
            record.refresh_from_db()
            self.assertEqual(record.name_id, name_id)


class TestExport(helpers.BaseUserTestCase):
    fixtures = helpers.BaseUserTestCase.fixtures + [
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    def _more_setup(self):
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
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
        self.assertEquals(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSpeciesNameFromNameID(helpers.BaseUserTestCase):
    """
    Use case:
    The schema doesn't include a Species Name but just a NameId column.
    Test that using the upload (excel) or API the species name is collected from herbie and populated.
    The test suite uses a mock herbie facade with a static species_name -> nameId dict
    @see helpers.SOME_SPECIES_NAME_NAME_ID_MAP
    """

    species_facade_class = helpers.LightSpeciesFacade

    def _more_setup(self):
        # set the HerbieFacade class
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class

    @staticmethod
    def schema_with_name_id():
        schema_fields = [
            {
                "name": "NameId",
                "type": "integer",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "When",
                "type": "date",
                "constraints": helpers.REQUIRED_CONSTRAINTS,
                "format": "any",
                "biosys": {
                    'type': 'observationDate'
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "Longitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        return schema

    def test_species_name_collected_upload(self):
        """
        Happy path: upload excel with a valid nameId.
        :return:
        """
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        # data
        csv_data = [
            ['NameId', 'When', 'Latitude', 'Longitude'],
            [25454, '01/01/2017', -32.0, 115.75],  # "Canis lupus"
            ['24204', '02/02/2017', -33.0, 116.0]  # "Vespadelus douglasorum"
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        self.assertEquals(0, Record.objects.filter(dataset=dataset).count())
        url = reverse('api:dataset-upload', kwargs={'pk': dataset.pk})
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp
            }
            resp = client.post(url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            records = Record.objects.filter(dataset=dataset)
            self.assertEquals(records.count(), len(csv_data) - 1)
            for r in records:
                self.assertTrue(r.name_id > 0)
                self.assertIsNotNone(r.species_name)
            canis_lupus = records.filter(name_id=25454).first()
            self.assertIsNotNone(canis_lupus)
            self.assertEqual(canis_lupus.species_name, "Canis lupus")
            vespadelus = records.filter(name_id=24204).first()
            self.assertIsNotNone(vespadelus)
            self.assertEqual(vespadelus.species_name, "Vespadelus douglasorum")

    def test_species_name_collected_api_create(self):
        """
        Same as above: testing that the species name is collected when using the API create
        :return:
        """
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        record_data = {
            'NameId': 25454,  # "Canis lupus"
            'When': '12/12/2017',
            'Latitude': -32.0,
            'Longitude': 115.756
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
        self.assertEqual(record.name_id, 25454)
        self.assertEqual(record.species_name, "Canis lupus")

    def test_species_name_collected_api_update(self):
        """
        Updating the nameId should update the species name
        :return:
        """
        # create record
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        record_data = {
            'NameId': 25454,  # "Canis lupus"
            'When': '12/12/2017',
            'Latitude': -32.0,
            'Longitude': 115.756
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
        self.assertEqual(record.name_id, 25454)
        self.assertEqual(record.species_name, "Canis lupus")

        # patch nameId
        new_name_id = 24204
        record_data['NameId'] = new_name_id
        expected_species_name = 'Vespadelus douglasorum'
        url = reverse('api:record-detail', kwargs={'pk': record.pk})
        payload = {
            'data': record_data
        }
        resp = client.patch(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        record.refresh_from_db()
        self.assertEqual(record.name_id, new_name_id)
        self.assertEqual(record.species_name, expected_species_name)

    def test_wrong_id_rejected_upload(self):
        """
        If a wrong nameId is provided the system assume its an error
        :return:
        """
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        # data
        csv_data = [
            ['NameId', 'When', 'Latitude', 'Longitude'],
            [99934, '01/01/2017', -32.0, 115.75],  # wrong
            ['24204', '02/02/2017', -33.0, 116.0]  # "Vespadelus douglasorum"
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        self.assertEquals(0, Record.objects.filter(dataset=dataset).count())
        url = reverse('api:dataset-upload', kwargs={'pk': dataset.pk})
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp
            }
            resp = client.post(url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_400_BAD_REQUEST, resp.status_code)
            records = Record.objects.filter(dataset=dataset)
            # should be only one record (the good one)
            self.assertEquals(records.count(), 1)
            vespadelus = records.filter(name_id=24204).first()
            self.assertIsNotNone(vespadelus)
            self.assertEqual(vespadelus.species_name, "Vespadelus douglasorum")

    def test_wrong_id_rejected_api_create(self):
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        record_data = {
            'NameId': 9999,  # wrong
            'When': '12/12/2017',
            'Latitude': -32.0,
            'Longitude': 115.756
        }
        payload = {
            'dataset': dataset.pk,
            'data': record_data
        }
        url = reverse('api:record-list')
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Record.objects.filter(dataset=dataset).count(), 0)


class TestSpeciesNameAndNameID(helpers.BaseUserTestCase):
    """
    Use case:
    The schema includes a Species Name and a NameId column.
    Test that the nameID takes precedence
    The test suite uses a mock herbie facade with a static species_name -> nameId dict
    @see helpers.SOME_SPECIES_NAME_NAME_ID_MAP
    """

    species_facade_class = helpers.LightSpeciesFacade

    def _more_setup(self):
        # set the HerbieFacade class
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class

    @staticmethod
    def schema_with_name_id_and_species_name():
        schema_fields = [
            {
                "name": "NameId",
                "type": "integer",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "Species Name",
                "type": "string",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "When",
                "type": "date",
                "constraints": helpers.REQUIRED_CONSTRAINTS,
                "format": "any",
                "biosys": {
                    'type': 'observationDate'
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "Longitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        return schema

    def test_species_name_collected_upload(self):
        """
        Happy path: upload excel with a valid nameId.
        :return:
        """
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id_and_species_name()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        # data
        csv_data = [
            ['NameId', 'Species Name', 'When', 'Latitude', 'Longitude'],
            [25454, 'Chubby Bat', '01/01/2017', -32.0, 115.75],  # "Canis lupus"
            ['24204', 'French Frog', '02/02/2017', -33.0, 116.0]  # "Vespadelus douglasorum"
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        self.assertEquals(0, Record.objects.filter(dataset=dataset).count())
        url = reverse('api:dataset-upload', kwargs={'pk': dataset.pk})
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp
            }
            resp = client.post(url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            records = Record.objects.filter(dataset=dataset)
            self.assertEquals(records.count(), len(csv_data) - 1)
            for r in records:
                self.assertTrue(r.name_id > 0)
                self.assertIsNotNone(r.species_name)
            canis_lupus = records.filter(name_id=25454).first()
            self.assertIsNotNone(canis_lupus)
            self.assertEqual(canis_lupus.species_name, "Canis lupus")
            vespadelus = records.filter(name_id=24204).first()
            self.assertIsNotNone(vespadelus)
            self.assertEqual(vespadelus.species_name, "Vespadelus douglasorum")

    def test_nameId_collected_upload(self):
        """
        Test that if nameId is not provided it is collected from the species list
        :return:
        """
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id_and_species_name()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        # data
        csv_data = [
            ['NameId', 'Species Name', 'When', 'Latitude', 'Longitude'],
            ['', 'Canis lupus', '01/01/2017', -32.0, 115.75],  # "Canis lupus"
            ['', 'Vespadelus douglasorum', '02/02/2017', -33.0, 116.0]  # "Vespadelus douglasorum"
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        self.assertEquals(0, Record.objects.filter(dataset=dataset).count())
        url = reverse('api:dataset-upload', kwargs={'pk': dataset.pk})
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp
            }
            resp = client.post(url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            records = Record.objects.filter(dataset=dataset)
            self.assertEquals(records.count(), len(csv_data) - 1)
            for r in records:
                self.assertTrue(r.name_id > 0)
                self.assertIsNotNone(r.species_name)
            canis_lupus = records.filter(name_id=25454).first()
            self.assertIsNotNone(canis_lupus)
            self.assertEqual(canis_lupus.species_name, "Canis lupus")
            vespadelus = records.filter(name_id=24204).first()
            self.assertIsNotNone(vespadelus)
            self.assertEqual(vespadelus.species_name, "Vespadelus douglasorum")

    def test_species_name_collected_api_create(self):
        """
        Same as above: testing that the species name is collected when using the API create
        :return:
        """
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id_and_species_name()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        record_data = {
            'NameId': 25454,  # "Canis lupus"
            'Species Name': 'Chubby Bat',
            'When': '12/12/2017',
            'Latitude': -32.0,
            'Longitude': 115.756
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
        self.assertEqual(record.name_id, 25454)
        self.assertEqual(record.species_name, "Canis lupus")

    def test_species_name_collected_api_update(self):
        """
        Updating the nameId should update the species name
        :return:
        """
        # create record
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_name_id_and_species_name()
        dataset = self._create_dataset_with_schema(project, client, schema, dataset_type=Dataset.TYPE_SPECIES_OBSERVATION)
        record_data = {
            'NameId': 25454,  # "Canis lupus"
            'Species Name': 'Chubby Bat',
            'When': '12/12/2017',
            'Latitude': -32.0,
            'Longitude': 115.756
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
        self.assertEqual(record.name_id, 25454)
        self.assertEqual(record.species_name, "Canis lupus")
        # TODO: the species name in the data is not updated. Should we?
        self.assertEqual(record.data.get('Species Name'), 'Chubby Bat')

        # patch nameId
        new_name_id = 24204
        record_data['NameId'] = new_name_id
        expected_species_name = 'Vespadelus douglasorum'
        url = reverse('api:record-detail', kwargs={'pk': record.pk})
        payload = {
            'data': record_data
        }
        resp = client.patch(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        record.refresh_from_db()
        self.assertEqual(record.name_id, new_name_id)
        self.assertEqual(record.species_name, expected_species_name)


class TestCompositeSpeciesName(helpers.BaseUserTestCase):
    """
    Test for species name composed from Genus, Species, infra_rank, infra_name columns
    Paul Gioa specs from https://decbugs.com/view.php?id=6674:
    1. If the field Genus is present (or tagged with biosys type Genus) it takes priority over species_name
    2. If Genus is present, there must also be a field Species (or tagged with biosys type Species). If not, then revert to Species_Name (if present)
    3. If Genus and species present, then user may optionally specify Infraspecific_Rank and Infraspecific_Name (or fields tagged with Infraspecific_Rank and Infraspecific_Name)
    4. An aggregated species name is constructed by using something like (genus.strip() + " " + species.strip() + " " + infraspecific_rank.strip() + " " + infraspecific_rank).strip()
    """

    def assert_create_dataset(self, schema):
        try:
            return self._create_dataset_with_schema(
                self.project_1,
                self.custodian_1_client,
                schema,
                dataset_type=Dataset.TYPE_SPECIES_OBSERVATION
            )
        except Exception as e:
            self.fail('Species Observation dataset creation failed for schema {schema}'.format(
                schema=schema
            ))

    def test_genus_species_only_happy_path(self):
        schema_fields = [
            {
                "name": "Genus",
                "type": "string",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "Species",
                "type": "string",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "When",
                "type": "date",
                "constraints": helpers.REQUIRED_CONSTRAINTS,
                "format": "any",
                "biosys": {
                    'type': 'observationDate'
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "Longitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        dataset = self.assert_create_dataset(schema)
        records = [
            ['Genus', 'Species', 'When', 'Latitude', 'Longitude'],
            ['Canis', 'lupus', '2018-01-25', -32.0, 115.75]
        ]
        resp = self._upload_records_from_rows(records, dataset_pk=dataset.pk)
        print(resp.json())
