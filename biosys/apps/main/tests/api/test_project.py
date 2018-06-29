from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from rest_framework import status

from main.constants import DATUM_CHOICES
from main.models import Project, Site
from main.tests.api import helpers
from main.tests import factories


class TestPermissions(helpers.BaseUserTestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin, custodians
    Create: admin, data_engineer
    Delete: forbidden through API
    """

    def test_get(self):
        urls = [
            reverse('api:project-list'),
            reverse('api:project-detail', kwargs={'pk': self.project_1.pk})
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
        Only admin and data engineer from the program can create
        :return:
        """
        urls = [reverse('api:project-list')]
        data = {
            "program": self.program_1.pk,
            "name": "A new project for Unit test",
            "code": "T1234",
            "timezone": "Australia/Perth",
            "custodians": [self.custodian_1_user.pk]
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
                self.data_engineer_1_client
            ]
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
        admin + data_engineer for the program
        :return:
        """
        project = self.project_1
        self.assertIsNotNone(project)
        previous_code = project.code or ''
        updated_code = previous_code + "-updated"
        urls = [reverse('api:project-detail', kwargs={'pk': project.pk})]
        data = {
            "code": updated_code,
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_2_client
            ],
            "allowed": [self.admin_client, self.data_engineer_1_client]
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
        admin + data_engineer for the program
        :return:
        """
        project = self.project_2
        previous_code = project.code or ''
        updated_code = previous_code + "-updated"

        urls = [reverse('api:project-detail', kwargs={'pk': project.pk})]
        data = {
            "code": updated_code,
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_1_client
            ],
            "allowed": [self.admin_client, self.data_engineer_2_client]
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
        Allowed for admin and data engineer
        :return:
        """
        project = self.project_1
        urls = [reverse('api:project-detail', kwargs={'pk': project.pk})]
        data = None
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_2_client,
                self.custodian_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [self.admin_client, self.data_engineer_1_client]
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


class TestProjectSiteBulk(helpers.BaseUserTestCase):
    """
    Test the bulk upload/get end-point project/{pk}/sites
    """
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
        site = factories.SiteFactory.create(project=project)
        data = [
            {
                "id": site.pk,
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
        sites = factories.SiteFactory.create_batch(5, project=project)
        all_sites_ids = [s.pk for s in sites]
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
        sites_1 = factories.SiteFactory.create_batch(5, project=project)
        # test that we will not delete sites from project 2
        sites_2 = factories.SiteFactory.create_batch(5, project=self.project_2)
        previous_project2_sites_count = Site.objects.filter(project=self.project_2).count()
        self.assertTrue(previous_project2_sites_count > 0)
        payload = 'all'
        resp = client.delete(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Site.objects.filter(project=project).count(), 0)
        self.assertEqual(Site.objects.filter(project=self.project_2).count(), previous_project2_sites_count)


class TestProjectCustodians(helpers.BaseUserTestCase):

    def test_add_custodian(self):
        """
        Like project update: only data engineer
        """
        project = self.project_1
        custodian = self.custodian_1_user
        client = self.data_engineer_1_client
        self.assertTrue(project.is_custodian(custodian))

        new_user = G(get_user_model())
        self.assertFalse(project.is_custodian(new_user))
        # add this user
        url = reverse('api:project-detail', kwargs={'pk': project.pk})
        data = {
            'custodians': [custodian.pk, new_user.pk]
        }
        resp = client.patch(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(project.is_custodian(custodian))
        # new user is a custodian of the project
        self.assertTrue(project.is_custodian(new_user))