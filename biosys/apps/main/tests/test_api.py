from datetime import date, timedelta
from django.core.urlresolvers import reverse
from django.utils.http import urlencode
import json
from tastypie.models import ApiAccess, ApiKey

from main.models import (Project, Site, Visit, SiteVisit,
                         SiteVisitDataFile, GeologyGroupLookup,
                         OldSpeciesObservation, SiteCharacteristic)
from main.tests.test_admin import BaseTestCase


class MainAPITest(BaseTestCase):
    def setUp(self):
        super(MainAPITest, self).setUp()
        # Setup API Key for uploader user to test non-session authentication
        self.api_key = ApiKey.objects.create(user=self.uploader, key="testkey")
        self.api_key.save()

    def test_permission_top_level(self):
        """Test access permission to top-level API URLs
        """
        url = reverse('api_v1_top_level', kwargs={'api_name': 'v1'})
        self.client.logout()
        response = self.client.get(url)  # Anonymous user
        self.assertEqual(response.status_code, 401)
        for user in ['custodian', 'uploader', 'normaluser']:
            self.client.login(username=user, password='test')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_permission_resource_list(self):
        """Test access permission to resource lists
        """
        for i in [
                'project', 'site', 'visit', 'sitevisitdatafile', 'sitevisit',
                'oldspeciesobservation', 'sitecharacteristic']:
            url = reverse('api_dispatch_list', kwargs={'resource_name': i, 'api_name': 'v1'})
            url += '?' + urlencode({'format': 'json'})
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
                Project, Site, Visit, SiteVisit, OldSpeciesObservation, SiteCharacteristic]:
            obj = i.objects.all()[0]
            url = reverse('api_dispatch_detail', kwargs={
                'resource_name': i._meta.object_name.lower(),
                'api_name': 'v1',
                'pk': obj.pk})
            url_json = url + '?' + urlencode({'format': 'json'})
            url_csv = url + '?' + urlencode({'format': 'csv'})
            self.client.logout()
            response = self.client.get(url_json)  # Anonymous user
            self.assertEqual(response.status_code, 401)
            # Authenticated users
            for user in ['custodian', 'uploader']:
                self.client.logout()
                self.client.login(username=user, password='test')
                response = self.client.get(url_json)
                self.assertEqual(response.status_code, 200)
                response = self.client.get(url_csv)
                self.assertEqual(response.status_code, 200)

    def test_apikey_permission_resource_list(self):        
        """Test access permission to resource lists using an api_key
        """
        for i in [
                'project', 'site', 'visit', 'sitevisitdatafile', 'sitevisit',
                'speciesobservation', 'sitecharacteristic']:
            url = reverse('api_dispatch_list', kwargs={'resource_name': i, 'api_name': 'v1'})
            querystring = '?' + urlencode({'format': 'json'})
            self.client.logout()
            response = self.client.get(url + querystring)  # Anonymous user
            self.assertEqual(response.status_code, 401)
            # Authenticated user
            querystring = '?' + urlencode({'format': 'json', 'username': 'uploader', 'api_key': 'testkey'})
            response = self.client.get(url + querystring)
            self.assertEqual(response.status_code, 200)
    
    def test_apikey_permission_resource_detail(self):
        """Test access permission to resource details (JSON & CSV)
        """
        for i in [
                Project, Site, Visit, SiteVisit, SpeciesObservation, SiteCharacteristic]:
            obj = i.objects.all()[0]
            url = reverse('api_dispatch_detail', kwargs={
                'resource_name': i._meta.object_name.lower(),
                'api_name': 'v1',
                'pk': obj.pk})
            url_json = url + '?' + urlencode({'format': 'json'})
            url_csv = url + '?' + urlencode({'format': 'csv'})
            self.client.logout()
            response = self.client.get(url_json)  # Anonymous user
            self.assertEqual(response.status_code, 401)
            response = self.client.get(url_csv)   # Anonymous user
            self.assertEqual(response.status_code, 401)
            # Authenticated user
            url_json = url + '?' + urlencode({'format': 'json', 'username': 'uploader', 'api_key': 'testkey'})
            url_csv = url + '?' + urlencode({'format': 'json', 'username': 'uploader', 'api_key': 'testkey'})
            response = self.client.get(url_json) # Authenticated user
            self.assertEqual(response.status_code, 200)
            response = self.client.get(url_csv) # Authenticated user 
            self.assertEqual(response.status_code, 200)

    def test_visit_filter_start_date(self):
        """Test that the Visit API filters on start_date field correctly
        """
        self.client.login(username='custodian', password='test')
        today = date.today()
        tomorrow = today + timedelta(1)
        # Make visit.start_date equal today.
        self.visit.start_date = today
        self.visit.save()
        # Return results that started today.
        url = reverse('api_dispatch_list', kwargs={'resource_name': 'visit', 'api_name': 'v1'})
        url1 = url + '?' + urlencode({'format': 'json'})
        resp1 = json.loads(self.client.get(url1).content)
        # Return results that started tomorrow.
        url2 = url + '?' + urlencode({'format': 'json', 'start_date': tomorrow.isoformat()})
        resp2 = json.loads(self.client.get(url2).content)
        # Result count should be different.
        self.assertNotEqual(resp1['meta']['total_count'], resp2['meta']['total_count'])

    def test_visit_filter_end_date(self):
        """Test that the Visit API filters on end_date field correctly
        """
        self.client.login(username='custodian', password='test')
        today = date.today()
        tomorrow = today + timedelta(1)
        # Make visit.end_date equal tomorrow.
        self.visit.end_date = tomorrow
        self.visit.save()
        # Return results that ended tomorrow.
        url = reverse('api_dispatch_list', kwargs={'resource_name': 'visit', 'api_name': 'v1'})
        url1 = url + '?' + urlencode({'format': 'json'})
        resp1 = json.loads(self.client.get(url1).content)
        # Return results that ended today.
        url2 = url + '?' + urlencode({'format': 'json', 'end_date': today.isoformat()})
        resp2 = json.loads(self.client.get(url2).content)
        # Result count should be different.
        self.assertNotEqual(resp1['meta']['total_count'], resp2['meta']['total_count'])

    def test_sitevisit_approve_endpoint_post_only(self):
        """Test the custom approve endpoint for SiteVisitResource accepts POST only
        """
        self.client.login(username='custodian', password='test')
        sv = SiteVisit.objects.all()[0]
        url = reverse('api_site_visit_change_status', kwargs={'resource_name': 'sitevisit', 'api_name': 'v1', 'pk': sv.pk})
        url += '?' + urlencode({'format': 'json', 'status': 'approved'})
        # GET request should return 405 Bad Method
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

    def test_sitevisit_approve_endpoint_permission(self):
        """Test permissions for the custom approve endpoint for SiteVisitResource
        """
        sv = SiteVisit.objects.all()[0]
        url = reverse('api_site_visit_change_status', kwargs={'resource_name': 'sitevisit', 'api_name': 'v1', 'pk': sv.pk})
        url += '?' + urlencode({'format': 'json', 'status': 'approved'})
        response = self.client.post(url)  # Anonymous user.
        self.assertEqual(response.status_code, 400)
        self.client.login(username='normaluser', password='test')  # Unauthorised user.
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        # Uploader should also return 403 Forbidden.
        self.client.login(username='uploader', password='test')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        # Custodian user.
        self.client.login(username='custodian', password='test')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_sitevisit_quarantined_results(self):
        """Test that the SiteVisitResource returns different data for normal & custodian users
        """
        url = reverse('api_dispatch_list', kwargs={'resource_name': 'sitevisit', 'api_name': 'v1'})
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

    def test_sitevisit_quarantined_children(self):
        """Test that child objects of the SiteVisit model return different data for normal & custodian users
        """
        for i in ['oldspeciesobservation', 'sitecharacteristic']:
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
