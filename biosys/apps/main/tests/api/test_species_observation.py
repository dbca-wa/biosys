import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.gis.geos import Point

from rest_framework import status
from rest_framework.test import APIClient

from main.models import Project, Site, Dataset
from main.tests.test_data_package import clone
from main.utils_auth import is_admin
from main.utils_species import HerbieFacade, NoSpeciesFacade
from main.tests.api import helpers


class TestPermissions(TestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin, custodians
    Create: admin, custodians
    Delete: admin, custodians
    """
    fixtures = [
        'test-groups',
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]
    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))  # faster password hasher
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
        self.project_1 = Project.objects.filter(title="Project1").first()
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
        self.project_2 = Project.objects.filter(title="Project2").first()
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
            reverse('api:speciesObservation-list'),
            reverse('api:speciesObservation-detail', kwargs={'pk': 1})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertEqual(
                    client.get(url).status_code,
                    status.HTTP_401_UNAUTHORIZED
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
        urls = [reverse('api:speciesObservation-list')]
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
        urls = [reverse('api:speciesObservation-list')]
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
        urls = [reverse('api:speciesObservation-detail', kwargs={'pk': rec.pk})]
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
        urls = [reverse('api:speciesObservation-detail', kwargs={'pk': rec.pk})]
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


class TestDataValidation(TestCase):
    fixtures = [
        'test-groups',
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))  # faster password hasher
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
        self.project_1 = Project.objects.filter(title="Project1").first()
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
        self.project_2 = Project.objects.filter(title="Project2").first()
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
        url = reverse('api:speciesObservation-list')
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
        url = reverse('api:speciesObservation-list')
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
        url = reverse('api:speciesObservation-list')
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
        url = reverse('api:speciesObservation-detail', kwargs={"pk": record.pk})
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
        url_post = reverse('api:speciesObservation-list')
        url_update = reverse('api:speciesObservation-detail', kwargs={'pk': record.pk})
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
        url_post = reverse('api:speciesObservation-list')
        url_update = reverse('api:speciesObservation-detail', kwargs={'pk': record.pk})
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
        url_post = reverse('api:speciesObservation-list')
        url_update = reverse('api:speciesObservation-detail', kwargs={'pk': record.pk})
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
        'test-groups',
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))  # faster password hasher
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
        self.project_1 = Project.objects.filter(title="Project1").first()
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
        self.project_2 = Project.objects.filter(title="Project2").first()
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
        url = reverse('api:speciesObservation-list')
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
        url = reverse('api:speciesObservation-detail', kwargs={"pk": record.pk})
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
        'test-groups',
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    species_facade_class = NoSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))  # faster password hasher
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
        self.project_1 = Project.objects.filter(title="Project1").first()
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
        self.project_2 = Project.objects.filter(title="Project2").first()
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
        url = reverse('api:speciesObservation-list')
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
        url = reverse('api:speciesObservation-detail', kwargs={"pk": record.pk})
        client = self.custodian_1_client
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_200_OK
        )
        self.assertEquals(ds.record_queryset.count(), count)
        self.assertEqual(ds.record_queryset.filter(species_name=name).count(), 1)


class TestNameID(TestCase):
    """
    Test that we retrieve the name id from the species facade
    """
    fixtures = [
        'test-groups',
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-species-observations'
    ]

    species_facade_class = helpers.LightSpeciesFacade

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))  # faster password hasher
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
        self.project_1 = Project.objects.filter(title="Project1").first()
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
        self.project_2 = Project.objects.filter(title="Project2").first()
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
            url = reverse('api:speciesObservation-list')
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
            url = reverse('api:speciesObservation-detail', kwargs={"pk": record.pk})
            client = self.custodian_1_client
            self.assertEqual(
                client.put(url, data, format='json').status_code,
                status.HTTP_200_OK
            )
            record.refresh_from_db()
            self.assertEqual(record.name_id, name_id)
