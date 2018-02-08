from os import path
import datetime

from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Point
from django.utils import timezone
from django_dynamic_fixture import G
from rest_framework import status

from main.models import Dataset, Site, Record
from main.tests.api import helpers


class TestPermission(helpers.BaseUserTestCase):
    # TODO
    pass


class TestGenericRecord(helpers.BaseUserTestCase):
    def _more_setup(self):
        self.fields = [
            {
                "name": "Column A",
                "type": "string",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
            {
                "name": "Column B",
                "type": "string",
                "constraints": helpers.REQUIRED_CONSTRAINTS
            }
        ]
        self.data_package = helpers.create_data_package_from_fields(self.fields)
        self.ds = G(Dataset,
                    project=self.project_1,
                    type=Dataset.TYPE_GENERIC,
                    data_package=self.data_package)
        self.url = reverse('api:dataset-upload', kwargs={'pk': self.ds.pk})

    def test_upload_csv_happy_path(self):
        csv_data = [
            ['Column A', 'Column B'],
            ['A1', 'B1'],
            ['A2', 'B2']
        ]
        file_ = helpers.rows_to_csv_file(csv_data)
        client = self.custodian_1_client
        self.assertEquals(0, self.ds.record_queryset.count())
        file_name = path.basename(file_)
        with open(file_) as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # The records should be saved in order of the row
            qs = self.ds.record_queryset.order_by('pk')
            self.assertEquals(len(csv_data) - 1, qs.count())

            index = 0
            record = qs[index]
            expected_data = {
                'Column A': 'A1',
                'Column B': 'B1',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            index = 1
            record = qs[index]
            expected_data = {
                'Column A': 'A2',
                'Column B': 'B2',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            self.assertEquals(self.project_1.record_count, len(csv_data) - 1)
            self.assertEquals(self.ds.record_count, len(csv_data) - 1)

    def test_upload_xlsx_happy_path(self):
        csv_data = [
            ['Column A', 'Column B'],
            ['A1', 'B1'],
            ['A2', 'B2']
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        client = self.custodian_1_client
        self.assertEquals(0, self.ds.record_queryset.count())
        file_name = path.basename(file_)
        with open(file_, 'rb') as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # The records should be saved in order of the row
            qs = self.ds.record_queryset.order_by('pk')
            self.assertEquals(len(csv_data) - 1, qs.count())

            index = 0
            record = qs[index]
            expected_data = {
                'Column A': 'A1',
                'Column B': 'B1',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            index = 1
            record = qs[index]
            expected_data = {
                'Column A': 'A2',
                'Column B': 'B2',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            self.assertEquals(self.project_1.record_count, len(csv_data) - 1)
            self.assertEquals(self.ds.record_count, len(csv_data) - 1)

    def test_upload_blank_column(self):
        """ Blank column should be ignored"""
        csv_data = [
            ['Column A', '', '   ', 'Column B'],
            ['A1', '', 'something', 'B1'],
            ['A2', '', 'something', 'B2']
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        client = self.custodian_1_client
        self.assertEquals(0, self.ds.record_queryset.count())
        file_name = path.basename(file_)
        with open(file_, 'rb') as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # The records should be saved in order of the row
            qs = self.ds.record_queryset.order_by('pk')
            self.assertEquals(len(csv_data) - 1, qs.count())
            index = 0
            record = qs[index]
            expected_data = {
                'Column A': 'A1',
                'Column B': 'B1',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            index = 1
            record = qs[index]
            expected_data = {
                'Column A': 'A2',
                'Column B': 'B2',
            }
            self.assertEquals(expected_data, record.data)
            # test that source_info contains the file_name and row_counter
            source_info = record.source_info
            self.assertIsNotNone(source_info)
            expected_info = {
                'file_name': file_name,
                'row': index + 2
            }
            self.assertEqual(source_info, expected_info)

            self.assertEquals(self.project_1.record_count, len(csv_data) - 1)
            self.assertEquals(self.ds.record_count, len(csv_data) - 1)

    def test_unicode(self):
        """
        Test that unicode characters works
        """
        csv_data = [
            [u'Column A', u'Column B'],
            [u'Some char: \u1234', u'The euro char: \u20ac']
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        client = self.custodian_1_client
        self.assertEquals(0, self.ds.record_queryset.count())
        with open(file_, 'rb') as fp:
            data = {
                'file': fp,
                'strict': False
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # The records should be saved in order of the row
            qs = self.ds.record_queryset.order_by('pk')
            self.assertEquals(len(csv_data) - 1, qs.count())

            index = 0
            record = qs[index]
            expected_data = {
                'Column A': u'Some char: \u1234',
                'Column B': u'The euro char: \u20ac',
            }
            self.assertEquals(expected_data, record.data)

    def test_headers_are_trimmed_csv(self):
        """
        Test that if the user upload a csv with columns containing heading or trailing space, the parser will trimmed it and
        then compare to schema.
        """
        fields = ['What', 'When', 'Who']
        dataset = self._create_dataset_from_rows([
            fields
        ])
        schema = dataset.schema
        self.assertEquals(schema.headers, fields)

        # upload record
        csv_data = [
            ['What ', ' When', ' Who  '],
            ['Something', '2018-02-01', 'me'],
        ]
        file_ = helpers.rows_to_csv_file(csv_data)
        client = self.custodian_1_client
        url = reverse('api:dataset-upload', kwargs={'pk': dataset.pk})
        with open(file_) as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)

            # verify stored data
            record = dataset.record_queryset.first()
            self.assertEquals(record.data.get('What'), 'Something')
            self.assertEquals(record.data.get('When'), '2018-02-01')
            self.assertEquals(record.data.get('Who'), 'me')
            # verify that the fields with space doesn't exists
            for f in csv_data[0]:
                self.assertIsNone(record.data.get(f))

    def test_headers_are_trimmed_xlsx(self):
        """
        Same as above but with an xlsx file
        """
        fields = ['What', 'When', 'Who']
        dataset = self._create_dataset_from_rows([
            fields
        ])
        schema = dataset.schema
        self.assertEquals(schema.headers, fields)

        # upload record
        csv_data = [
            ['What ', ' When', ' Who  '],
            ['Something', '2018-02-01', 'me'],
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        client = self.custodian_1_client
        url = reverse('api:dataset-upload', kwargs={'pk': dataset.pk})
        with open(file_) as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)

            # verify stored data
            record = dataset.record_queryset.first()
            self.assertEquals(record.data.get('What'), 'Something')
            self.assertEquals(record.data.get('When'), '2018-02-01')
            self.assertEquals(record.data.get('Who'), 'me')
            # verify that the fields with space doesn't exists
            for f in csv_data[0]:
                self.assertIsNone(record.data.get(f))


class TestObservation(helpers.BaseUserTestCase):
    all_fields_nothing_required = [
        {
            "name": "What",
            "type": "string",
        },
        {
            "name": "When",
            "type": "date",
            "format": "any",
            "biosys": {
                'type': 'observationDate'
            }
        },
        {
            "name": 'Site',
            "type": "string",
            "biosys": {
                'type': 'siteCode'
            }
        },
        {
            "name": "Latitude",
            "type": "number",
            "biosys": {
                "type": "latitude"
            },
            "constraints": {
                "minimum": -90.0,
                "maximum": 90.0,
            }
        },
        {
            "name": "Longitude",
            "type": "number",
            "biosys": {
                "type": "longitude"
            },
            "constraints": {
                "minimum": -180.0,
                "maximum": 180.0,
            }
        },
        {
            "name": "Northing",
            "type": "number",
            "biosys": {
                "type": "northing"
            }
        },
        {
            "name": "Easting",
            "type": "number",
            "biosys": {
                "type": "easting"
            }
        },
        {
            "name": "Datum",
            "type": "string",
        },
        {
            "name": "Zone",
            "type": "integer",
        }
    ]

    def _more_setup(self):
        self.project = self.project_1
        self.client = self.custodian_1_client
        self.dataset = self._create_dataset_with_schema(
            self.project,
            self.client,
            self.all_fields_nothing_required,
            Dataset.TYPE_OBSERVATION
        )
        self.url = reverse('api:dataset-upload', kwargs={'pk': self.dataset.pk})
        # create a site
        site_geometry = Point(115.76, -32.0)
        payload = {
            'project': self.project.pk,
            'name': 'Cottesloe',
            'code': 'COT',
            'geometry': site_geometry.geojson
        }
        url = reverse('api:site-list')
        resp = self.client.post(url, data=payload, format='json')
        self.assertEquals(resp.status_code, status.HTTP_201_CREATED)
        self.site = Site.objects.filter(pk=resp.json().get('id')).first()
        self.assertIsNotNone(self.site)
        self.assertEquals(self.site.code, 'COT')

    def test_site_no_date(self):
        csv_data = [
            ['What', 'Site'],
            ['No Date', self.site.code]
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        client = self.custodian_1_client
        with open(file_, 'rb') as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            records = self.dataset.record_queryset.all()
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.site, self.site)
            self.assertIsNone(record.datetime)
            self.assertEquals(record.geometry, self.site.geometry)

    def test_site_with_date(self):
        csv_data = [
            ['What', 'Site', 'When'],
            ['No Date', self.site.code, '04/06/2017']
        ]
        file_ = helpers.rows_to_xlsx_file(csv_data)
        client = self.custodian_1_client
        with open(file_, 'rb') as fp:
            data = {
                'file': fp,
                'strict': True  # upload in strict mode
            }
            resp = client.post(self.url, data=data, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            records = self.dataset.record_queryset.all()
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.site, self.site)
            expected_date = datetime.date(2017, 6, 4)
            self.assertEqual(timezone.localtime(record.datetime).date(), expected_date)
            self.assertEquals(record.geometry, self.site.geometry)
