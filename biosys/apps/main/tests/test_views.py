from django.core.urlresolvers import reverse
from main.tests.test_admin import BaseTestCase


class DatasheetSchemaViewTest(BaseTestCase):
    def test_datasheet_view_anon(self):
        """Test that anonymous users can't open the datasheet schema view
        """
        url = reverse('datasheet_schema')
        response = self.client.get(url)  # Anonymous user.
        self.assertEqual(response.status_code, 403)

    def test_datasheet_view_auth(self):
        """Test that authenticated users can open the datasheet schema view
        """
        url = reverse('datasheet_schema')
        for user in ['custodian', 'uploader', 'normaluser']:
            self.client.login(username=user, password='test')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
