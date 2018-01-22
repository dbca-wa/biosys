import datetime as dt
from os import path

from datapackage import Package
from django.core.exceptions import ValidationError
from django.shortcuts import reverse
from rest_framework import status

from main import utils_data_package
from main.models import Dataset
from main.tests.api import helpers
from main.utils_data_package import BiosysSchema


class InferTestBase(helpers.BaseUserTestCase):

    def verify_biosys_dataset(self, data_package, dataset_type):
        """
        Verify that the dataset model validation is error free
        :param data_package:
        :param dataset_type:
        :return:
        """
        try:
            Dataset.validate_data_package(data_package, dataset_type)
        except ValidationError as e:
            self.fail('Dataset validation error: {}'.format(e))

    def verify_inferred_data(self, received):
        """
        Test that the data returned by the infer endpoint are valid and can be used to create a dataset through API
        :param received should be of the form
        {
          'name': 'dataset name'
          'type': 'generic'|'observation'|'species_observation'
          'data_package': {
             # a valid data package with schema
          }
        }
        """
        self.assertIn('name', received)
        # self.assertIsNotNone(received.get('name'))
        self.assertIn('type', received)
        self.assertIn(received.get('type'), ['generic', 'observation', 'species_observation'])

        # dataset
        self.verify_biosys_dataset(received.get('data_package'), received.get('type'))

        # TODO: implement the create data package with API
        # url = reverse('api:dataset-list')
        # client = self.admin_client
        # resp = client.post(url, received, format='json')
        # self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])


class TestGenericSchema(InferTestBase):
    def _more_setup(self):
        self.url = reverse('api:infer-dataset')

    def test_generic_string_and_number_simple_xls(self):
        """
        Test that the infer detect numbers and integers type
        """
        columns = ['Name', 'Age', 'Weight', 'Comments']
        rows = [
            columns,
            ['Frederic', 56, 80.5, 'a comment'],
            ['Hilda', 24, 56, '']
        ]
        client = self.custodian_1_client
        file_ = helpers.rows_to_xlsx_file(rows)
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp,
            }
            resp = client.post(self.url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # should be json
            self.assertEqual(resp.get('content-type'), 'application/json')
            received = resp.json()

            # name should be set with the file name
            self.assertIn('name', received)
            file_name = path.splitext(path.basename(fp.name))[0]
            self.assertEquals(file_name, received.get('name'))
            # type should be 'generic'
            self.assertIn('type', received)
            self.assertEquals('generic', received.get('type'))

            # data_package verification
            self.assertIn('data_package', received)
            self.verify_inferred_data(received)

            # verify schema
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            self.assertEquals(len(schema.fields), len(columns))
            self.assertEquals(schema.field_names, columns)

            field = schema.get_field_by_name('Name')
            self.assertEquals(field.type, 'string')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_name('Age')
            self.assertEquals(field.type, 'integer')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_name('Weight')
            self.assertEquals(field.type, 'number')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_name('Comments')
            self.assertEquals(field.type, 'string')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

    def test_generic_string_and_number_simple_csv(self):
        """
        Test that the infer detect numbers and integers type
        """
        columns = ['Name', 'Age', 'Weight', 'Comments']
        rows = [
            columns,
            ['Frederic', '56', '80.5', 'a comment'],
            ['Hilda', '24', '56', '']
        ]
        client = self.custodian_1_client
        file_ = helpers.rows_to_csv_file(rows)
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp,
            }
            resp = client.post(self.url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # should be json
            self.assertEqual(resp.get('content-type'), 'application/json')
            received = resp.json()

            # name should be set with the file name
            self.assertIn('name', received)
            file_name = path.splitext(path.basename(fp.name))[0]
            self.assertEquals(file_name, received.get('name'))
            # type should be 'generic'
            self.assertIn('type', received)
            self.assertEquals('generic', received.get('type'))

            # data_package verification
            self.assertIn('data_package', received)
            self.verify_inferred_data(received)

            # verify schema
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            self.assertEquals(len(schema.fields), len(columns))
            self.assertEquals(schema.field_names, columns)

            field = schema.get_field_by_name('Name')
            self.assertEquals(field.type, 'string')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_name('Age')
            self.assertEquals(field.type, 'integer')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_name('Weight')
            self.assertEquals(field.type, 'number')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_name('Comments')
            self.assertEquals(field.type, 'string')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

    def test_generic_date_iso_xls(self):
        """
        Scenario: date column with ISO string 'yyyy-mm-dd'
        Given that a column is provided with strings of form 'yyyy-mm-dd'
        Then the column type should be 'date'
        And the format should be 'any'
        """
        columns = ['What', 'When']
        rows = [
            columns,
            ['Something', '2018-01-19'],
            ['Another thing', dt.date(2017, 12, 29).isoformat()],
            ['Another thing', '2017-08-01']
        ]
        client = self.custodian_1_client
        file_ = helpers.rows_to_xlsx_file(rows)
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp,
            }
            resp = client.post(self.url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            received = resp.json()
            # data_package verification
            self.assertIn('data_package', received)
            self.verify_inferred_data(received)

            # verify schema
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            field = schema.get_field_by_name('What')
            self.assertEquals(field.type, 'string')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_name('When')
            self.assertEquals(field.type, 'date')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'any')

    def test_observation_with_lat_long_xls(self):
        """
        Scenario: File with column Latitude and Longitude
         Given that a column named Latitude and Longitude exists
         Then they should be of type 'number'
         And they should be set as required
         And they should be tagged with the appropriate biosys tag
         And the dataset type should be observation
        """
        columns = ['What', 'Latitude', 'Longitude']
        rows = [
            columns,
            ['Observation1', -32, 117.75],
            ['Observation with lat/long as string', '-32', '115.75']
        ]
        client = self.custodian_1_client
        file_ = helpers.rows_to_xlsx_file(rows)
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp,
            }
            resp = client.post(self.url, data=payload, format='multipart')
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            received = resp.json()
            # data_package verification
            self.assertIn('data_package', received)

            # verify fields attributes
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            lat_field = schema.get_field_by_name('Latitude')
            lon_field = schema.get_field_by_name('Longitude')
            self.assertEquals(lat_field.type, 'number')
            self.assertEquals(lon_field.type, 'number')
            self.assertTrue(lat_field.required)
            self.assertTrue(lon_field.required)
            # biosys types
            self.assertTrue(BiosysSchema(lat_field.get(BiosysSchema.BIOSYS_KEY_NAME)).is_latitude())
            self.assertTrue(BiosysSchema(lon_field.get(BiosysSchema.BIOSYS_KEY_NAME)).is_longitude())

            self.assertEquals(Dataset.TYPE_OBSERVATION, received.get('type'))
            # test biosys validity
            self.verify_inferred_data(received)