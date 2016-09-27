from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Project, Site, Dataset
from main.utils_auth import is_admin

from main.tests.test_data_package import (
    clone,
    GENERIC_DATA_PACKAGE,
    LAT_LONG_OBSERVATION_DATA_PACKAGE,
    SPECIES_OBSERVATION_DATA_PACKAGE,
)


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
    ]

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))  # faster password hasher
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))

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
            reverse('api:dataset-list'),
            reverse('api:dataset-detail', kwargs={'pk': 1})
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
        # authenticated
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
        project = self.project_1
        urls = [reverse('api:dataset-list')]
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': self.ds_1.data_package
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
                # name must be unique
                data['name'] += '1'
                count = Dataset.objects.count()
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(Dataset.objects.count(), count + 1)

    def test_bulk_create_forbidden(self):
        """
        Bulk create is not authorized for Datasets
        :return:
        """
        """
        Cannot create multiple dataset
        :return:
        """
        project = self.project_1
        urls = [reverse('api:dataset-list')]
        data = [
            {
                "name": "New1 for Unit test",
                "type": Dataset.TYPE_GENERIC,
                "project": project.pk,
                'data_package': self.ds_1.data_package
            },
            {
                "name": "New2 for Unit test",
                "type": Dataset.TYPE_GENERIC,
                "project": project.pk,
                'data_package': self.ds_1.data_package
            }
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client, self.admin_client,
                          self.custodian_1_client],
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
                # name must be unique
                for ds in data:
                    ds['name'] += '1'
                count = Dataset.objects.count()
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(Dataset.objects.count(), count + 1)

    def test_update(self):
        """
        admin + custodian of project for site 1
        :return:
        """
        ds = self.ds_1
        previous_name = ds.name
        updated_name = previous_name + "-updated"
        urls = [reverse('api:dataset-detail', kwargs={'pk': ds.pk})]
        data = {
            "name": updated_name,
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
                ds.name = previous_name
                ds.save()
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                ds.refresh_from_db()
                self.assertEqual(ds.name, updated_name)

    def test_delete(self):
        """
        Currently admin + custodian
        :return:
        """
        ds = self.ds_1
        urls = [reverse('api:dataset-detail', kwargs={'pk': ds.pk})]
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
                ds.save()
                count = Dataset.objects.count()
                self.assertEqual(
                    client.delete(url, data, format='json').status_code,
                    status.HTTP_204_NO_CONTENT
                )
                self.assertTrue(Dataset.objects.count(), count - 1)


class TestDataPackageValidation(TestCase):
    """
    Test that when create/update the datapackage validation is called
    """
    fixtures = [
        'test-groups',
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
    ]

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',))  # faster password hasher
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))

    def test_generic_happy_path(self):
        data_package = clone(GENERIC_DATA_PACKAGE)

        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': data_package
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )

    def test_observation_happy_path(self):
        data_package = clone(LAT_LONG_OBSERVATION_DATA_PACKAGE)

        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_OBSERVATION,
            "project": project.pk,
            'data_package': data_package
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )

    def test_species_observation_happy_path(self):
        data_package = clone(SPECIES_OBSERVATION_DATA_PACKAGE)

        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_SPECIES_OBSERVATION,
            "project": project.pk,
            'data_package': data_package
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )

    def test_create_none_error(self):
        """
        data package cannot be None
        :return:
        """
        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': None
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_update_none_error(self):
        """
        data package cannot be None
        :return:
        """
        ds = self.ds_1
        url = reverse('api:dataset-detail', kwargs={"pk": ds.pk})
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': None
        }
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_create_empty_error(self):
        """
        create
        data package cannot be empty
        :return:
        """
        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': {}
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_update_empty_error(self):
        """
        update
        data package cannot be empty
        :return:
        """
        ds = self.ds_1
        url = reverse('api:dataset-detail', kwargs={"pk": ds.pk})
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': {}
        }
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_no_schema_error(self):
        data_package = clone(GENERIC_DATA_PACKAGE)
        data_package['resources'][0]['schema'] = {}
        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.custodian_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': {}
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )


