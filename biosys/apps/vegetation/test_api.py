from django.core.urlresolvers import reverse
from django.utils.http import urlencode
import json
from main.tests.test_admin import BaseTestCase
from mixer.backend.django import mixer

from vegetation import models


class VegetationAPITest(BaseTestCase):
    def setUp(self):
        super(VegetationAPITest, self).setUp()
        # Create some test data.
        self.veg_visit = mixer.blend(
            models.VegetationVisit, site_visit=mixer.SELECT)
        self.stratum_sp = mixer.blend(
            models.StratumSpecies, vegetation_visit=mixer.SELECT)
        self.transect_obs = mixer.blend(
            models.TransectObservation, vegetation_visit=mixer.SELECT)
        self.transect_dist_changes = mixer.blend(
            models.TransectDistinctChanges, vegetation_visit=mixer.SELECT)
        self.basal_bitt = mixer.blend(
            models.BasalBitterlichObservation, vegetation_visit=mixer.SELECT)
        self.erosion_peg = mixer.blend(
            models.ErosionPeg, vegetation_visit=mixer.SELECT)
        self.peg_obs = mixer.blend(
            models.PegObservation, vegetation_visit=mixer.SELECT)
        self.ground_cover_summ = mixer.blend(
            models.GroundCoverSummary, vegetation_visit=mixer.SELECT)
        self.stratum_summary = mixer.blend(
            models.StratumSummary, vegetation_visit=mixer.SELECT)
        self.dist_ind = mixer.blend(
            models.DisturbanceIndicator, vegetation_visit=mixer.SELECT)
        self.plant_obs = mixer.blend(
            models.PlantObservation, vegetation_visit=mixer.SELECT)
        self.biodiversity_ind = mixer.blend(
            models.BiodiversityIndicator, vegetation_visit=mixer.SELECT)

    def test_permission_resource_list(self):
        """Test access permission to resource lists
        """
        for i in [
                'vegetationvisit', 'stratumspecies', 'transectobservation',
                'transectdistinctchanges', 'basalbitterlichobservation',
                'erosionpeg', 'pegobservation', 'stratumsummary',
                'disturbanceindicator', 'plantobservation', 'biodiversityindicator']:
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
        for i in [
                models.VegetationVisit, models.StratumSpecies,
                models.TransectDistinctChanges, models.BasalBitterlichObservation,
                models.ErosionPeg, models.PegObservation, models.StratumSummary,
                models.DisturbanceIndicator, models.PlantObservation,
                models.BiodiversityIndicator]:
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

    def test_vegetationvisit_quarantined_results(self):
        """Test that the VegetationVisitResource returns different data for normal & custodian users
        """
        url = reverse('api_dispatch_list', kwargs={'resource_name': 'vegetationvisit', 'api_name': 'v1'})
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

    def test_vegetationvisit_quarantined_children(self):
        """Test that child objects of the VegetationVisit model return different data for normal & custodian users
        """
        for i in [
                'stratumspecies', 'transectobservation', 'transectdistinctchanges',
                'basalbitterlichobservation', 'erosionpeg', 'pegobservation',
                'groundcoversummary', 'stratumsummary', 'disturbanceindicator',
                'plantobservation', 'biodiversityindicator']:
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
