import six

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class TestProjects(TestCase):
    """
    Project are ReadOnly
    """
    fixtures = ['test-users', 'test-data']

    def setUp(self):
        self.anonymous_client = APIClient()
        self.authenticated_client = APIClient()
        self.assertTrue(self.authenticated_client.login(username='normal', password='password'))
        self.admin_client = APIClient()
        self.assertTrue(self.admin_client.login(username='admin', password='password'))

    def test_read(self):
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
        client = self.authenticated_client
        for url in urls:
            self.assertEqual(
                client.get(url).status_code,
                status.HTTP_200_OK
            )

    def test_not_write(self):
        """
        Verify allow methods in header is just read only
        :return:
        """
        client = self.authenticated_client
        resp = client.get(reverse('api:project-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        allow = resp.get('allow')
        self.assertEqual(allow, 'GET, HEAD, OPTIONS')

