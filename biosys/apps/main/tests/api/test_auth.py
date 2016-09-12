import base64
import six

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class TestBasicAuth(TestCase):
    """
    Basic Auth is currently turned on.
    """
    fixtures = ['test-users']

    def test_basic_auth(self):
        client = APIClient()
        url = reverse('api:dataset-list')
        resp = client.get(url)
        self.assertEquals(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        user = User.objects.filter(username="normal").first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('password'))

        # build the Authorization Header for basic for user=normaluser password=password
        basic_key = base64.b64encode(six.b("normal:password")).decode('utf-8')
        client.credentials(HTTP_AUTHORIZATION='Basic ' + basic_key)
        resp = client.get(url)
        self.assertEquals(resp.status_code, status.HTTP_200_OK)

    def test_token_auth_end_point(self):
        """
        Test that when hitting the auth_token end point we receive a token
        :return:
        """
        client = APIClient()
        # request token
        url = reverse('api:auth_token')
        user = User.objects.filter(username="normal").first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('password'))
        data = {
            'username': "normal",
            "password": "password"
        }
        resp = client.post(url, data=data, format='json')
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
        # check that we have a token
        self.assertTrue('token' in resp.data)
        token = resp.data.get('token')
        self.assertTrue(token)

    def test_token_valid(self):
        """
        Test that the token received can be used for authentication
        :return:
        """
        client = APIClient()
        url = reverse('api:auth_token')
        data = {
            'username': "normal",
            "password": "password"
        }
        resp = client.post(url, data=data, format='json')
        token = resp.data.get('token')
        self.assertTrue(token)

        # can't get dataset list without token
        url = reverse('api:dataset-list')
        resp = client.get(url)
        self.assertEquals(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # set credential token
        client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        resp = client.get(url)
        self.assertEquals(resp.status_code, status.HTTP_200_OK)

    def test_session_auth(self):
        client = APIClient()
        # can't get dataset list without login
        url = reverse('api:dataset-list')
        resp = client.get(url)
        self.assertEquals(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # The login of the client uses the session mechanism
        client.login(username="normal", password="password")
        resp = client.get(url)
        self.assertEquals(resp.status_code, status.HTTP_200_OK)
