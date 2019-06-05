from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient
from freezegun import freeze_time

from main.tests.api import helpers


class TestAuth(helpers.BaseUserTestCase):

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def test_token_auth_end_point(self):
        """
        Test that when hitting the auth_token end point we receive a token
        :return:
        """
        client = APIClient()
        # request token
        url = reverse('api:auth-token')
        user = self.readonly_user
        self.assertTrue(user.check_password('password'))
        data = {
            'username': "readonly",
            "password": "password"
        }
        resp = client.post(url, data=data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # check that we have a token
        self.assertTrue('token' in resp.data)
        token = resp.data.get('token')
        self.assertTrue(token)

    @override_settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.MD5PasswordHasher',),
                       REST_FRAMEWORK_TEST_SETTINGS=helpers.REST_FRAMEWORK_TEST_SETTINGS)
    def test_token_valid(self):
        """
        Test that the token received can be used for authentication
        :return:
        """
        client = APIClient()
        user = self.readonly_user
        self.assertTrue(user.check_password('password'))
        url = reverse('api:auth-token')
        data = {
            'username': user.username,
            "password": "password"
        }
        resp = client.post(url, data=data, format='json')
        token = resp.data.get('token')
        self.assertTrue(token)

        # can't get dataset list without token
        url = reverse('api:dataset-list')
        resp = client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # set credential token
        client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        resp = client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class TestUserAuthThrottling(helpers.BaseUserTestCase):
    """
    Use case: Prevent brute force authentication by preventing the API user issuing too many auth-token request
    """

    def test_brute_force(self):
        """
        test that a hacker sending auth request with wrong password will be blocked after n attempts
        :return:
        """
        rate = '6/hour'
        drf_settings = settings.REST_FRAMEWORK
        drf_settings['DEFAULT_THROTTLE_RATES']['auth'] = rate
        with override_settings(REST_FRAMEWORK=drf_settings):
            max_attempt = 6
            client = APIClient()
            # request token
            url = reverse('api:auth-token')
            user = self.readonly_user
            self.assertTrue(user.check_password('password'))
            data = {
                'username': "readonly",
                "password": "bruteforce"
            }
            # Hacking attempt should return HTTP_400_BAD_REQUEST while attempts < throttle rate
            with freeze_time("2018-05-29 12:00:00", tick=True):
                for attempt in range(max_attempt):
                    resp = client.post(url, data=data, format='json')
                    self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
                # next attempt should return a HTTP_429_TOO_MANY_REQUESTS
                resp = client.post(url, data=data, format='json')
                self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

            # let's simulate a 30 min jump in time. Should still return HTTP_429_TOO_MANY_REQUESTS
            with freeze_time("2018-05-29 12:30:00", tick=True):
                resp = client.post(url, data=data, format='json')
                self.assertEqual(resp.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

            # let's  jump more than one hour in time. Should be back at returning HTTP_400_BAD_REQUEST
            with freeze_time("2018-05-29 13:00:05", tick=True):
                resp = client.post(url, data=data, format='json')
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
