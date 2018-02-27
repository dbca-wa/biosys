import datetime as dt
from os import path
import json

from datapackage import Package
from django.core.exceptions import ValidationError
from django.shortcuts import reverse
from django.utils import six
from rest_framework import status

from main import utils_data_package
from main.models import Dataset
from main.tests.api import helpers
from main.utils_data_package import BiosysSchema
from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory
from main.api.views import InferDatasetView
from rest_framework.test import force_authenticate


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

        # Verify that we can create a dataset from the inference result.
        url = reverse('api:dataset-list')
        client = self.custodian_1_client
        project = self.project_1
        payload = {
            'project': project.pk,
            'name': received.get('name'),
            'type': received.get('type'),
            'data_package': received.get('data_package')
        }
        resp = client.post(url, payload, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])


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

    def test_mix_types_infer_most_plausible(self):
        """
        Scenario: column with more integers than string should be infer a type='integer'
        Given than a column contains 2 strings then 5 integers
        Then the column type should be 'integer'
        """
        columns = ['How Many']
        rows = [
            columns,
            [1],
            ['1 or 2'],
            ['3 or 4'],
            [2],
            [3],
            [4],
            [5]
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
            field = schema.get_field_by_name('How Many')
            self.assertEquals(field.type, 'integer')

    def test_csv_with_excel_content_type(self):
        """
        Often on Windows a csv file comes with an excel content-type (e.g: 'application/vnd.ms-excel')
        Test that we handle the case.
        """
        view = InferDatasetView.as_view()
        columns = ['Name', 'Age', 'Weight', 'Comments']
        rows = [
            columns,
            ['Frederic', '56', '80.5', 'a comment'],
            ['Hilda', '24', '56', '']
        ]
        file_ = helpers.rows_to_csv_file(rows)
        factory = APIRequestFactory()
        with open(file_, 'rb') as fp:
            payload = {
                'file': fp,
            }
            # In order to hack the Content-Type of the multipart form data we need to use the APIRequestFactory and work
            # with the view directly. Can't use the classic API client.
            # hack the content-type of the request.
            data, content_type = factory._encode_data(payload, format='multipart')
            if six.PY3:
                data = data.decode('utf-8')
            data = data.replace('Content-Type: text/csv', 'Content-Type: application/vnd.ms-excel')
            if six.PY3:
                data = data.encode('utf-8')
            request = factory.generic('POST', self.url, data, content_type=content_type)
            user = self.custodian_1_user
            token, _ = Token.objects.get_or_create(user=user)
            force_authenticate(request, user=self.custodian_1_user, token=token)
            resp = view(request).render()
            self.assertEquals(status.HTTP_200_OK, resp.status_code)
            # should be json
            self.assertEqual(resp.get('content-type'), 'application/json')
            if six.PY3:
                content = resp.content.decode('utf-8')
            else:
                content = resp.content
            received = json.loads(content)

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


class TestObservationSchema(InferTestBase):

    def _more_setup(self):
        self.url = reverse('api:infer-dataset')

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

    def test_observation_with_lat_long_datum_xls(self):
        """
        Scenario: File with column Latitude, Longitude and Datum
         Given that columns named Latitude, Longitude and Datum exists
         Then the dataset type should be inferred as Observation
         And latitude should be of type 'number', set as required and tag with biosys type latitude
         And longitude should be of type 'number', set as required and tag with biosys type longitude
         And datum should be of type 'string', set as not required and with biosys type datum
        """
        columns = ['What', 'Latitude', 'Longitude', 'Datum']
        rows = [
            columns,
            ['Observation1', -32, 117.75, 'WGS84'],
            ['Observation with lat/long as string', '-32', '115.75', None]
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
            # type observation
            self.assertEquals(Dataset.TYPE_OBSERVATION, received.get('type'))

            # verify fields attributes
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            lat_field = schema.get_field_by_name('Latitude')
            self.assertEquals(lat_field.type, 'number')
            self.assertTrue(lat_field.required)
            biosys = lat_field.get('biosys')
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.LATITUDE_TYPE_NAME)

            lon_field = schema.get_field_by_name('Longitude')
            self.assertEquals(lon_field.type, 'number')
            self.assertTrue(lon_field.required)
            biosys = lon_field.get('biosys')
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.LONGITUDE_TYPE_NAME)

            # datum
            datum_field = schema.get_field_by_name('Datum')
            self.assertEquals(datum_field.type, 'string')
            self.assertFalse(datum_field.required)
            biosys = datum_field.get('biosys')
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.DATUM_TYPE_NAME)

            # test that we can save the dataset back.
            self.verify_inferred_data(received)

    def test_observation_with_easting_northing_datum_xls(self):
        """
        Scenario: File with column Easting, Northing and Datum
         Given that a column named Easting , Northing and Datum exist
         Then the dataset type should be inferred as Observation
         And the type of Easting and Northing should be 'number'
         And Easting and Northing should be set as required
         And they should be tagged with the appropriate biosys tag
         And Datum should be of type string and required.
        """
        columns = ['What', 'Easting', 'Northing', 'Datum', 'Comments']
        rows = [
            columns,
            ['Something', 12563.233, 568932.345, 'WGS94', 'A dog'],
            ['Observation with easting/northing as string', '12563.233', '568932.345', 'WGS94', 'A dog']
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
            # should be an observation
            self.assertEquals(Dataset.TYPE_OBSERVATION, received.get('type'))
            # data_package verification
            self.assertIn('data_package', received)

            # verify fields attributes
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            east_field = schema.get_field_by_name('Easting')
            self.assertIsNotNone(east_field)
            self.assertEquals(east_field.type, 'number')
            self.assertTrue(east_field.required)
            biosys = east_field.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.EASTING_TYPE_NAME)

            north_field = schema.get_field_by_name('Northing')
            self.assertIsNotNone(north_field)
            self.assertEquals(north_field.type, 'number')
            self.assertTrue(north_field.required)
            biosys = north_field.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.NORTHING_TYPE_NAME)

            datum_field = schema.get_field_by_name('Datum')
            self.assertIsNotNone(datum_field)
            self.assertEquals(datum_field.type, 'string')
            self.assertTrue(datum_field.required)
            biosys = datum_field.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.DATUM_TYPE_NAME)

            # test that we can save the dataset as returned
            self.verify_inferred_data(received)

    def test_observation_with_easting_northing_zone_xls(self):
        """
        Scenario: File with column Easting, Northing and Zone
         Given that a column named Easting , Northing and Zone exist
         Then the dataset type should be inferred as Observation
         And the type of Easting and Northing should be 'number'
         And Easting and Northing should be set as required
         And they should be tagged with the appropriate biosys tag
         And Zone should be of type integer and required.
        """
        columns = ['What', 'Easting', 'Northing', 'Zone', 'Comments']
        rows = [
            columns,
            ['Something', 12563.233, 568932.345, 50, 'A dog'],
            ['Observation with easting/northing as string', '12563.233', '568932.345', 50, 'A dog']
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
            # should be an observation
            self.assertEquals(Dataset.TYPE_OBSERVATION, received.get('type'))
            # data_package verification
            self.assertIn('data_package', received)

            # verify fields attributes
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            east_field = schema.get_field_by_name('Easting')
            self.assertIsNotNone(east_field)
            self.assertEquals(east_field.type, 'number')
            self.assertTrue(east_field.required)
            biosys = east_field.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.EASTING_TYPE_NAME)

            north_field = schema.get_field_by_name('Northing')
            self.assertIsNotNone(north_field)
            self.assertEquals(north_field.type, 'number')
            self.assertTrue(north_field.required)
            biosys = north_field.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.NORTHING_TYPE_NAME)

            zone_field = schema.get_field_by_name('Zone')
            self.assertIsNotNone(zone_field)
            self.assertEquals(zone_field.type, 'integer')
            self.assertTrue(zone_field.required)
            biosys = zone_field.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.ZONE_TYPE_NAME)

            # test that we can save the dataset as returned
            self.verify_inferred_data(received)


