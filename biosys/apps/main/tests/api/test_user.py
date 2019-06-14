import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from main.tests import factories
from main.tests.api import helpers

User = get_user_model()


class TestPermissions(helpers.BaseUserTestCase):
    """
    Test Permissions
    Get: admin or data_engineer
    Update: admin or user itself
    Create: admin
    Delete: forbidden through API
    """

    def test_get(self):
        urls = [
            reverse('api:user-list'),
            reverse('api:user-detail', kwargs={'pk': self.readonly_user.pk})
        ]
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
            ],
            "allowed": [
                self.admin_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client
            ]
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

    @override_settings(ALLOW_PUBLIC_REGISTRATION=False)
    def test_create(self):
        """
        By default only admin can create.
        But if the site settings is set to allow public registration (see test_create_public)
        :return:
        """
        urls = [reverse('api:user-list')]
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password"
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_1_client],
            "allowed": [self.admin_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    def test_create_public(self):
        """
        Test that if the site is set to allow public registration an anonymous user can register
        :return:
        """
        urls = [reverse('api:user-list')]
        data = {
            "username": "public",
            "email": "newuser@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe"
        }
        access = {
            "forbidden": [self.readonly_client, self.custodian_1_client],
            "allowed": [self.admin_client, self.anonymous_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                # we need to provide a unique username by adding an 'x' every time
                data['username'] += 'x'
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True, SEND_REGISTRATION_CONF=True,
                       REGISTRATION_EMAIL_SUBJECT='registration', REGISTRATION_EMAIL_FROM='hello',
                       REGISTRATION_EMAIL_BODY='body')
    def test_create_public_with_email_conf(self):
        """
        Test that if the site is set to allow public registration and email confirmation
        a confirmation is sent
        :return:
        """
        url = reverse('api:user-list')
        client = APIClient()

        payload = {
            "username": "public",
            "email": "newuser@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe"
        }
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('registration' in mail.outbox[0].subject)
        self.assertTrue('body' in mail.outbox[0].body)

    def test_bulk_create(self):
        """
        Bulk create is not possible
        :return:
        """
        urls = [reverse('api:user-list')]
        data = [
            {
                "username": "newuser1",
                "email": "newuser1@example.com",
                "password": "password"
            },
            {
                "username": "newuser2",
                "email": "newuser2@example.com",
                "password": "password"
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

    def test_patch(self):
        """
        admin only or user
        :return:
        """
        user = self.custodian_1_user
        user_client = self.custodian_1_client
        urls = [reverse('api:user-detail', kwargs={'pk': user.pk})]
        new_first_name = "New First Name"
        data = {
            "first_name": new_first_name,
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, user_client]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                new_first_name += '1'
                data['first_name'] = new_first_name
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                user.refresh_from_db()
                self.assertEqual(user.first_name, new_first_name)

    def test_delete(self):
        """
        Currently forbidden through API
        :return:
        """
        user = self.custodian_1_user
        urls = [reverse('api:user-detail', kwargs={'pk': user.pk})]
        data = None
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_1_client, self.admin_client,
                          self.custodian_2_client],
            "allowed": []
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.delete(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )

    def test_options(self):
        urls = [
            reverse('api:user-list'),
            reverse('api:user-detail', kwargs={'pk': 1})
        ]
        access = {
            "forbidden": [
                self.anonymous_client,
            ],
            "allowed": [
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client,
                self.admin_client
            ]
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


class TestFiltering(helpers.BaseUserTestCase):

    def test_project_custodians(self):
        """
        Test that we can filter users to obtain only the custodians of a project.
        """
        user_1, user_2 = factories.UserFactory.create_batch(2)
        project = self.project_1
        project.custodians.add(user_1)
        expected_users = [self.custodian_1_user, user_1]
        for user in expected_users:
            self.assertTrue(project.is_custodian(user))
        self.assertFalse(project.is_custodian(user_2))

        # test by project id
        url = reverse('api:user-list')
        # since june 2019. Only admin or data_engineer can GET users.
        client = self.data_engineer_1_client
        filters = {
            'project__id': project.id
        }
        resp = client.get(url, filters)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        users = resp.json()
        self.assertEqual(len(users), len(expected_users))
        self.assertEqual(sorted([u['id'] for u in users]), sorted([u.id for u in expected_users]))

        # test by project name
        url = reverse('api:user-list')
        # since june 2019. Only admin or data_engineer can GET users.
        client = self.data_engineer_1_client
        filters = {
            'project__name': project.name
        }
        resp = client.get(url, filters)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        users = resp.json()
        self.assertEqual(len(users), len(expected_users))
        self.assertEqual(sorted([u['id'] for u in users]), sorted([u.id for u in expected_users]))

        # test by project code
        url = reverse('api:user-list')
        # since june 2019. Only admin or data_engineer can GET users.
        client = self.data_engineer_1_client
        filters = {
            'project__code': project.code
        }
        resp = client.get(url, filters)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        users = resp.json()
        self.assertEqual(len(users), len(expected_users))
        self.assertEqual(sorted([u['id'] for u in users]), sorted([u.id for u in expected_users]))


class TestPasswords(helpers.BaseUserTestCase):

    def test_create_with_password(self):
        """
        User can be created with password.
        Test that the password is set
        """
        client = self.admin_client
        url = reverse('api:user-list')
        user_payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            'first_name': 'New',
            'last_name': 'User',
            "password": "abcdefghi"
        }
        resp = client.post(url, user_payload)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        # verify response
        data = resp.json()
        self.assertIn('id', data)
        user = User.objects.filter(id=data['id']).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(user_payload['password']))
        self.assertEqual(user.username, user_payload['username'])
        self.assertEqual(user.email, user_payload['email'])
        self.assertEqual(user.first_name, user_payload['first_name'])
        self.assertEqual(user.last_name, user_payload['last_name'])

        # test that the user can retrieve it's token
        url = reverse('api:auth-token')
        token_payload = {
            'username': user_payload['username'],
            'password': user_payload['password']
        }
        resp = client.post(url, token_payload)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

    def test_update_not_change_password(self):
        """
        An update (PUT or PATCH) should not change the password
        """
        client = self.admin_client
        url = reverse('api:user-list')
        initial_password = 'abcdefghi'
        payload = {
            "username": 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            "password": initial_password
        }
        resp = client.post(url, payload)
        self.assertEqual(status.HTTP_201_CREATED, resp.status_code)
        data = resp.json()
        user = User.objects.filter(id=data['id']).first()

        # put with new password
        url = reverse('api:user-detail', kwargs={'pk': user.pk})
        # change first name and password
        payload = {
            "username": 'newuser',
            'first_name': 'First',
            'last_name': 'Last',
            "password": "xxxxxxxxxxxxxxx"
        }
        resp = client.put(url, payload)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        user.refresh_from_db()
        self.assertEqual(user.first_name, payload['first_name'])
        self.assertTrue(user.check_password(initial_password))

        # patch
        payload = {
            'first_name': 'serge',
            "password": "zzzzzzzz"
        }
        resp = client.patch(url, payload)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        user.refresh_from_db()
        self.assertEqual(user.first_name, payload['first_name'])
        # password should be unchanged
        self.assertTrue(user.check_password(initial_password))

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {
                'min_length': 10,
            }
        },
    ])
    def test_create_user_password_constraints(self):
        """
        Test that the when creating a User the API respect the password constraints settings
        """
        # password min length = 10
        client = self.admin_client
        url = reverse('api:user-list')
        # password too short
        user_payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            'first_name': 'New',
            'last_name': 'User',
            "password": "123456"
        }
        resp = client.post(url, user_payload)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)
        # should have an error fo the email field
        data = resp.json()
        self.assertIn('password', data)
        messages = data.get('password')
        self.assertIsInstance(messages, list)
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertIn('must contain at least 10 characters', message)

    def test_change_password_end_point(self):
        """
        end point is POST /api/password/ with payload { current_password:'', new_password:''}
        Test cases:
        - only a user can change it's own password. The end point acts only the authenticated user.
        - a readonly user
        """
        url = reverse('api:set-password')
        # test happy path
        user = self.custodian_1_user
        current_password = 'password'
        self.assertTrue(user.check_password(current_password))
        new_password = 'possward'
        self.assertNotEqual(current_password, new_password)
        payload = {
            'current_password': current_password,
            'new_password': new_password
        }
        client = self.custodian_1_client
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))

        # test if the current_password is not correct we have a 400
        payload = {
            'current_password': 'not correct',
            'new_password': new_password
        }
        client.force_login(self.custodian_1_user)
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        self.assertIn('current_password', data)
        messages = data.get('current_password')
        self.assertIsInstance(messages, list)
        self.assertEqual(len(messages), 1)
        message = messages[0]
        self.assertIn('invalid password', message.lower())

        # an anonymous client get a 401 response
        client = self.anonymous_client
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TestPasswordResetWorkflow(helpers.BaseUserTestCase):
    """
    Workflow:
    request a POST /pssword/reset/ with just an email at payload
    if email exists in the system send an email with at least a link to a url like
    http://web-client/#reset-password{uid}/{token}
    the web client is charge then to hit the API /password/reset/confirm with payload:
    {
      'uid': 'uid from url'
      'token': 'token from url'
      'new_password': 'new password'
    }
    """

    def test_reset_password_permissions(self):
        """
        Any one can issue a reset password request.
        If the email is not found in the system it will return 204 or 400 with an error message, depending of a setting
        """
        url = reverse('api:password-reset')
        client = APIClient()
        # send an email that is not in the system
        payload = {
            'email': 'daboss@gaiaresources.com.au'
        }
        resp = client.post(url, payload)
        # the response status code depends of a setting, could be 204 or 400
        self.assertIn(resp.status_code, [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_400_BAD_REQUEST
        ])

    @override_settings(DJOSER={
        'PASSWORD_RESET_CONFIRM_URL': 'password-reset/{uid}/{token}',
        'PASSWORD_RESET_SHOW_EMAIL_NOT_FOUND': True
    })
    def test_reset_password_email(self):
        """
        Happy path:
        - request a reset password for a valid email,
        - email should have been sent to the correct email,
        - email should contains a valid url with a uid and a token
        """
        url = reverse('api:password-reset')
        client = APIClient()

        # create a user
        email = 'john.doe@example.com'
        # User created with factories.UserFactory doesn't have a proper encoded password. The password-reset view will
        # discard them with a filter on is_password_usable.
        # TODO: fix the UserFactory to encode password using MD5 for quick encoding.
        user = User.objects.create_user(username='johndoe', email=email, password='sjaksjq')
        payload = {
            'email': email
        }
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('/password-reset/' in mail.outbox[0].body)
        pattern = r'/password-reset/(?P<uid>[^\/]+)\/(?P<token>[^\/\s]+)'
        match = re.search(pattern, mail.outbox[0].body)
        params = match.groupdict()
        uid = params.get('uid')
        token = params.get('token')

        # knowing uid and token we should be able to request a password reset confirm
        url = reverse('api:password-reset-confirm')
        new_password = 'DaPassword'
        payload = {
            'uid': uid,
            'token': token,
            'new_password': new_password
        }
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        # check that the user has a new password
        user.refresh_from_db()
        self.assertTrue(user.check_password(new_password))


