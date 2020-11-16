from django.urls import reverse
from rest_framework import status

from main.models import Dataset
from main.tests.api import helpers
from main.tests.test_data_package import (
    clone,
    GENERIC_DATA_PACKAGE,
    LAT_LONG_OBSERVATION_DATA_PACKAGE,
    SPECIES_OBSERVATION_DATA_PACKAGE,
)


class TestPermissions(helpers.BaseUserTestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin, data_engineer
    Create: admin, data_engineer
    Delete: admin, data_engineer
    """

    def test_get(self):
        dataset = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client, helpers.GENERIC_SCHEMA)
        urls = [
            reverse('api:dataset-list'),
            reverse('api:dataset-detail', kwargs={'pk': dataset.pk})
        ]
        access = {
            "forbidden": [
                self.anonymous_client
            ],
            "allowed": [
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client,
                self.admin_client
            ]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.get(url).status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        # authenticated
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.get(url).status_code,
                    status.HTTP_200_OK
                )

    def test_create(self):
        """
        Admin and data engineers
        :return:
        """
        data_package = clone(GENERIC_DATA_PACKAGE)
        project = self.project_1
        urls = [reverse('api:dataset-list')]
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': data_package
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_2_client,
                self.custodian_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
                self.data_engineer_1_client
            ]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                # name must be unique
                data['name'] += '1'
                count = Dataset.objects.count()
                resp = client.post(url, data, format='json')
                self.assertEqual(
                    resp.status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(Dataset.objects.count(), count + 1)

    def test_bulk_create_forbidden(self):
        """
        Bulk create is not authorized for Datasets
        :return:
        """
        """
        Cannot create multiple dataset
        :return:
        """
        project = self.project_1
        urls = [reverse('api:dataset-list')]
        data = [
            {
                "name": "New1 for Unit test",
                "type": Dataset.TYPE_GENERIC,
                "project": project.pk,
                'data_package': clone(GENERIC_DATA_PACKAGE)
            },
            {
                "name": "New2 for Unit test",
                "type": Dataset.TYPE_GENERIC,
                "project": project.pk,
                'data_package': clone(GENERIC_DATA_PACKAGE)
            }
        ]
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_2_client,
                self.admin_client,
                self.custodian_1_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client
            ],
            "allowed": []
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                # name must be unique
                for ds in data:
                    ds['name'] += '1'
                count = Dataset.objects.count()
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )
                self.assertEqual(Dataset.objects.count(), count + 1)

    def test_update(self):
        """
        admin + data engineer of project for site 1
        :return:
        """
        ds = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client, helpers.GENERIC_SCHEMA)
        previous_name = ds.name
        updated_name = previous_name + "-updated"
        urls = [reverse('api:dataset-detail', kwargs={'pk': ds.pk})]
        data = {
            "name": updated_name,
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_2_client,
                self.custodian_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
                self.data_engineer_1_client
            ]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                ds.name = previous_name
                ds.save()
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                ds.refresh_from_db()
                self.assertEqual(ds.name, updated_name)

    def test_delete(self):
        """
        Currently admin + custodian
        :return:
        """
        ds = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client, helpers.GENERIC_SCHEMA)
        urls = [reverse('api:dataset-detail', kwargs={'pk': ds.pk})]
        data = None
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_2_client,
                self.custodian_1_client,
                self.data_engineer_2_client
            ],
            "allowed": [
                self.admin_client,
                self.data_engineer_1_client
            ]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                ds.save()
                count = Dataset.objects.count()
                self.assertEqual(
                    client.delete(url, data, format='json').status_code,
                    status.HTTP_204_NO_CONTENT
                )
                self.assertEqual(Dataset.objects.count(), count - 1)

    def test_options(self):
        urls = [
            reverse('api:dataset-list'),
            reverse('api:dataset-detail', kwargs={'pk': 1})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
                self.admin_client,
                self.data_engineer_1_client,
                self.data_engineer_2_client
            ]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.options(url).status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        # authenticated
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.options(url).status_code,
                    status.HTTP_200_OK
                )

    def test_options_model_choices(self):
        """
        Test that the options request return model choices for dataset type
        :return:
        """
        url = reverse('api:dataset-list')
        client = self.admin_client
        resp = client.options(url)
        self.assertEqual(status.HTTP_200_OK, resp.status_code)
        data = resp.json()
        choices = data.get('actions', {}).get('POST', {}).get('type', {}).get('choices', None)
        self.assertTrue(choices)
        expected = [{'value': d[0], 'display_name': d[1]} for d in Dataset.TYPE_CHOICES]
        self.assertEqual(expected, choices)


class TestDataPackageValidation(helpers.BaseUserTestCase):
    """
    Test that when create/update the datapackage validation is called
    """

    def test_generic_create_happy_path(self):
        data_package = clone(GENERIC_DATA_PACKAGE)

        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': data_package
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )

    def test_observation_create_happy_path(self):
        data_package = clone(LAT_LONG_OBSERVATION_DATA_PACKAGE)

        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_OBSERVATION,
            "project": project.pk,
            'data_package': data_package
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )

    def test_species_observation_create_happy_path(self):
        data_package = clone(SPECIES_OBSERVATION_DATA_PACKAGE)

        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_SPECIES_OBSERVATION,
            "project": project.pk,
            'data_package': data_package
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_201_CREATED
        )

    def test_create_none_error(self):
        """
        data package cannot be None
        :return:
        """
        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': None
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_update_none_error(self):
        """
        data package cannot be None
        :return:
        """
        project = self.project_1
        client = self.data_engineer_1_client
        ds = self._create_dataset_with_schema(project, self.data_engineer_1_client, helpers.GENERIC_SCHEMA)
        url = reverse('api:dataset-detail', kwargs={"pk": ds.pk})
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': None
        }
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_create_empty_error(self):
        """
        create
        data package cannot be empty
        :return:
        """
        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': {}
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_update_empty_error(self):
        """
        update
        data package cannot be empty
        :return:
        """
        project = self.project_1
        client = self.data_engineer_1_client
        ds = self._create_dataset_with_schema(project, self.data_engineer_1_client, helpers.GENERIC_SCHEMA)
        url = reverse('api:dataset-detail', kwargs={"pk": ds.pk})
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': {}
        }
        self.assertEqual(
            client.patch(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_no_schema_error(self):
        data_package = clone(GENERIC_DATA_PACKAGE)
        data_package['resources'][0]['schema'] = {}
        url = reverse('api:dataset-list')
        project = self.project_1
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_GENERIC,
            "project": project.pk,
            'data_package': {}
        }
        self.assertEqual(
            client.post(url, data, format='json').status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_easting_northing_no_zone(self):
        """
        In the case of a Easting/Northing only schema the zone is mandatory if the project datum is not a projected one
        (e.g: WSG84)
        """
        from main.constants import is_projected_srid

        project = self.project_1
        # project datum is not a Zone one
        self.assertEqual(project.datum, 4326)
        self.assertFalse(is_projected_srid(project.datum))

        fields_no_zone = [
            {
                "name": "Observation Date",
                "type": "date",
                "format": "any",
                "constraints": {
                    "required": True,
                }
            },
            {
                "name": "Northing",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                },
            },
            {
                "name": "Easting",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                },
            }
        ]
        url = reverse('api:dataset-list')
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_OBSERVATION,
            "project": project.pk,
            'data_package': helpers.create_data_package_from_fields(fields_no_zone)
        }
        resp = client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # check error message
        resp_data = resp.json()
        errors = resp_data.get('data_package')
        self.assertEqual(len(errors), 1)
        self.assertIn('Northing/easting coordinates require a zone', errors[0])

        # change the project datum
        project.datum = 28350  # 'GDA94 / MGA zone 50'
        project.save()
        self.assertTrue(is_projected_srid(project.datum))
        resp = client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_easting_northing_zone_not_required(self):
        """
        In the case of a Easting/Northing only schema the zone is mandatory if the project datum is not a projected one
        (e.g: WSG84)
        """
        from main.constants import is_projected_srid

        project = self.project_1
        # project datum is not a Zone one
        self.assertEqual(project.datum, 4326)
        self.assertFalse(is_projected_srid(project.datum))

        fields = [
            {
                "name": "Observation Date",
                "type": "date",
                "format": "any",
                "constraints": {
                    "required": True,
                }
            },
            {
                "name": "Northing",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                },
            },
            {
                "name": "Easting",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                },
            },
            {
                "name": "Zone",
                "type": "number",
                "format": "default",
            }
        ]
        url = reverse('api:dataset-list')
        client = self.data_engineer_1_client
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_OBSERVATION,
            "project": project.pk,
            'data_package': helpers.create_data_package_from_fields(fields)
        }
        resp = client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # check error message
        resp_data = resp.json()
        errors = resp_data.get('data_package')
        self.assertEqual(len(errors), 1)
        self.assertIn('Northing/easting coordinates require a zone', errors[0])

        # add required constraints
        fields[3]['constraints'] = {'required': True}
        data = {
            "name": "New for Unit test",
            "type": Dataset.TYPE_OBSERVATION,
            "project": project.pk,
            'data_package': helpers.create_data_package_from_fields(fields)
        }
        resp = client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


class TestRecordsView(helpers.BaseUserTestCase):
    """
    Test API access to records from dataset
    """
    schema_fields = [
        {
            "name": "What",
            "type": "string",
            "constraints": helpers.REQUIRED_CONSTRAINTS
        },
        {
            "name": "When",
            "type": "date",
            "constraints": helpers.NOT_REQUIRED_CONSTRAINTS,
            "format": "any",
            "biosys": {
                'type': 'observationDate'
            }
        },
        {
            "name": "Where",
            "type": "string",
            "constraints": helpers.REQUIRED_CONSTRAINTS
        },
        {
            "name": "Who",
            "type": "string",
            "constraints": helpers.REQUIRED_CONSTRAINTS
        },
    ]

    def _more_setup(self):
        self.project = self.project_1
        self.client = self.data_engineer_1_client
        self.dataset = self._create_dataset_with_schema(self.project, self.client, self.schema_fields)
        self.url = reverse('api:dataset-records', kwargs={'pk': self.dataset.pk})

    def test_permissions_get(self):
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
        }
        for client in access['forbidden']:
            self.assertIn(
                client.get(self.url).status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
            )
        # authenticated
        for client in access['allowed']:
            self.assertEqual(
                client.get(self.url).status_code,
                status.HTTP_200_OK
            )

    def test_permissions_delete(self):
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.custodian_1_client, self.admin_client]
        }
        for client in access['forbidden']:
            self.assertIn(
                client.delete(self.url, data=[], format='json').status_code,
                [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
            )
        # authenticated
        for client in access['allowed']:
            self.assertEqual(
                client.delete(self.url, data=[], format='json').status_code,
                status.HTTP_204_NO_CONTENT
            )

    def test_not_allowed_methods(self):
        not_allowed = ['post', 'put', 'patch']
        for method in not_allowed:
            func = getattr(self.client, method)
            if callable(func):
                self.assertEqual(
                    func(self.url, data=None, format='json').status_code,
                    status.HTTP_405_METHOD_NOT_ALLOWED
                )

    def test_bulk_delete_list(self):
        # create some records
        record_pks = []
        for i in range(1, 4):
            record_data = {
                'What': str(i)
            }
            record_pks.append(self._create_record(self.client, self.dataset, record_data).pk)
        # verify list
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), len(record_pks))

        # delete the first 2
        deleted_pks = record_pks[:2]
        expected_remaining_pks = record_pks[2:]
        resp = self.client.delete(self.url, data=deleted_pks, format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # ask the list again
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        existing_pks = [r['id'] for r in resp.json()]
        self.assertEqual(sorted(existing_pks), sorted(expected_remaining_pks))

    def test_bulk_delete_all(self):
        # create some records
        record_pks = []
        for i in range(1, 4):
            record_data = {
                'What': str(i)
            }
            record_pks.append(self._create_record(self.client, self.dataset, record_data).pk)
        # verify list
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), len(record_pks))

        # delete them all
        resp = self.client.delete(self.url, data='all', format='json')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # ask the list again
        resp = self.client.get(self.url, data=None, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)


class TestDatasetRecordsSearchAndOrdering(helpers.BaseUserTestCase):

    def _more_setup(self):
        self.client = self.custodian_1_client

    def test_server_side_search(self):
        rows = [
            ['When', 'Species', 'How Many', 'Latitude', 'Longitude', 'Comments'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-02', 'Canis dingo', 2, -32.0, 115.75, 'Watch out kids'],
            ['2018-02-10', 'Unknown', 3, -32.0, 115.75, 'Canis?'],
        ]
        dataset = self._create_dataset_and_records_from_rows(rows)

        url = reverse('api:dataset-records', kwargs={'pk': dataset.pk})

        # test fetch all records for dataset
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 4)

        # test fetching records in dataset using specific search term specific term.
        # The search should search on all the columns
        search = 'Canis'
        expected_number_of_records = 3  # 2 records with canis in the species and one in comments
        resp = self.client.get(url + '?search=' + search, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(len(resp.json()), expected_number_of_records)

    def test_server_side_ordering_string(self):
        rows = [
            ['When', 'Species', 'How Many', 'Latitude', 'Longitude', 'Comments'],
            ['2018-02-07', 'Canis lupus', 1, -32.0, 115.75, ''],
            ['2018-01-12', 'Chubby bat', 10, -32.0, 115.75, 'Awesome'],
            ['2018-02-10', 'Unknown', 2, -32.0, 115.75, 'Canis?'],
            ['2018-02-02', 'Canis dingo', 2, -32.0, 115.75, 'Watch out kids'],
        ]
        dataset = self._create_dataset_and_records_from_rows(rows)

        url = reverse('api:dataset-records', kwargs={'pk': dataset.pk})

        # check unordered request is not ordered by family
        resp = self.client.get(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_response = resp.json()
        self.assertEqual(len(resp.json()), 4)

        species = [row[1] for row in rows[1:]]
        sorted_species = sorted(species)
        self.assertNotEqual(species, sorted_species)

        record_species = [record['data']['Species'] for record in json_response]
        self.assertNotEqual(record_species, sorted_species)

        # check is request ordered by family is ordered by family in alphabetical order
        resp = self.client.get(url + '?ordering=Species', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_response = resp.json()
        self.assertEqual(len(json_response), 4)

        record_species = [record['data']['Species'] for record in json_response]
        self.assertEqual(record_species, sorted_species)

        # check is request ordered by family in descending order is ordered by family in reverse alphabetical order
        resp = self.client.get(url + '?ordering=-Species', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        json_response = resp.json()
        self.assertEqual(len(json_response), 4)

        record_species = [record['data']['Species'] for record in json_response]
        self.assertEqual(record_species, list(reversed(sorted_species)))

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

        url = reverse('api:dataset-records', kwargs={'pk': dataset.pk})

        resp = self.client.get(url + '?ordering=row', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_response = resp.json()
        self.assertEqual(len(json_response), 11)

        # row start at 2
        sorted_rows = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        record_rows = [record['source_info']['row'] for record in json_response]
        self.assertEqual(record_rows, sorted_rows)

        # check is request ordered by family in descending order is ordered by family in reverse alphabetical order
        resp = self.client.get(url + '?ordering=-row', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        json_response = resp.json()
        self.assertEqual(len(json_response), 11)

        record_rows = [record['source_info']['row'] for record in json_response]
        self.assertEqual(record_rows, list(reversed(sorted_rows)))
