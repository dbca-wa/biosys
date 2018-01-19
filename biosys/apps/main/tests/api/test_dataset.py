import json

from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.utils.encoding import force_text
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Project, Site, Dataset
from main.tests.api import helpers
from main.tests.test_data_package import (
    clone,
    GENERIC_DATA_PACKAGE,
    LAT_LONG_OBSERVATION_DATA_PACKAGE,
    SPECIES_OBSERVATION_DATA_PACKAGE,
)
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))

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
            reverse('api:dataset-list'),
            reverse('api:dataset-detail', kwargs={'pk': 1})
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

    def test_options(self):
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

    def test_options_model_choices(self):
        """
        Test that the options request return model choices for dataset type
        :return:
        """
        url = reverse('api:dataset-list')
        client = self.admin_client
        resp = client.options(url)
        self.assertEquals(status.HTTP_200_OK, resp.status_code)
        data = resp.json()
        choices = data.get('actions', {}).get('POST', {}).get('type', {}).get('choices', None)
        self.assertTrue(choices)
        expected = [{'value': d[0], 'display_name': d[1]} for d in Dataset.TYPE_CHOICES]
        self.assertEquals(expected, choices)


class TestDataPackageValidation(TestCase):
    """
    Test that when create/update the datapackage validation is called
    """
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
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
        self.ds_1 = Dataset.objects.filter(name="Bats1", project=self.project_1).first()
        self.assertTrue(self.ds_1.is_custodian(self.custodian_1_user))

    def test_generic_create_happy_path(self):
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

    def test_observation_create_happy_path(self):
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

    def test_species_observation_create_happy_path(self):
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
            status.HTTP_400_BAD_REQUEST
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


class TestRecordsView(helpers.BaseUserTestCase):
    """
    Test API access to records from dataset
    """
    schema_fields = [
        {
            "name": "What",
            "type": "string",
            "constraints": helpers.REQUIRED_CONSTRAINTS
        },
        {
            "name": "When",
            "type": "date",
            "constraints": helpers.NOT_REQUIRED_CONSTRAINTS,
            "format": "any",
            "biosys": {
                'type': 'observationDate'
            }
        },
        {
            "name": "Where",
            "type": "string",
            "constraints": helpers.REQUIRED_CONSTRAINTS
        },
        {
            "name": "Who",
            "type": "string",
            "constraints": helpers.REQUIRED_CONSTRAINTS
        },
    ]

    def _more_setup(self):
        self.project = self.project_1
        self.client = self.custodian_1_client
        self.dataset = self._create_dataset_with_schema(self.project, self.client, self.schema_fields)
        self.url = reverse('api:dataset-records', kwargs={'pk': self.dataset.pk})

    def test_permissions_get(self):
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
        }
        for client in access['forbidden']:
            self.assertIn(
                client.get(self.url).status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
            )
        # authenticated
        for client in access['allowed']:
            self.assertEqual(
                client.get(self.url).status_code,
                status.HTTP_200_OK
            )

    def test_permissions_delete(self):
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.custodian_1_client, self.admin_client]
        }
        for client in access['forbidden']:
            self.assertIn(
                client.delete(self.url, data=[], format='json').status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
            )
        # authenticated
        for client in access['allowed']:
            self.assertEqual(
                client.delete(self.url, data=[], format='json').status_code,
                status.HTTP_204_NO_CONTENT
            )

    def test_not_allowed_methods(self):
        not_allowed = ['post', 'put', 'patch']
        for method in not_allowed:
            func = getattr(self.client, method)
            if callable(func):
                self.assertEqual(
                    func(self.url, data=None, format='json').status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED
                )

    def test_bulk_delete_list(self):
        # create some records
        record_pks = []
        for i in range(1, 4):
            record_data = {
                'What': str(i)
            }
            record_pks.append(self._create_record(self.client, self.dataset, record_data).pk)
        # verify list
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), len(record_pks))

        # delete the first 2
        deleted_pks = record_pks[:2]
        expected_remaining_pks = record_pks[2:]
        resp = self.client.delete(self.url, data=deleted_pks, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # ask the list again
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        existing_pks = [r['id'] for r in resp.json()]
        self.assertEqual(sorted(existing_pks), sorted(expected_remaining_pks))

    def test_bulk_delete_all(self):
        # create some records
        record_pks = []
        for i in range(1, 4):
            record_data = {
                'What': str(i)
            }
            record_pks.append(self._create_record(self.client, self.dataset, record_data).pk)
        # verify list
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), len(record_pks))

        # delete them all
        resp = self.client.delete(self.url, data='all', format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # ask the list again
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

class TestDatasetRecordsSearchAndOrdering(TestCase):
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites',
        'test-datasets',
        'test-generic-records'
    ]

    def setUp(self):
        password = 'password'
        user_model = get_user_model()
        self.admin_user = user_model.objects.filter(username="admin").first()
        self.assertIsNotNone(self.admin_user)
        self.assertTrue(is_admin(self.admin_user))
        self.admin_user.set_password(password)
        self.admin_user.save()
        self.assertTrue(self.client.login(username=self.admin_user.username, password=password))

    def test_server_side_search(self):
        # this dataset has records in it
        dataset = Dataset.objects.all()[2]

        self.assertIsNotNone(dataset)

        self.assertEqual(dataset.record_queryset.count(), 10)

        url = reverse('api:dataset-records', kwargs={'pk': dataset.pk})

        # test fetch all records for dataset
        resp = self.client.get(url, format='json')

        self.assertEqual(resp.status_code, 200)

        json_response = json.loads(force_text(resp.content))

        self.assertEqual(len(json_response), 10)

        # test fetching records in dataset using specific search term specific term
        resp = self.client.get(url + '?search=Chalino', format='json')

        self.assertEqual(resp.status_code, 200)

        json_response = json.loads(force_text(resp.content))

        self.assertEqual(len(json_response), 2)

    def test_server_side_ordering(self):
        # this dataset has records in it
        dataset = Dataset.objects.all()[2]

        self.assertIsNotNone(dataset)

        self.assertEqual(dataset.record_queryset.count(), 10)

        url = reverse('api:dataset-records', kwargs={'pk': dataset.pk})

        # check unordered request is not ordered by family
        resp = self.client.get(url, format='json')

        self.assertEqual(resp.status_code, 200)

        json_response = json.loads(force_text(resp.content))

        self.assertEqual(len(json_response), 10)

        record_families = [record['data']['Family'] for record in json_response]

        self.assertNotEqual(record_families, sorted(record_families))

        # check is request ordered by family is ordered by family in alphabetical order
        resp = self.client.get(url + '?ordering=Family', format='json')

        self.assertEqual(resp.status_code, 200)

        json_response = json.loads(force_text(resp.content))

        self.assertEqual(len(json_response), 10)

        record_families = [record['data']['Family'] for record in json_response]

        self.assertEqual(record_families, sorted(record_families))

        # check is request ordered by family in descending order is ordered by family in reverse alphabetical order
        resp = self.client.get(url + '?ordering=-Family', format='json')

        self.assertEqual(resp.status_code, 200)

        json_response = json.loads(force_text(resp.content))

        self.assertEqual(len(json_response), 10)

        record_families = [record['data']['Family'] for record in json_response]

        self.assertEqual(record_families, list(reversed(sorted(record_families))))
