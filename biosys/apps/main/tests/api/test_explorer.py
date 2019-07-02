from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework import status

from main.tests.api import helpers


class TestSwaggerPermission(helpers.BaseUserTestCase):
    """
    If server allows public registration, swagger should only accessible to admin and data_engineers.
    Otherwise it should be only for authenticated user.
    """

    @override_settings(ALLOW_PUBLIC_REGISTRATION=False)
    def test_no_public_registration(self):
        url = '/api/explorer'
        forbidden = [
            self.anonymous_client,
        ]
        for client in forbidden:
            response = client.get(url, follow=True)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Something is weird here. When trying to use the /api/explorer end point the unit tests break after the first
        # successful get!! The error is database already closed ??
        # (django.db.utils.InterfaceError: connection already closed)
        # By using the following url it works. This url has the same permission as the /api/swagger
        # TODO: fix the issue described above
        url = '/api/swagger.json'
        allowed = [
            self.readonly_client,
            self.custodian_1_client,
            self.data_engineer_1_client,
            self.admin_client
        ]
        for client in allowed:
            response = client.get(url, follow=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(ALLOW_PUBLIC_REGISTRATION=True)
    def test_public_registration(self):
        url = '/api/explorer'
        forbidden = [
            self.anonymous_client,
            self.readonly_client,
            self.custodian_1_client,
            self.custodian_2_client,
        ]
        for client in forbidden:
            response = client.get(url, follow=True)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Something is weird here. When trying to use the /api/explorer end point the unit tests break after the first
        # successful get!! The error is database already closed ??
        # (django.db.utils.InterfaceError: connection already closed)
        # By using the following url it works. This url has the same permission as the /api/swagger
        # TODO: fix the issue described above
        url = '/api/swagger.json'
        allowed = [
            self.data_engineer_1_client,
            self.admin_client
        ]
        for client in allowed:
            response = client.get(url, follow=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
