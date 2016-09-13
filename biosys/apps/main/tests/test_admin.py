from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from mixer.backend.django import mixer
from django.contrib.auth.models import User
from main.models import Project, Site


class BaseTestCase(TestCase):
    fixtures = ['test-users.json']
    client = Client()

    def setUp(self):
        super(BaseTestCase, self).setUp()
        # Create some data
        self.project = mixer.blend(Project)
        self.site = mixer.blend(Site, project=mixer.SELECT)


class AdminTest(BaseTestCase):
    def test_permission_index(self):
        """Test that non-superusers are all redirected away from the admin index
        """
        url = reverse('admin:index')
        response = self.client.get(url)  # Anonymous user
        self.assertEqual(response.status_code, 302)
        for user in ['readonly', 'custodian']:
            self.client.login(username=user, password='password')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_permission_main_index(self):
        """Test that users in each group can/cannot view the main app index
        """
        for user, code in [('readonly', 302), ('custodian', 302),]:
            self.client.login(username=user, password='password')
            url = reverse('admin:app_list', args=('main',))
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, code,
                '{} wrong permission for main app index ({})'.format(user, response.status_code))

    def test_permission_main_changelists(self):
        """Test that users in each group can/cannot view main app model changelists
        """
        for user, code in [('readonly', 302), ('custodian', 302)]:
            self.client.login(username=user, password='password')
            for m in [Project, Site]:
                url = reverse('admin:main_{}_changelist'.format(m._meta.model_name))
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, code,
                    '{} wrong permission for {} ({})'.format(user, m._meta.object_name, response.status_code))