@override_settings(AUTH_PASSWORD_VALIDATORS=[])
class TestUsername(helpers.BaseUserTestCase):

    def test_username_backslash(self):
        """
        Required by OEH NSW to accommodate their Windows domain name
        The username can include a '\`, e.g 'DEC\serge`
        """
        # test create
        url = reverse('api:user-list')
        client = self.admin_client
        payload = {
            'username': 'domain\\user',
            'password': '123456'
        }
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # ORM query
        user = User.objects.filter(username='domain\\user').first()
        self.assertIsNotNone(user)
        # try API to get the auth token
        # test that the user can retrieve it's token
        url = reverse('api:auth-token')
        client = APIClient()
        token_payload = {
            'username': payload['username'],
            'password': payload['password']
        }
        resp = client.post(url, token_payload)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)

        # should also work with put/patch
        url = reverse('api:user-detail', kwargs={'pk': user.pk})
        payload = {
            'username': 'dec\\a\\lot'
        }
        client = self.admin_client
        resp = client.patch(url, payload)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        user.refresh_from_db()
        self.assertEqual(user.username, 'dec\\a\\lot')

    def test_username_unique(self):
        """
        Test that the API detect username duplicate
        """
        # create user
        url = reverse('api:user-list')
        client = self.admin_client
        payload = {
            'username': 'domain\\user',
            'first_name': 'F1',
            'lats_name': 'L1',
            'password': '123456'
        }
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # try to create a user with same username
        url = reverse('api:user-list')
        client = self.admin_client
        payload = {
            'username': 'domain\\user',
            'first_name': 'F2',
            'lats_name': 'L2',
            'password': 'abcdefghij'
        }
        resp = client.post(url, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        data = resp.json()
        self.assertIn('username', data)
        # the error message should contains the word unique
        message = data.get('username')[0]
        self.assertIn('unique', message.lower())


class TestUserCreateDefaultProject(helpers.BaseUserTestCase):
    """
    Use case:
    When a user signup he can request to be the custodian od a projects through POST params.
    This will only be allowed if the requested project name is in a ALLOWED_PUBLIC_REGISTRATION_PROJECTS setting list.
    Note: at this stage if the user request a not allowed project we don't return any error. The user is created but not
    assigned to the requested project.
    """

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    def test_default_none(self):
        """
        By default the user is not assigned to any project even if user request it
        """
        url = reverse('api:user-list')
        payload = {
            "username": "public",
            "email": "newuser@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe",
            "projects": self.project_1.name
        }
        client = self.anonymous_client
        resp = client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.filter(username=payload['username']).first()
        self.assertIsNotNone(user)
        self.assertFalse(self.project_1.is_custodian(user))

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    @override_settings(ALLOWED_PUBLIC_REGISTRATION_PROJECTS=['Project_1'])
    def test_one_project_allowed(self):
        """
        User request to be assigned to an allowed project
        """
        url = reverse('api:user-list')
        payload = {
            "username": "public",
            "email": "newuser@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe",
            "projects": 'Project_1'
        }
        client = self.anonymous_client
        resp = client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.filter(username=payload['username']).first()
        self.assertIsNotNone(user)
        self.assertTrue(self.project_1.is_custodian(user))

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    @override_settings(ALLOWED_PUBLIC_REGISTRATION_PROJECTS=['Project_2'])
    def test_one_project_not_allowed(self):
        """
        User request to be assigned to not allowed project
        """
        url = reverse('api:user-list')
        payload = {
            "username": "public",
            "email": "newuser@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe",
            "projects": ['Project_1']
        }
        client = self.anonymous_client
        resp = client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.filter(username=payload['username']).first()
        self.assertIsNotNone(user)
        self.assertFalse(self.project_1.is_custodian(user))

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    @override_settings(ALLOWED_PUBLIC_REGISTRATION_PROJECTS=['Project_1'])
    def test_request_two_projects_only_one_allowed(self):
        """
        User request to be assigned to two projects but only one is allowed.
        No error is sent back but the user is custodian of only one
        """
        url = reverse('api:user-list')
        payload = {
            "username": "public",
            "email": "newuser@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe",
            "projects": ['Project_1', 'Project_2']
        }
        client = self.anonymous_client
        resp = client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.filter(username=payload['username']).first()
        self.assertIsNotNone(user)
        self.assertTrue(self.project_1.is_custodian(user))
        self.assertFalse(self.project_2.is_custodian(user))

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    @override_settings(ALLOWED_PUBLIC_REGISTRATION_PROJECTS=['Project_1', 'Project_2'])
    def test_request_two_projects_allowed(self):
        """
        User request to be assigned to two projects but only one is allowed.
        No error is sent back but the user is custodian of only one
        """
        url = reverse('api:user-list')
        payload = {
            "username": "public",
            "email": "newuser@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe",
            "projects": ['Project_1', 'Project_2']
        }
        client = self.anonymous_client
        resp = client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.filter(username=payload['username']).first()
        self.assertIsNotNone(user)
        self.assertTrue(self.project_1.is_custodian(user))
        self.assertTrue(self.project_2.is_custodian(user))