class TestSpeciesObservation(InferTestBase):

    def _more_setup(self):
        self.url = reverse('api:infer-dataset')

    def test_observation_with_species_name_only_xls(self):
        """
        Scenario: File with column Latitude and Longitude and Species Name should be inferred as species observation
         Given that a column named Latitude and Longitude and Species Name exists
         Then the dataset type should be of type speciesObservation
         And the column 'Species Name' should be of type string
         And the column 'Species Name' should be set as 'required'
         And they should be tagged with the speciesName biosys tag.
        """
        columns = ['What', 'When', 'Latitude', 'Longitude', 'Species Name', 'Comments']
        rows = [
            columns,
            ['I saw a dog', '2018-02-02', -32, 117.75, 'Canis lupus', None],
            ['I saw a Chubby bat', '2017-01-02', -32, 116.7, 'Chubby bat', 'Amazing!'],
            ['I saw nothing', '2018-01-02', -32.34, 116.7, None, None],
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
            # should be a species observation
            self.assertEquals(Dataset.TYPE_SPECIES_OBSERVATION, received.get('type'))
            self.assertIn('data_package', received)
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            species_name_field = schema.get_field_by_name('Species Name')
            # field attributes
            self.assertIsNotNone(species_name_field)
            self.assertEquals(species_name_field.type, 'string')
            self.assertTrue(species_name_field.required)
            # biosys type
            biosys = species_name_field.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.SPECIES_NAME_TYPE_NAME)

            # test that we can create a dataset with the returned data
            self.verify_inferred_data(received)

    def test_observation_with_genus_and_species_only_xls(self):
        """
        Scenario: File with column Latitude, Longitude, Genus and Species should be inferred as species observation
         Given that a column named Latitude, Longitude, Genus and Species exists
         Then the dataset type should be of type speciesObservation
         And the column 'Genus' should be of type string, set as required and tag as biosys type genus
         And the column 'Species' should be of type string, set as required and tag as biosys type species
        """
        columns = ['What', 'When', 'Latitude', 'Longitude', 'Genus', 'Species', 'Comments']
        rows = [
            columns,
            ['I saw a dog', '2018-02-02', -32, 117.75, 'Canis', 'lupus', None],
            ['I saw a Chubby bat', '2017-01-02', -32, 116.7, 'Chubby', 'bat', 'Amazing!'],
            ['I saw nothing', '2018-01-02', -32.34, 116.7, None, None, None],
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
            # should be a species observation
            self.assertEquals(Dataset.TYPE_SPECIES_OBSERVATION, received.get('type'))
            self.assertIn('data_package', received)
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            # field attributes
            # genus
            genus = schema.get_field_by_name('Genus')
            self.assertIsNotNone(genus)
            self.assertEquals(genus.type, 'string')
            self.assertTrue(genus.required)
            biosys = genus.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.GENUS_TYPE_NAME)

            species = schema.get_field_by_name('Species')
            self.assertIsNotNone(species)
            self.assertEquals(species.type, 'string')
            self.assertTrue(species.required)
            biosys = species.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.SPECIES_TYPE_NAME)

            # test that we can create a dataset with the returned data
            self.verify_inferred_data(received)

    def test_observation_with_genus_species_infra_rank_and_infra_name_only_xls(self):
        """
        Scenario: File with column Latitude, Longitude, Genus, Species, Infraspecific Rank and Infraspecific Name
                  should be inferred as species observation
         Given that a column named Latitude, Longitude, Genus, Species Infraspecific Rank and Infraspecific Name exists
         Then the dataset type should be of type speciesObservation
         And the column 'Genus' should be of type string, set as required and tag as biosys type genus
         And the column 'Species' should be of type string, set as required and tag as biosys type species
         And the column 'Infraspecific Rank' should be of type string, set as not required and tag as biosys type InfraSpecificRank
         And the column 'Infraspecific Name' should be of type string, set as not required and tag as biosys type InfraSpecificName
        """
        columns = ['What', 'When', 'Latitude', 'Longitude', 'Genus', 'Species', 'Infraspecific Rank',
                   'Infraspecific Name', 'Comments']
        rows = [
            columns,
            ['I saw a dog', '2018-02-02', -32, 117.75, 'Canis', 'lupus', 'subsp. familiaris', '', None],
            ['I saw a Chubby bat', '2017-01-02', -32, 116.7, 'Chubby', 'bat', '', '', 'Amazing!'],
            ['I saw nothing', '2018-01-02', -32.34, 116.7, None, None, None, None, None],
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
            # should be a species observation
            self.assertEquals(Dataset.TYPE_SPECIES_OBSERVATION, received.get('type'))
            self.assertIn('data_package', received)
            schema_descriptor = Package(received.get('data_package')).resources[0].descriptor['schema']
            schema = utils_data_package.GenericSchema(schema_descriptor)
            # field attributes
            # genus
            genus = schema.get_field_by_name('Genus')
            self.assertIsNotNone(genus)
            self.assertEquals(genus.type, 'string')
            self.assertTrue(genus.required)
            biosys = genus.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.GENUS_TYPE_NAME)
            # species
            species = schema.get_field_by_name('Species')
            self.assertIsNotNone(species)
            self.assertEquals(species.type, 'string')
            self.assertTrue(species.required)
            biosys = species.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.SPECIES_TYPE_NAME)
            # infra rank
            infra_rank = schema.get_field_by_name('Infraspecific Rank')
            self.assertIsNotNone(infra_rank)
            self.assertEquals(infra_rank.type, 'string')
            self.assertFalse(infra_rank.required)
            biosys = infra_rank.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.INFRA_SPECIFIC_RANK_TYPE_NAME)
            # infra name
            infra_name = schema.get_field_by_name('Infraspecific Name')
            self.assertIsNotNone(infra_name)
            self.assertEquals(infra_name.type, 'string')
            self.assertFalse(infra_name.required)
            biosys = infra_name.get('biosys')
            self.assertIsNotNone(biosys)
            biosys_type = biosys.get('type')
            self.assertEquals(biosys_type, BiosysSchema.INFRA_SPECIFIC_NAME_TYPE_NAME)

            # test that we can create a dataset with the returned data
            self.verify_inferred_data(received)
