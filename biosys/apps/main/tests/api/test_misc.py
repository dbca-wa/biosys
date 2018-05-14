from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import TestCase
from django_dynamic_fixture import G
from rest_framework import status
from rest_framework.test import APIClient

from main.models import Project, Site
from main.tests.api import helpers


class TestWhoAmI(TestCase):
    def setUp(self):
        self.url = reverse('api:whoami')

    def test_get(self):
        anonymous = APIClient()
        client = anonymous
        self.assertEqual(
            client.get(self.url).status_code,
            status.HTTP_200_OK
        )

        user = G(get_user_model())
        user.set_password('password')
        user.save()
        client = APIClient()
        self.assertTrue(client.login(username=user.username, password='password'))
        resp = client.get(self.url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK
        )
        # test that the response contains username, first and last name and email at least and the id
        data = resp.json()
        self.assertEqual(user.username, data['username'])
        self.assertEqual(user.first_name, data['first_name'])
        self.assertEqual(user.last_name, data['last_name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.id, data['id'])

        # test that the password is not in the returned fields
        self.assertFalse('password' in data)

    def test_not_allowed_methods(self):
        user = G(get_user_model())
        user.set_password('password')
        user.save()
        client = APIClient()
        self.assertTrue(client.login(username=user.username, password='password'))
        self.assertEqual(
            client.post(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            client.put(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            client.patch(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


class TestStatistics(TestCase):
    def setUp(self):
        self.url = reverse('api:statistics')

    def test_get(self):
        anonymous = APIClient()
        client = anonymous
        self.assertIn(
            client.get(self.url).status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

        user = G(get_user_model())
        user.set_password('password')
        user.save()
        client = APIClient()
        self.assertTrue(client.login(username=user.username, password='password'))
        resp = client.get(self.url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK
        )
        # expected response with no data
        expected = {
            'projects': {'total': 0},
            'datasets': {
                'total': 0,
                'generic': {'total': 0},
                'observation': {'total': 0},
                'speciesObservation': {'total': 0},
            },
            'records': {
                'total': 0,
                'generic': {'total': 0},
                'observation': {'total': 0},
                'speciesObservation': {'total': 0},
            },
            'sites': {'total': 0},
        }
        self.assertEquals(expected, resp.json())

        # create one project
        project = G(Project)
        self.assertEquals(1, Project.objects.count())
        expected['projects']['total'] = 1
        resp = client.get(self.url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK
        )
        self.assertEquals(expected, resp.json())

        # create some sites
        count = 3
        for i in range(0, count):
            G(Site, project=project)
        expected['sites']['total'] = count
        resp = client.get(self.url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK
        )
        self.assertEquals(expected, resp.json())

    def test_not_allowed_methods(self):
        user = G(get_user_model())
        user.set_password('password')
        user.save()
        client = APIClient()
        self.assertTrue(client.login(username=user.username, password='password'))
        self.assertEqual(
            client.post(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            client.put(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            client.patch(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )


class TestSpecies(TestCase):
    # set the species list to be the testing one
    species_facade_class = helpers.LightSpeciesFacade

    def setUp(self):
        from main.api.views import SpeciesMixin
        SpeciesMixin.species_facade_class = self.species_facade_class

        self.url = reverse('api:species')

    def test_get(self):
        anonymous = APIClient()
        client = anonymous
        self.assertEqual(
            client.get(self.url).status_code,
            status.HTTP_200_OK
        )

        user = G(get_user_model())
        user.set_password('password')
        user.save()
        client = APIClient()
        self.assertTrue(client.login(username=user.username, password='password'))
        resp = client.get(self.url)
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK
        )

    def test_not_allowed_methods(self):
        user = G(get_user_model())
        user.set_password('password')
        user.save()
        client = APIClient()
        self.assertTrue(client.login(username=user.username, password='password'))
        self.assertEqual(
            client.post(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            client.put(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            client.patch(self.url, {}).status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
