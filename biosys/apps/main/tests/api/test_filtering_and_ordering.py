import json

from django.urls import reverse
from django.contrib.gis.geos import Polygon
from rest_framework import status

from main.models import Record, Dataset
from main.tests.api import helpers


class TestJsonSearchAndOrdering(helpers.BaseUserTestCase):

    def test_filter_dataset(self):
        dataset1 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Who'],
            ['Crashed the db', '2018-02-14', 'Serge'],
            ['Restored the db', '2018-02-14', 'Shay']
        ])

        dataset2 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-02-14', -32.0, 115.75],
            ['Chubby bat', '2017-05-18', -34.4, 116.78]
        ])

        client = self.custodian_1_client
        url = reverse('api:record-list')

        # no filters
        resp = client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 4)
        expected_whats = sorted(['Crashed the db', 'Restored the db', 'Canis lupus', 'Chubby bat'])
        self.assertEqual(sorted([r['data']['What'] for r in records]), expected_whats)

        # dataset__id
        expected_dataset = dataset1
        url = reverse('api:record-list')
        resp = client.get(url, {'dataset__id': expected_dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 2)
        expected_whats = sorted(['Crashed the db', 'Restored the db'])
        self.assertEqual(sorted([r['data']['What'] for r in records]), expected_whats)

        # dataset__name
        expected_dataset = dataset2
        resp = client.get(url, {'dataset__name': expected_dataset.name})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 2)
        expected_whats = sorted(['Canis lupus', 'Chubby bat'])
        self.assertEqual(sorted([r['data']['What'] for r in records]), expected_whats)

    def test_search_in_json_data(self):
        """
        Test that if we provide a dataset and a search parameters we can search through the data json field
        :return:
        """
        dataset1 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Who'],
            ['Crashed the db', '2018-02-14', 'Serge'],
            ['Restored the db', '2018-02-14', 'Shay']
        ])

        dataset2 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-02-14', -32.0, 115.75],
            ['Chubby bat', '2017-05-18', -34.4, 116.78],
            ['Chubby Serge', '2017-05-18', -34.4, 116.78]
        ])

        client = self.custodian_1_client
        url = reverse('api:record-list')

        # search Serge in dataset1
        resp = client.get(url, {'search': 'Serge', 'dataset__id': dataset1.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 1)
        record = records[0]
        expected_data = sorted(['Crashed the db', '2018-02-14', 'Serge'])
        self.assertEqual(sorted(list(record['data'].values())), expected_data)

        # search serge in dataset2 case insensitive
        resp = client.get(url, {'search': 'Serge', 'dataset__id': dataset2.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 1)
        record = records[0]
        expected_data = sorted(['Chubby Serge', '2017-05-18', '-34.4', '116.78'])
        record_values_as_string = [str(v) for v in record['data'].values()]
        self.assertEqual(sorted(list(record_values_as_string)), expected_data)

    def test_string_ordering_in_json_data(self):
        """
        Test that if we provide a dataset and an order parameter (field) we can order through the data json field
        for string
        :return:
        """
        dataset = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-02-14', -32.0, 115.75],
            ['Zebra', '2017-01-01', -34.7, 115.75],
            ['Chubby bat', '2017-05-18', -34.4, 116.78],
            ['Alligator', '2017-05-18', -34.4, 116.78]
        ])

        client = self.custodian_1_client
        url = reverse('api:record-list')

        # order by What asc
        ordering = 'What'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 4)
        expected_whats = sorted(['Alligator', 'Canis lupus', 'Chubby bat', 'Zebra'])
        self.assertEqual([r['data']['What'] for r in records], expected_whats)

        # order by What desc
        ordering = '-What'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 4)
        expected_whats = sorted(['Alligator', 'Canis lupus', 'Chubby bat', 'Zebra'], reverse=True)
        self.assertEqual([r['data']['What'] for r in records], expected_whats)

        # test that the ordering is case sensitive
        ordering = 'what'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 4)
        expected_whats = sorted(['Alligator', 'Canis lupus', 'Chubby bat', 'Zebra'])
        self.assertNotEqual([r['data']['What'] for r in records], expected_whats)

    def test_server_side_ordering_row_number(self):
        """
        Test that we can order by the source_info['row'] (row number in the csv or xlsx) and that the
        sort in numeric based not char based (10 is after 9)
        """
        # create 11 records (data not important)
        rows = [
            ['When', 'Species', 'How Many', 'Latitude', 'Longitude', 'Comments'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-10', 'Unknown', 2, -32.0, 115.75, 'Canis?'],
            ['2018-02-02', 'Canis dingo', 2, -32.0, 115.75, 'Watch out kids'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-10', 'Unknown', 2, -32.0, 115.75, 'Canis?'],
            ['2018-02-02', 'Canis dingo', 2, -32.0, 115.75, 'Watch out kids'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-10', 'Unknown', 2, -32.0, 115.75, 'Canis?'],
        ]
        dataset = self._create_dataset_and_records_from_rows(rows)
        client = self.custodian_1_client
        url = reverse('api:record-list')
        ordering = 'row'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_response = resp.json()
        self.assertEqual(len(json_response), 11)

        # row start at 2
        sorted_rows = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        record_rows = [record['source_info']['row'] for record in json_response]
        self.assertEqual(record_rows, sorted_rows)

        # check is request ordered by family in descending order is ordered by family in reverse alphabetical order
        ordering = '-row'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_response = resp.json()
        self.assertEqual(len(json_response), 11)

        record_rows = [record['source_info']['row'] for record in json_response]
        self.assertEqual(record_rows, list(reversed(sorted_rows)))

    def test_numeric_ordering_in_json_data_from_upload_end_point(self):
        """
        Assuming we have a schema that contains a numeric field (integer or number types).
        Querying an order on this field should return a numerical order not string (10, after 9)
        This test uses the upload end_point
        """
        dataset = self._create_dataset_and_records_from_rows([
            ['What', 'How Many'],
            ['Canis lupus', 7],
            ['Zebra', 1],
            ['Chubby bat', 9],
            ['Alligator', 10]
        ])
        # check that we have a field of type integer
        self.assertEqual(dataset.schema.get_field_by_name('How Many').type, 'integer')

        client = self.custodian_1_client
        url = reverse('api:record-list')

        ordering = 'How Many'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 4)
        expected = [('Zebra', 1), ('Canis lupus', 7), ('Chubby bat', 9), ('Alligator', 10)]
        self.assertEqual([(r['data']['What'], r['data']['How Many']) for r in records], expected)

    def test_numeric_ordering_in_json_data_from_post_end_point(self):
        """
        Assuming we have a schema that contains a numeric field (integer or number types).
        Querying an order on this field should return a numerical order not string (10, after 9)
        This test uses the api POST record/ end_point with floats instead of integers.
        """
        weights = [23.6, 123.4, 2.6, 203.4]
        # sorted float list should return [2.6, 23.6, 123.4, 203.4]
        # while a string sorted should return ['123.4', '2.6', '203.4', '23.6']
        float_sorted = sorted(weights)
        string_sorted = sorted([str(w) for w in weights])
        self.assertNotEqual(float_sorted, [float(s) for s in string_sorted])

        dataset = self._create_dataset_from_rows([
            ['What', 'Weight'],
            ['Canis lupus', weights[0]],
            ['Zebra', weights[1]],
            ['Chubby bat', weights[2]],
            ['Alligator', weights[3]]
        ])
        # check that we have a field of type integer
        self.assertEqual(dataset.schema.get_field_by_name('Weight').type, 'number')
        # post some records
        records_data = [
            {
                'What': 'Canis lupus',
                'Weight': weights[0]
            },
            {
                'What': 'Zebra',
                'Weight': weights[1]
            },
            {
                'What': 'Chubby bat',
                'Weight': weights[2]
            },
            {
                'What': 'Alligator',
                'Weight': weights[3]
            },
        ]
        records = []
        for record_data in records_data:
            records.append(self._create_record(self.custodian_1_client, dataset, record_data))
        client = self.custodian_1_client
        url = reverse('api:record-list')

        ordering = 'Weight'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 4)
        expected = [('Chubby bat', 2.6), ('Canis lupus', 23.6), ('Zebra', 123.4), ('Alligator', 203.4)]
        self.assertEqual([(r['data']['What'], r['data']['Weight']) for r in records], expected)

        # revert ordering
        ordering = '-Weight'
        resp = client.get(url, {'ordering': ordering, 'dataset__id': dataset.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 4)
        # reverse expected
        expected = expected[::-1]
        self.assertEqual([(r['data']['What'], r['data']['Weight']) for r in records], expected)

    def test_filter_id__in(self):
        """
        Test the id__in filter.
        Note: the filter parameter has to be a comma-separated list of ids, e.g: &id__in=1,2,3,4
        Not supported:
        - &id__in=[1,2,3,4]    (square bracket)
        - &id__in=1&id__in=2&id__in=3  (repeated key)
        """
        self._create_dataset_and_records_from_rows([
            ['What', 'Comment'],
            ['aaaa', 'AAAA'],
            ['bbbb', 'BBBB'],
            ['cccc', 'CCCC'],
            ['dddd', 'DDDD'],
        ])
        record_ids = list(Record.objects.values_list('id', flat=True))
        self.assertTrue(len(record_ids) >= 4)
        url = reverse('api:record-list')
        client = self.custodian_1_client

        # Test 2 records (first and last)
        expected_ids = [record_ids[0], record_ids[-1]]
        params = {
            'id__in': ','.join([str(i) for i in expected_ids])
        }
        resp = client.get(url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(2, len(records))
        self.assertEqual(sorted([r['id'] for r in records]), sorted(expected_ids))

        # Test only one value
        expected_id = record_ids[1]
        params = {
            'id__in': expected_id
        }
        resp = client.get(url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(1, len(records))
        self.assertEqual(records[0]['id'], expected_id)

        # Test blank returns all records (filter disabled)
        params = {
            'id__in': ''
        }
        resp = client.get(url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(record_ids), len(records))
        expected_ids = record_ids
        self.assertEqual(sorted([r['id'] for r in records]), sorted(expected_ids))

        # Test that square bracket doesn't work. It will return no records
        expected_ids = [record_ids[0], record_ids[-1]]
        params = {
            'id__in': json.dumps(expected_ids)  # '[1,4]'
        }
        resp = client.get(url, params)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(0, len(records))
        self.assertNotEqual(sorted([r['id'] for r in records]), sorted(expected_ids))

        # Test that repeated key doesn't work. It will return the last one
        expected_ids = [record_ids[0], record_ids[-1]]
        params = {
            'id__in': expected_ids,  # repeated key is the default url encoding for an array for the python test client
        }
        resp = client.get(url, params)
        self.assertEqual(resp.request['QUERY_STRING'], 'id__in={}&id__in={}'.format(record_ids[0], record_ids[-1]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(1, len(records))
        self.assertNotEqual(sorted([r['id'] for r in records]), sorted(expected_ids))
        self.assertEqual(records[0]['id'], record_ids[-1])

    def test_json_filter_contains(self):
        """
        Test the data__contains filter. Filter for key=value in the data JSONField.
        see:
        https://docs.djangoproject.com/en/2.0/ref/contrib/postgres/fields/#std:fieldlookup-hstorefield.contains
        """
        dataset = self._create_dataset_and_records_from_rows([
            ['Species Name', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-06-22', -32, 115.75],
            ['Koala', '2018-04-01', -35.0, 118],
            ['Koala', '2017-12-12', -33.333, 111.111],
            ['Eucalyptus robusta', '2017-11-23', -36.5, 120.5]
        ])
        self.assertEqual(dataset.type, Dataset.TYPE_SPECIES_OBSERVATION)
        url = reverse('api:record-list')
        client = self.custodian_1_client

        # search for koala
        expected_number = 2
        expected_species = 'Koala'
        param = {
            'data__contains': json.dumps({"Species Name": "Koala"})
        }
        resp = client.get(url, param, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), expected_number)
        for record in records:
            self.assertEqual(record['data']['Species Name'], expected_species)

        # test species + date
        expected_number = 1
        expected_species = 'Koala'
        param = {
            'data__contains': json.dumps({
                "Species Name": "Koala",
                "When": "2017-12-12"
            })
        }
        resp = client.get(url, param, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), expected_number)
        for record in records:
            self.assertEqual(record['data']['Species Name'], expected_species)
            self.assertEqual(record['data']['When'], "2017-12-12")

        # test numeric: latitude
        param = {
            'data__contains': json.dumps({"Latitude": -32})
        }
        resp = client.get(url, param, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['data']['Species Name'], 'Canis lupus')

        # test numeric: latitude with decimal .0
        param = {
            'data__contains': json.dumps({"Latitude": -32.0})
        }
        resp = client.get(url, param, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['data']['Species Name'], 'Canis lupus')

    def test_json_field_has_key(self):
        """
        Test the JSONField has_key lookup
        see:
        https://docs.djangoproject.com/en/2.0/ref/contrib/postgres/fields/#has-key
        """
        self._create_dataset_and_records_from_rows([
            ['Species Name', 'When', 'Latitude', 'Longitude'],
            ['Canis lupus', '2018-06-22', -32, 115.75],
            ['Koala', '2018-04-01', -35.0, 118],
            ['Koala', '2017-12-12', -33.333, 111.111],
            ['Eucalyptus robusta', '2017-11-23', -36.5, 120.5]
        ])

        # the second dataset has different column name but the 'When'
        self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Lat', 'Long'],
            ['Canis lupus', '2018-06-22', -32, 115.75],
            ['Koala', '2018-04-01', -35.0, 118],
            ['Koala', '2017-12-12', -33.333, 111.111],
            ['Eucalyptus robusta', '2017-11-23', -36.5, 120.5]
        ])
        url = reverse('api:record-list')
        client = self.custodian_1_client

        # search for every record with 'Species Name'
        expected_number = 4
        param = {
            'data__has_key': 'Species Name'
        }
        resp = client.get(url, param, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), expected_number)

        # search for every record with 'When'. Should return all the records
        expected_number = 4 * 2
        param = {
            'data__has_key': 'When'
        }
        resp = client.get(url, param, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.json()
        self.assertEqual(len(records), expected_number)


class TestSpatialFiltering(helpers.BaseUserTestCase):
    """
    Test ability to spatially filter records by providing a geometry__within
    Format is geojson.
    Only WGS84 supported
    This filter should be available for
    GET /records/  and GET /dataset/{id}/records/ end-points.
    """

    def setUp(self):
        super(TestSpatialFiltering, self).setUp()
        # lets's create some datasets
        self.perth_metro_ds = self._create_dataset_and_records_from_rows([
            ['Species Name', 'When', 'Latitude', 'Longitude', 'Where'],
            ['Canis lupus', '2018-06-22', -32, 115.75, 'Cottesloe'],
            ['Quokka', '2018-04-01', -32.011935, 115.517554, 'Rottnest Island'],
            ['Eucalyptus robusta', '2017-11-23', -31.959765, 115.8322754, 'Kings Park'],
            ['Chubby Bat', '2018-08-23', -32.531197, 115.725752, 'Mandurah']
        ])

        self.wa_north_ds = self._create_dataset_and_records_from_rows([
            ['Species Name', 'When', 'Latitude', 'Longitude', 'Where'],
            ['Canis lupus', '2018-06-22', -24.882248, 113.662995, 'Carnavon'],
            ['Quokka', '2018-04-01', -23.142194, 113.772222, 'Coral Bay'],
            ['Eucalyptus robusta', '2017-11-23', -21.177125, 119.765361, 'Marble Bar'],
            ['Chubby Bat', '2018-08-23', -17.962075, 122.234554, 'Broome']
        ])

    def test_get_record_happy(self):
        """
        Test GET /records/ endpoint
        """
        url = reverse('api:record-list')
        client = self.custodian_1_client

        # query with polygon of Perth roughly. That should exclude mandurah and all the north records
        west = 115.0
        east = 116.0
        north = -31.5
        south = -32.1  # north of Mandurah

        query = {
            'geometry__within': Polygon.from_bbox((west, south, east, north)).geojson
        }
        expected_records = [
            ['Canis lupus', '2018-06-22', -32, 115.75, 'Cottesloe'],
            ['Quokka', '2018-04-01', -32.011935, 115.517554, 'Rottnest Island'],
            ['Eucalyptus robusta', '2017-11-23', -31.959765, 115.8322754, 'Kings Park'],
        ]
        response = client.get(url, query)
        self.assertEqual(200, response.status_code)
        records = response.json()
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), len(expected_records))
        # check location
        self.assertEqual(
            sorted([r['data'].get('Where') for r in records]),
            ['Cottesloe', 'Kings Park', 'Rottnest Island']
        )

    def test_get_dataset_records_happy(self):
        """
        Same test as above but GET /dataset/{id}/records/
        """
        url = reverse('api:dataset-records', kwargs={'pk': self.perth_metro_ds.pk})
        client = self.custodian_1_client

        # query with polygon of Perth roughly. That should exclude mandurah and all the north records
        west = 115.0
        east = 116.0
        north = -31.5
        south = -32.1  # north of Mandurah

        query = {
            'geometry__within': Polygon.from_bbox((west, south, east, north)).geojson
        }
        expected_records = [
            ['Canis lupus', '2018-06-22', -32, 115.75, 'Cottesloe'],
            ['Quokka', '2018-04-01', -32.011935, 115.517554, 'Rottnest Island'],
            ['Eucalyptus robusta', '2017-11-23', -31.959765, 115.8322754, 'Kings Park'],
        ]
        response = client.get(url, query)
        self.assertEqual(200, response.status_code)
        records = response.json()
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), len(expected_records))
        # check location
        self.assertEqual(
            sorted([r['data'].get('Where') for r in records]),
            ['Cottesloe', 'Kings Park', 'Rottnest Island']
        )
