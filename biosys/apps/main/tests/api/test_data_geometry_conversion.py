from django.core.urlresolvers import reverse
from rest_framework import status

from main.models import Dataset, Record
from main.tests.api import helpers


class LatLongSchema(helpers.BaseUserTestCase):
    @staticmethod
    def schema_with_lat_long():
        schema_fields = [
            {
                "name": "What",
                "type": "string",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "When",
                "type": "date",
                "constraints": helpers.REQUIRED_CONSTRAINTS,
                "format": "any",
                "biosys": {
                    'type': 'observationDate'
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS,
            },
            {
                "name": "Longitude",
                "type": "number",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            },
            {
                "name": "Datum",
                "type": "string",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            }
        ]
        return helpers.create_schema_from_fields(schema_fields)

    def _create_dataset_with_schema(self, project, client, schema):
        resp = client.post(
            reverse('api:dataset-list'),
            data={
                "name": "Test site code geometry",
                "type": Dataset.TYPE_OBSERVATION,
                "project": project.pk,
                'data_package': helpers.create_data_package_from_schema(schema)
            },
            format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        dataset = Dataset.objects.filter(id=resp.json().get('id')).first()
        self.assertIsNotNone(dataset)
        return dataset

    def test_data_to_geometry(self):
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_lat_long()
        dataset = self._create_dataset_with_schema(project, client, schema)
        self.assertIsNotNone(dataset.schema.latitude_field)
        self.assertIsNotNone(dataset.schema.longitude_field)
        self.assertIsNotNone(dataset.schema.datum_field)

        # create record
        record_data = {
            'What': 'Cottesloe',
            'When': '20/06/2017',
            'Longitude': 115.75,
            'Latitude': -32.0,
            'Datum': 'WGS84'
        }
        payload = {
            'dataset': dataset.pk,
            'data': record_data
        }
        url = reverse('api:record-list')
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        record = Record.objects.filter(id=resp.json().get('id')).first()
        previous_record_geometry = record.geometry
        previous_record_data = record.data
        previous_record_dt = record.datetime

        url = reverse('api:data-to-geometry', kwargs={'pk': record.pk})
        # if we don't send any data, the server assume the record data and will return the geometry of this record
        payload = {
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get('content-type'), 'application/json')
        data = resp.json()
        self.assertTrue('geometry' in data)
        self.assertTrue('data' in data)
        # data should be the record data
        self.assertEqual(data['data'], record_data)
        expected_geometry = {
            'type': 'Point',
            'coordinates': [115.75, -32.0]
        }
        self.assertEqual(data['geometry'], expected_geometry)

        # we can send partial data as long the system has enough information
        payload = {
            'data': {
                'Longitude': 118,
                'Latitude': -34.0,
                'Datum': 'WGS84'
            }
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get('content-type'), 'application/json')
        data = resp.json()
        self.assertTrue('geometry' in data)
        self.assertTrue('data' in data)
        self.assertEqual(data['data'], payload['data'])
        expected_geometry = {
            'type': 'Point',
            'coordinates': [118, -34.0]
        }
        self.assertEqual(data['geometry'], expected_geometry)
        # record should be unchanged
        record.refresh_from_db()
        self.assertEqual(record.data, previous_record_data)
        self.assertEqual(record.geometry, previous_record_geometry)
        self.assertEqual(record.datetime, previous_record_dt)

        # send complete data
        payload = {
            'data': {
                'What': 'A new what',
                'When': '01/01/2015',
                'Longitude': 118,
                'Latitude': -34.0,
                'Datum': 'WGS84'
            }
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get('content-type'), 'application/json')
        data = resp.json()
        self.assertTrue('geometry' in data)
        self.assertTrue('data' in data)
        self.assertEqual(data['data'], payload['data'])
        expected_geometry = {
            'type': 'Point',
            'coordinates': [118, -34.0]
        }
        self.assertEqual(data['geometry'], expected_geometry)
        # record should be unchanged
        record.refresh_from_db()
        self.assertEqual(record.data, previous_record_data)
        self.assertEqual(record.geometry, previous_record_geometry)
        self.assertEqual(record.datetime, previous_record_dt)

    def test_geometry_to_data(self):
        project = self.project_1
        client = self.custodian_1_client
        schema = self.schema_with_lat_long()
        dataset = self._create_dataset_with_schema(project, client, schema)
        self.assertIsNotNone(dataset.schema.latitude_field)
        self.assertIsNotNone(dataset.schema.longitude_field)
        self.assertIsNotNone(dataset.schema.datum_field)

        # create record
        record_data = {
            'What': 'Cottesloe',
            'When': '20/06/2017',
            'Longitude': 115.75,
            'Latitude': -32.0,
            'Datum': 'WGS84'
        }
        payload = {
            'dataset': dataset.pk,
            'data': record_data
        }
        url = reverse('api:record-list')
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        record = Record.objects.filter(id=resp.json().get('id')).first()
        previous_record_geometry = record.geometry
        previous_record_data = record.data
        previous_record_dt = record.datetime

        url = reverse('api:geometry-to-data', kwargs={'pk': record.pk})
        # the geometry is required
        payload = {
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # send a geometry
        new_geometry = {
            'type': 'Point',
            'coordinates': [118, -34.0]
        }
        payload = {
            'geometry': new_geometry
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.get('content-type'), 'application/json')
        data = resp.json()
        self.assertTrue('geometry' in data)
        self.assertTrue('data' in data)
        expected_data = {
            'What': record_data['What'],
            'When': record_data['When'],
            'Longitude': 118.0,
            'Latitude': -34.0,
            'Datum': 'WGS84'
        }
        print(data['data'])
        for k, v in data['data'].items():
            self.assertIn(k, expected_data)
            self.assertEqual(v, expected_data[k])
        expected_geometry = new_geometry
        self.assertEqual(data['geometry'], expected_geometry)
        # record should be unchanged
        record.refresh_from_db()
        self.assertEqual(record.data, previous_record_data)
        self.assertEqual(record.geometry, previous_record_geometry)
        self.assertEqual(record.datetime, previous_record_dt)
