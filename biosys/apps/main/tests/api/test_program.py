from django.core.urlresolvers import reverse
from rest_framework import status

from main.tests.api import helpers


class TestPermissions(helpers.BaseUserTestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin
    Create: admin
    Delete: admin
    """

    def test_get(self):
        urls = [
            reverse('api:program-list'),
            reverse('api:program-detail', kwargs={'pk': self.program_1.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client],
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
        Only admin
        :return:
        """
        urls = [reverse('api:program-list')]
        data = {
            "name": "A new program for Unit test",
            "code": "T1234",
            "data_engineers": [self.data_engineer_1_user.pk]
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
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

    def test_put(self):
        """
        Only admin
        :return:
        """
        urls = [reverse('api:program-detail', kwargs={'pk': self.program_1.pk})]
        data = {
            "name": "A new program for Unit test",
            "code": "T1234",
            "data_engineers": [self.data_engineer_1_user.pk]
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
            ]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.put(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                # Name must me unique
                data['name'] += '1'
                self.assertEqual(
                    client.put(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )

    def test_patch(self):
        """
        Only admin
        :return:
        """
        urls = [reverse('api:program-detail', kwargs={'pk': self.program_1.pk})]
        data = {
            "code": "XXXX",
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
            ]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )

    def test_delete(self):
        """
        Admin only
        :return:
        """
        urls = [reverse('api:program-detail', kwargs={'pk': self.program_1.pk})]
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
            ]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.delete(url, format='json').status_code,
                    status.HTTP_204_NO_CONTENT
                )
