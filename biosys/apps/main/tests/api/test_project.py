from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from main.models import Project


class TestPermissions(TestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin, custodians
    Create: admin
    Delete: admin
    """
    fixtures = ['test-users', 'test-projects']

    def setUp(self):
        self.anonymous_client = APIClient()
        self.readonly_client = APIClient()
        self.assertTrue(self.readonly_client.login(username='readonly', password='password'))
        self.custodian_client = APIClient()
        self.assertTrue(self.readonly_client.login(username='custodian', password='password'))
        self.admin_client = APIClient()
        self.assertTrue(self.admin_client.login(username='admin', password='password'))

        p = Project.objects.first()
        u = User.objects.filter(username='custodian').first()
        self.assertTrue(p.is_custodian(u))
        self.assertFalse(p.is_custodian(User.objects.filter(username='readonly').first()))

    def test_get(self):
        urls = [
            reverse('api:project-list'),
            reverse('api:project-detail', kwargs={'pk': 1})
        ]
        # anonymous
        client = self.anonymous_client
        for url in urls:
            self.assertEqual(
                client.get(url).status_code,
                status.HTTP_401_UNAUTHORIZED
            )
        # authenticated
        client = self.readonly_client
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
        url = reverse('api:project-list')
        data = {
            "title": "A new project for Unit test",
            "code": "T1234",
            "timezone": "Australia/Perth"
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_client],
            "allowed": [self.admin_client]
        }
        for client in access['forbidden']:
            self.assertIn(
                client.post(url, data, format='json').status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
            )

        for client in access['allowed']:
            self.assertEqual(
                client.post(url, data, format='json').status_code,
                status.HTTP_201_CREATED
            )

    def test_update(self):
        """
        admin + custodian
        :return:
        """
        print('test_update')
        proj = Project.objects.first()
        self.assertIsNotNone(proj)
        previous_code = proj.code
        updated_code = previous_code + "-updated"
        url = reverse('api:project-detail', kwargs={'pk': proj.pk})
        data = {
            "code": updated_code,
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client],
            "allowed": [self.admin_client, self.custodian_client]
        }
        print('forbidden')
        for client in access['forbidden']:
            print('client', client)
            self.assertIn(
                client.patch(url, data, format='json').status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
            )

        print('allowed')
        for client in access['allowed']:
            print('client', client)
            proj.code = previous_code
            proj.save()
            self.assertEqual(
                client.patch(url, data, format='json').status_code,
                status.HTTP_200_OK
            )
            proj.refresh_from_db()
            self.assertEqual(proj.code, updated_code)
