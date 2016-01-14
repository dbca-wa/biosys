from django.core.urlresolvers import reverse
from django.utils.http import urlencode
import json
from main.tests.test_admin import BaseTestCase
from mixer.backend.django import mixer

from animals import models


class AnimalsAPITest(BaseTestCase):
    def setUp(self):
        super(AnimalsAPITest, self).setUp()
        self.trap = mixer.blend(models.Trap, site_visit=mixer.SELECT)
        self.animal_obs = mixer.blend(models.AnimalObservation, site_visit=mixer.SELECT)
        self.oppor_obs = mixer.blend(models.OpportunisticObservation, site_visit=mixer.SELECT)

    def test_permission_resource_list(self):
        """Test access permission to resource lists
        """
        for i in ['trap', 'animalobservation', 'opportunisticobservation']:
            url = reverse('api_dispatch_list', kwargs={'resource_name': i, 'api_name': 'v1'})
            self.client.logout()
            response = self.client.get(url)  # Anonymous user
            self.assertEqual(response.status_code, 401)
            # Authenticated users
            for user in ['custodian', 'uploader', 'normaluser']:
                self.client.login(username=user, password='test')
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_permission_resource_detail(self):
        """Test access permission to resource details (JSON & CSV)
        """
        for i in [models.Trap, models.AnimalObservation, models.OpportunisticObservation]:
            self.client.logout()
            obj = i.objects.all()[0]
            url = reverse('api_dispatch_detail', kwargs={
                'resource_name': i._meta.object_name.lower(),
                'api_name': 'v1',
                'pk': obj.pk})
            url_json = url + '?' + urlencode({'format': 'json'})
            url_csv = url + '?' + urlencode({'format': 'csv'})
            response = self.client.get(url_json)  # Anonymous user
            self.assertEqual(response.status_code, 401)
            # Authorised users
            for user in ['custodian', 'uploader']:
                self.client.login(username=user, password='test')
                response = self.client.get(url_json)
                self.assertEqual(response.status_code, 200)
                response = self.client.get(url_csv)
                self.assertEqual(response.status_code, 200)

    def test_sitevisit_quarantined_children(self):
        """Test that child objects of the SiteVisit model return different data for normal & custodian users
        """
        for i in ['trap', 'animalobservation', 'opportunisticobservation']:
            url = reverse('api_dispatch_list', kwargs={'resource_name': i, 'api_name': 'v1'})
            url += '?' + urlencode({'format': 'json'})
            self.client.login(username='normaluser', password='test')
            resp_ro = json.loads(self.client.get(url).content)
            self.client.login(username='custodian', password='test')
            # R/o result list should be empty.
            self.assertFalse(resp_ro['objects'])
            # Custodian should see data.
            resp = json.loads(self.client.get(url).content)
            self.assertTrue(resp['objects'])
            # Result count for normal & custodian user should be different.
            self.assertNotEqual(resp_ro['meta']['total_count'], resp['meta']['total_count'])
