from django.core.urlresolvers import reverse
from rest_framework import status

from main.tests import factories
from main.tests.api import helpers


class TestPermissions(helpers.BaseUserTestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin or user itself
    Create: admin
    Delete: forbidden through API
    """

    def test_get(self):
        urls = [
            reverse('api:user-list'),
            reverse('api:user-detail', kwargs={'pk': 1})
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

    def test_update(self):
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

        url = reverse('api:user-list')
        client = self.custodian_1_client
        filters = {
            'project_id': project.id
        }
        resp = client.get(url, filters)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        users = resp.json()
        self.assertEqual(len(users), len(expected_users))
        self.assertEqual(sorted([u['id'] for u in users]), sorted([u.id for u in expected_users]))
