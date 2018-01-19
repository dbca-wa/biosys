from os import path

from datapackage import Package
from django.shortcuts import reverse
from rest_framework import status

from django.core.exceptions import ValidationError

from main.tests.api import helpers
from main.models import Dataset
from main import utils_data_package


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

    def test_generic_string_and_number_simple(self):
        """
        Test that the infer detect numbers and integers type
        """
        columns = ['Name', 'Age', 'Weight', 'Comments']
        csv_data = [
            columns,
            ['Frederic', 56, 80.5, 'a comment'],
            ['Hilda', 24, 56, '']
        ]
        client = self.custodian_1_client
        file_ = helpers.rows_to_xlsx_file(csv_data)
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

            field = schema.get_field_by_mame('Name')
            self.assertEquals(field.type, 'string')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_mame('Age')
            self.assertEquals(field.type, 'integer')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_mame('Weight')
            self.assertEquals(field.type, 'number')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')

            field = schema.get_field_by_mame('Comments')
            self.assertEquals(field.type, 'string')
            self.assertFalse(field.required)
            self.assertEquals(field.format, 'default')
