from django.urls import reverse
from rest_framework import status

from main.tests.api import helpers


class TestView(helpers.BaseUserTestCase):

    def test_logged_in_happy_path(self):
        url = reverse('doc-swagger')
        resp = self.readonly_client.get(url, follow=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
