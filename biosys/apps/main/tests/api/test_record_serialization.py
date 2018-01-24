from django.shortcuts import reverse
from rest_framework import status

from main.tests.api import helpers


class TestFieldSelection(helpers.BaseUserTestCase):

    def _more_setup(self):
        # create some data with date and geometry
        self.rows = [
            ['What', 'When', 'Latitude', 'Longitude'],
            ['a big bird', '20018-01-24', -32.0, 115.75],
            ['a chubby bat ', '20017-12-24', -33.6, 116.678],
        ]
        self.dataset = self._create_dataset_and_records_from_rows(self.rows)

    def test_only_geometry(self):
        """
        Scenario: a web map user needs only the geometry field.
            Given some records with geometry are created
            And I request a get 'dataset-record' with fields=geometry
            Then it should return only the geometry field
        """
        # records are created in setup
        client = self.custodian_1_client
        url = reverse('api:dataset-records', kwargs={'pk': self.dataset.pk})
        query_params = {
            'fields': 'geometry'
        }
        resp = client.get(url, data=query_params, format='json')
        self.assertEquals(status.HTTP_200_OK, resp.status_code)
        records = resp.json()
        self.assertIsInstance(records, list)
        expected_record_count = len(self.rows) - 1
        self.assertEquals(len(records), expected_record_count)
        expected_fields = ['geometry']
        for record in records:
            self.assertIsInstance(record, dict)
            self.assertListEqual(list(record.keys()), expected_fields)

    def test_geometry_and_id(self):
        """
        Scenario: a web map user needs only the geometry field and the record id to display an edit link.
            Given some records with geometry are created
            And I request a get 'dataset-record' with fields geometry and id
            Then it should return only the geometry and the id field
        """
        # records are created in setup
        client = self.custodian_1_client
        url = reverse('api:dataset-records', kwargs={'pk': self.dataset.pk})
        query_params = {
            'fields': ['geometry', 'id']
        }
        resp = client.get(url, data=query_params, format='json')
        self.assertEquals(status.HTTP_200_OK, resp.status_code)
        records = resp.json()
        self.assertIsInstance(records, list)
        expected_record_count = len(self.rows) - 1
        self.assertEquals(len(records), expected_record_count)
        expected_fields = ['geometry', 'id']
        for record in records:
            self.assertIsInstance(record, dict)
            self.assertListEqual(list(record.keys()), expected_fields)

    def test_geometry_and_id_record_end_point(self):
        """
        Same as above but we hit the GET /records instead of GET/dataset/{pk}/records
        Scenario: a web map user needs only the geometry field and the record id to display an edit link.
            Given some records with geometry are created
            And I request a get 'record' with fields geometry and id
            Then it should return only the geometry and the id field
        """
        # records are created in setup
        client = self.custodian_1_client
        url = reverse('api:record-list')
        query_params = {
            'fields': ['geometry', 'id']
        }
        resp = client.get(url, data=query_params, format='json')
        self.assertEquals(status.HTTP_200_OK, resp.status_code)
        records = resp.json()
        self.assertIsInstance(records, list)
        expected_record_count = len(self.rows) - 1
        self.assertEquals(len(records), expected_record_count)
        expected_fields = ['geometry', 'id']
        for record in records:
            self.assertIsInstance(record, dict)
            # only key = geometry
            self.assertListEqual(list(record.keys()), expected_fields)
            # request record individually
            url = reverse('api:record-detail', kwargs={'pk': record.get('id')})
            resp = client.get(url, data=query_params, format='json')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            self.assertListEqual(list(resp.json().keys()), expected_fields)

    def test_not_existing_field(self):
        """
        Scenario: asking for field that doesn't exists should not return an error but empty records
            Given some records with geometry are created
            And I request a get 'record' with a field 'field_with_typo'
            Then it should be successful
            And return records with no field
        """
        # records are created in setup
        client = self.custodian_1_client
        url = reverse('api:record-list')
        query_params = {
            'fields': ['field_with_typo']
        }
        resp = client.get(url, data=query_params, format='json')
        self.assertEquals(status.HTTP_200_OK, resp.status_code)
        records = resp.json()
        expected_fields = []
        for record in records:
            self.assertIsInstance(record, dict)
            self.assertListEqual(list(record.keys()), expected_fields)

    def test_one_not_existing_field(self):
        """
        Scenario: asking for field that exists and one that doesn't exists should not return an error but the valid field
            Given some records with geometry are created
            And I request a get 'record' with a field 'geometry' and a field 'field_with_typo'
            Then it should be successful
            And return records with the geometry field
        """
        # records are created in setup
        client = self.custodian_1_client
        url = reverse('api:record-list')
        query_params = {
            'fields': ['geometry', 'field_with_typo']
        }
        resp = client.get(url, data=query_params, format='json')
        self.assertEquals(status.HTTP_200_OK, resp.status_code)
        records = resp.json()
        expected_fields = ['geometry']
        for record in records:
            self.assertIsInstance(record, dict)
            self.assertListEqual(list(record.keys()), expected_fields)

