from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from mixer.backend.django import mixer
from django.contrib.auth.models import User
from main.models import (Project, Site, Visit, SiteVisit,
                         SiteVisitDataFile, GeologyGroupLookup,
                         SpeciesObservation, SiteCharacteristic)


class BaseTestCase(TestCase):
    fixtures = ['groups.json', 'test-users.json']
    client = Client()

    def setUp(self):
        super(BaseTestCase, self).setUp()
        # Need to set user passwords to enable test db re-use.
        self.superuser = User.objects.get(username='admin')
        self.superuser.set_password('test')
        self.superuser.save()
        self.custodian = User.objects.get(username='custodian')
        self.custodian.set_password('test')
        self.custodian.save()
        self.uploader = User.objects.get(username='uploader')
        self.uploader.set_password('test')
        self.uploader.save()
        self.n_user = User.objects.get(username='normaluser')
        self.n_user.set_password('test')
        self.n_user.save()
        # Create some data
        self.project = mixer.blend(Project)
        self.site = mixer.blend(Site, site_ID=mixer.RANDOM, project=mixer.SELECT)
        self.visit = mixer.blend(Visit, project=mixer.SELECT)
        self.site_visit = mixer.blend(SiteVisit, site=mixer.SELECT)
        self.species_obs = mixer.blend(SpeciesObservation, site_visit=mixer.SELECT)
        self.site_char = mixer.blend(SiteCharacteristic, site_visit=mixer.SELECT)


class AdminTest(BaseTestCase):
    def test_permission_index(self):
        """Test that non-superusers are all redirected away from the admin index
        """
        url = reverse('admin:index')
        response = self.client.get(url)  # Anonymous user
        self.assertEqual(response.status_code, 302)
        for user in ['custodian', 'uploader', 'normaluser']:
            self.client.login(username=user, password='test')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)

    def test_permission_main_index(self):
        """Test that users in each group can/cannot view the main app index
        """
        for user, code in [('custodian', 200), ('uploader', 200), ('normaluser', 302)]:
            self.client.login(username=user, password='test')
            url = reverse('admin:app_list', args=('main',))
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, code,
                '{} wrong permission for main app index ({})'.format(user, response.status_code))

    def test_render_main_index_links_present(self):
        """Test that required links render on main app index
        """
        for user in ['custodian', 'uploader']:
            self.client.login(username=user, password='test')
            url = reverse('admin:app_list', args=('main',))
            response = self.client.get(url)
            for m in [Project, Site, Visit]:
                url = reverse('admin:main_{}_changelist'.format(m._meta.model_name))
                self.assertContains(response, url, msg_prefix=user)

    def test_render_main_index_links_absent(self):
        """Test that defined links do not render on main app index
        """
        for user in ['custodian', 'uploader']:
            self.client.login(username=user, password='test')
            url = reverse('admin:app_list', args=('main',))
            response = self.client.get(url)
            for m in [SiteVisit, SiteVisitDataFile, GeologyGroupLookup]:
                url = reverse('admin:main_{}_changelist'.format(m._meta.model_name))
                self.assertNotContains(response, url, msg_prefix=user)

    def test_permission_main_changelists(self):
        """Test that users in each group can/cannot view main app model changelists
        """
        for user, code in [('custodian', 200), ('uploader', 200), ('normaluser', 302)]:
            self.client.login(username=user, password='test')
            for m in [Project, Site, Visit]:
                url = reverse('admin:main_{}_changelist'.format(m._meta.model_name))
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, code,
                    '{} wrong permission for {} ({})'.format(user, m._meta.object_name, response.status_code))

    def test_permission_visit_changeform(self):
        """Test that users in each group can/cannot view Visit change form
        """
        for user, code in [('custodian', 200), ('uploader', 200), ('normaluser', 302)]:
            self.client.login(username=user, password='test')
            url = reverse('admin:main_visit_change', args=[self.visit.pk])
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, code, '{} wrong permission ({})'.format(user, response.status_code))

    def test_render_visit_changeform(self):
        for user in ['custodian', 'uploader']:
            self.client.login(username=user, password='test')
            url = reverse('admin:main_visit_change', args=[self.visit.pk])
            response = self.client.get(url)
            self.assertTemplateUsed(response, 'main/visit_change_form.html')
            # 'Download blank datasheets' URL
            url = reverse('admin:main_visit_download_datasheet', kwargs={'pk': self.visit.pk})
            self.assertContains(response, url, msg_prefix=user)
            # 'Upload completed datasheet' URL
            url = reverse('admin:main_visit_upload_datasheet', args=[self.visit.pk])
            self.assertContains(response, url, msg_prefix=user)

    def test_permission_visit_upload_datasheet_view(self):
        for user, code in [('custodian', 200), ('uploader', 200), ('normaluser', 302)]:
            self.client.login(username=user, password='test')
            url = reverse('admin:main_visit_upload_datasheet', args=[self.visit.pk])
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, code, '{} wrong permission ({})'.format(user, response.status_code))
