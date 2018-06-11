from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django_dynamic_fixture import G
from rest_framework import status
from rest_framework.test import APIClient

from main.constants import DATUM_CHOICES
from main.models import Project, Site
from main.tests.api import helpers
from main.utils_auth import is_admin


class TestPermissions(TestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin, custodians
    Create: admin
    Delete: forbidden through API
    """
    fixtures = [
        'test-users',
        'test-projects'
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
        self.assertTrue(self.project_1.is_custodian(self.custodian_1_user))

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(name="Project2").first()
        self.assertTrue(self.project_2.is_custodian(self.custodian_2_user))
        self.assertFalse(self.project_1.is_custodian(self.custodian_2_user))

        self.readonly_user = User.objects.filter(username="readonly").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.assertFalse(self.project_2.is_custodian(self.readonly_user))
        self.assertFalse(self.project_1.is_custodian(self.readonly_user))
        self.readonly_user.set_password(password)
        self.readonly_user.save()
        self.readonly_client = APIClient()
        self.assertTrue(self.readonly_client.login(username=self.readonly_user.username, password=password))

        self.anonymous_client = APIClient()

    def test_get(self):
        urls = [
            reverse('api:project-list'),
            reverse('api:project-detail', kwargs={'pk': 1})
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
        Only admin can create
        :return:
        """
        urls = [reverse('api:project-list')]
        data = {
            "name": "A new project for Unit test",
            "code": "T1234",
            "timezone": "Australia/Perth",
            "custodians": [self.custodian_1_user.pk]
        }
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.admin_client, self.readonly_client, self.custodian_1_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                # Name must me unique
                data['name'] += '1'
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )

    def test_bulk_create(self):
        """
        Bulk create is not possible for project
        :return:
        """
        urls = [reverse('api:project-list')]
        data = [
            {
                "name": "Project1 for Unit test",
                "code": "T1234",
                "timezone": "Australia/Perth"
            },
            {
                "name": "Project2 for Unit test",
                "code": "T1234",
                "timezone": "Australia/Perth"
            },
        ]
        access = {
            "forbidden": [self.admin_client, self.anonymous_client, self.readonly_client, self.custodian_1_client],
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
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )

    def test_update1(self):
        """
        admin + custodian of project for project 1
        :return:
        """
        project = self.project_1
        self.assertIsNotNone(project)
        previous_code = project.code
        updated_code = previous_code + "-updated"
        urls = [reverse('api:project-detail', kwargs={'pk': project.pk})]
        data = {
            "code": updated_code,
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
                project.code = previous_code
                project.save()
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                project.refresh_from_db()
                self.assertEqual(project.code, updated_code)

    def test_update2(self):
        """
        admin + custodian of project for project 2
        :return:
        """
        project = self.project_2
        previous_code = project.code
        updated_code = previous_code + "-updated"

        urls = [reverse('api:project-detail', kwargs={'pk': project.pk})]
        data = {
            "code": updated_code,
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_1_client],
            "allowed": [self.admin_client, self.custodian_2_client]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                project.code = previous_code
                project.save()
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                project.refresh_from_db()
                self.assertEqual(project.code, updated_code)

    def test_delete(self):
        """
        Allowed for admin and custodian
        :return:
        """
        project = self.project_1
        urls = [reverse('api:project-detail', kwargs={'pk': project.pk})]
        data = None
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.custodian_1_client, self.admin_client]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            project.save()
            count = Project.objects.count()
            for url in urls:
                self.assertEqual(
                    client.delete(url, data, format='json').status_code,
                    status.HTTP_204_NO_CONTENT
                )
                self.assertTrue(Project.objects.count(), count - 1)

    def test_options(self):
        urls = [
            reverse('api:project-list'),
            reverse('api:project-detail', kwargs={'pk': 1})
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
        Test that the options request return model choices
        :return:
        """
        url = reverse('api:project-list')
        client = self.admin_client
        resp = client.options(url)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = resp.json()
        datum_choices = data.get('actions', {}).get('POST', {}).get('datum', {}).get('choices', None)
        self.assertTrue(datum_choices)
        expected = [{'value': d[0], 'display_name': d[1]} for d in DATUM_CHOICES]
        self.assertEqual(expected, datum_choices)


class TestProjectSiteBulk(TestCase):
    """
    Test the bulk upload/get end-point project/{pk}/sites
    """
    fixtures = [
        'test-users',
        'test-projects',
        'test-sites'
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
        self.project_1 = Project.objects.filter(name="Project1").first()
        self.site_1 = Site.objects.filter(code="Site1").first()
        self.assertTrue(self.site_1.is_custodian(self.custodian_1_user))

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(name="Project2").first()
        self.site_2 = Site.objects.filter(code="Site2").first()
        self.assertTrue(self.site_2.is_custodian(self.custodian_2_user))
        self.assertFalse(self.site_1.is_custodian(self.custodian_2_user))

        self.readonly_user = User.objects.filter(username="readonly").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.assertFalse(self.site_2.is_custodian(self.readonly_user))
        self.assertFalse(self.site_1.is_custodian(self.readonly_user))
        self.readonly_user.set_password(password)
        self.readonly_user.save()
        self.readonly_client = APIClient()
        self.assertTrue(self.readonly_client.login(username=self.readonly_user.username, password=password))

        self.anonymous_client = APIClient()

    def test_permissions_read(self):
        """
        Get: everyone authenticated
        """
        project = self.project_1
        urls = [
            reverse('api:project-sites', kwargs={'pk': project.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.get(url, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.get(url, format='json').status_code,
                    status.HTTP_200_OK
                )

    def test_permissions_post(self):
        """
        Custodian and admin
        """
        project = self.project_1
        urls = [
            reverse('api:project-sites', kwargs={'pk': project.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.custodian_1_client, self.admin_client]
        }
        data = [
            {
                "code": "AAAA"
            },
            {
                "code": "BBBB"
            }
        ]
        for client in access['forbidden']:
            for url in urls:
                # code must be unique
                for site in data:
                    site['code'] += '1'
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        for client in access['allowed']:
            for url in urls:
                # code must be unique
                for site in data:
                    site['code'] += '1'
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )

    def test_permissions_delete(self):
        """
        Bulk delete is possible for custodian as long as we provide a list of ids
        :return:
        """
        project = self.project_1
        urls = [
            reverse('api:project-sites', kwargs={'pk': project.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.custodian_1_client, self.admin_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url, data=[], format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED]
                )
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.delete(url, data=[], format='json').status_code,
                    status.HTTP_204_NO_CONTENT
                )

    def test_bulk_update_forbidden(self):
        project = self.project_1
        urls = [
            reverse('api:project-sites', kwargs={'pk': project.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client, self.custodian_1_client,
                          self.admin_client],
            "allowed": []
        }
        site = self.site_1
        data = [
            {
                "id": self.site_1.pk,
                "code": site.code + '-uTest1'
            }
        ]
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.put(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED]
                )
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED]
                )
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.put(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )

    def test_bulk_post(self):
        project = self.project_1
        url = reverse('api:project-sites', kwargs={'pk': project.pk})
        # delete all sites
        Site.objects.filter(project=project).delete()
        self.assertEqual(0, Site.objects.filter(project=project).count())
        site_1 = {
            "code": "AAAA",
            "name": "Site A",
            "description": "description A",
            "attributes": {
                "color": "blue",
                "area": 12
            }
        }
        site_2 = {
            "code": "BBBB",
            "name": "Site B",
            "description": "description B",
            "attributes": {
                "color": "red",
                "area": 100
            }
        }
        data = [
            site_1,
            site_2
        ]

        client = self.custodian_1_client
        resp = client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # the response should include the 2 sites
        self.assertEqual(len(resp.data), len(data))
        # check db
        self.assertEqual(Site.objects.filter(project=project).count(), len(data))
        sdb_1 = Site.objects.filter(project=project, code=site_1['code']).first()
        self.assertIsNotNone(sdb_1)
        self.assertEqual(sdb_1.name, site_1['name'])
        self.assertEqual(sdb_1.description, site_1['description'])
        self.assertEqual(sdb_1.attributes, site_1['attributes'])

        sdb_2 = Site.objects.filter(project=project, code=site_2['code']).first()
        self.assertIsNotNone(sdb_2)
        self.assertEqual(sdb_2.name, site_2['name'])
        self.assertEqual(sdb_2.description, site_2['description'])
        self.assertEqual(sdb_2.attributes, site_2['attributes'])

    def test_bulk_delete_happy_path(self):
        """
        Test the delete with an array of ids in the payload
        """
        project = self.project_1
        client = self.custodian_1_client
        url = reverse('api:project-sites', kwargs={'pk': project.pk})
        all_sites_ids = [s.pk for s in Site.objects.filter(project=project)]
        self.assertTrue(len(all_sites_ids) > 1)
        to_delete = all_sites_ids[:2]
        resp = client.delete(url, data=to_delete, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        sites = Site.objects.filter(project=project)
        self.assertEqual(sites.count(), len(all_sites_ids) - len(to_delete))
        for pk in to_delete:
            self.assertIsNone(Site.objects.filter(pk=pk).first())

    def test_delete_all(self):
        """
        Test that is the request payload as 'all' all the sites for the project are deleted
        """
        project = self.project_1
        client = self.custodian_1_client
        url = reverse('api:project-sites', kwargs={'pk': project.pk})
        self.assertTrue(Site.objects.filter(project=project).count() > 0)
        # test that we will not delete sites from project 2
        previous_project2_sites_count = Site.objects.filter(project=self.project_2).count()
        self.assertTrue(previous_project2_sites_count > 0)
        payload = 'all'
        resp = client.delete(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Site.objects.filter(project=project).count(), 0)
        self.assertEqual(Site.objects.filter(project=self.project_2).count(), previous_project2_sites_count)


class TestProjectCustodians(TestCase):
    fixtures = [
        'test-users',
        'test-projects'
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
        self.project_1 = Project.objects.filter(name="Project1").first()
        self.assertTrue(self.project_1.is_custodian(self.custodian_1_user))

        self.custodian_2_user = User.objects.filter(username="custodian2").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.custodian_2_user.set_password(password)
        self.custodian_2_user.save()
        self.custodian_2_client = APIClient()
        self.assertTrue(self.custodian_2_client.login(username=self.custodian_2_user.username, password=password))
        self.project_2 = Project.objects.filter(name="Project2").first()
        self.assertTrue(self.project_2.is_custodian(self.custodian_2_user))
        self.assertFalse(self.project_1.is_custodian(self.custodian_2_user))

        self.readonly_user = User.objects.filter(username="readonly").first()
        self.assertIsNotNone(self.custodian_2_user)
        self.assertFalse(self.project_2.is_custodian(self.readonly_user))
        self.assertFalse(self.project_1.is_custodian(self.readonly_user))
        self.readonly_user.set_password(password)
        self.readonly_user.save()
        self.readonly_client = APIClient()
        self.assertTrue(self.readonly_client.login(username=self.readonly_user.username, password=password))

        self.anonymous_client = APIClient()

    def test_add_custodian(self):
        project = self.project_1
        custodian = self.custodian_1_user
        client = self.custodian_1_client
        self.assertTrue(project.is_custodian(custodian))

        new_user = G(get_user_model())
        self.assertFalse(project.is_custodian(new_user))
        # add this user
        url = reverse('api:project-detail', kwargs={'pk': project.pk})
        data = {
            'custodians': [custodian.pk, new_user.pk]
        }
        resp = client.patch(url, data, format='json')
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(project.is_custodian(custodian))
        # new user is a custodian of the project
        self.assertTrue(project.is_custodian(new_user))

    def test_remove_custodian(self):
        """
        A custodian removes itself from the list of custodian.
        It cannot add itself back! Only an admin can do that.
        :return:
        """
        project = self.project_1
        custodian = self.custodian_1_user
        client = self.custodian_1_client
        self.assertTrue(project.is_custodian(custodian))
        url = reverse('api:project-detail', kwargs={'pk': project.pk})
        expected_custodians = [custodian.pk]
        resp = client.get(url)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertEqual(expected_custodians, resp.json()['custodians'])

        # clear custodians list
        # custodians can't be empty
        data = {
            'custodians': []
        }
        resp = client.patch(url, data, format='json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

        # add someone else
        data = {
            'custodians': [self.custodian_2_user.pk]
        }
        resp = client.patch(url, data, format='json')
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        resp = client.get(url)
        expected_custodians = data['custodians']
        self.assertEqual(expected_custodians, resp.json()['custodians'])
        # no more a custodian
        self.assertFalse(project.is_custodian(custodian))

        # oops! try to get back on board
        data = {
            'custodians': [custodian.pk]
        }
        resp = client.patch(url, data, format='json')
        # can't
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )
        self.assertFalse(project.is_custodian(custodian))

        # only admin can do it now
        client = self.admin_client
        data = {
            'custodians': [custodian.pk]
        }
        resp = client.patch(url, data, format='json')
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        self.assertTrue(project.is_custodian(custodian))
