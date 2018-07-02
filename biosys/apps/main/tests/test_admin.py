from django.core.urlresolvers import reverse

from main.models import Project, Site
from main.tests import factories
from main.tests.api import helpers


class BaseTestCase(helpers.BaseUserTestCase):

    def setUp(self):
        super(BaseTestCase, self).setUp()
        # Create some data
        self.program = factories.ProgramFactory.create()
        self.project = self.project_1
        self.site = factories.SiteFactory(
            project=self.project_1
        )


class AdminTest(BaseTestCase):
    def test_permission_index(self):
        """Test that non-superusers are all redirected away from the admin index
        """
        url = reverse('admin:index')
        forbidden = [
            self.anonymous_client,
            self.readonly_client,
            self.custodian_1_client,
            self.data_engineer_1_client,
            self.custodian_2_client,
            self.data_engineer_2_client,
        ]
        for client in forbidden:
            response = client.get(url)
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