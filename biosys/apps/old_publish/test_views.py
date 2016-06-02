from django.core.urlresolvers import reverse
from main.tests.test_admin import BaseTestCase


class PublishViewTest(BaseTestCase):
    def test_reportview_anon_unauth_redirect(self):
        """Test that the ReportView redirects anonymous users
        """
        url = reverse('old_publish:publish_report')
        response = self.client.get(url)  # Anonymous user
        self.assertEqual(response.status_code, 302)

    def test_reportview_auth(self):
        """Test that authorised users can open the ReportView
        """
        url = reverse('old_publish:publish_report')
        for user in ['custodian', 'uploader', 'normaluser']:
            self.client.login(username=user, password='test')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_anonymous_downloadview(self):
        """Test that the DownloadView redirects anonymous users
        """
        url = reverse('old_publish:publish_download')
        response = self.client.get(url)  # Anonymous user.
        self.assertEqual(response.status_code, 302)
