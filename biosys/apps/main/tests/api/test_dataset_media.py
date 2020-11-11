from django.urls import reverse
from rest_framework import status

from main.models import Media, Record, DatasetMedia, Dataset
from main.tests import factories
from main.tests.api import helpers


class TestPermissions(helpers.BaseUserTestCase):
    """
    Test Permissions
    GET: authenticated
    POST: admin, custodians
    PUT/PATCH: forbidden
    DELETE: admin, custodians
    """

    def setUp(self):
        super(TestPermissions, self).setUp()

        # create dataset and media media
        self.ds_1 = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 1')
        self.dataset_media_1 = factories.DatasetMediaFactory(dataset=self.ds_1)
        self.assertEqual(self.dataset_media_1.dataset.id, self.ds_1.id)

    def test_get(self):
        urls = [
            reverse('api:dataset-media-list'),
            reverse('api:dataset-media-detail', kwargs={'pk': self.dataset_media_1.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.data_engineer_1_client, self.admin_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.get(url).status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        for client in access['allowed']:
            for url in urls:
                self.assertEqual(
                    client.get(url).status_code,
                    status.HTTP_200_OK
                )

    def test_create(self):
        urls = [
            reverse('api:dataset-media-list'),
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_1_client,
                          self.data_engineer_2_client],
            "allowed": [self.admin_client, self.data_engineer_1_client]
        }
        for client in access['forbidden']:
            for url in urls:
                with open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
                    payload = {
                        'dataset': self.ds_1.pk,
                        'file': fp
                    }
                    self.assertIn(
                        client.post(url, data=payload, format='multipart').status_code,
                        [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                    )
        # authenticated
        for client in access['allowed']:
            for url in urls:
                with open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
                    payload = {
                        'dataset': self.ds_1.pk,
                        'file': fp
                    }
                    self.assertEqual(
                        client.post(url, data=payload, format='multipart').status_code,
                        status.HTTP_201_CREATED
                    )

    def test_put_patch(self):
        urls = [
            reverse('api:dataset-media-detail', kwargs={'pk': self.dataset_media_1.pk}),
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client,
                          self.admin_client, self.custodian_1_client],
            "allowed": []
        }
        for client in access['forbidden']:
            for url in urls:
                with open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
                    payload = {
                        'dataset': self.ds_1.pk,
                        'file': fp
                    }
                    self.assertIn(
                        client.put(url, data=payload, format='multipart').status_code,
                        [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                    )
                    self.assertIn(
                        client.patch(url, data=payload, format='multipart').status_code,
                        [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                    )
        # authenticated
        for client in access['allowed']:
            for url in urls:
                with open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
                    payload = {
                        'dataset': self.ds_1.pk,
                        'file': fp
                    }
                    self.assertEqual(
                        client.put(url, data=payload, format='multipart').status_code,
                        status.HTTP_200_OK
                    )
                    self.assertEqual(
                        client.patch(url, data=payload, format='multipart').status_code,
                        status.HTTP_200_OK
                    )

    def test_delete(self):
        urls = [reverse('api:dataset-media-detail', kwargs={'pk': self.dataset_media_1.pk})]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client,
                          self.data_engineer_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url).status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        for client in access['allowed']:
            for url in urls:
                self.assertIn(
                    client.delete(url).status_code,
                    [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND]
                )


class TestSerialization(helpers.BaseUserTestCase):

    def setUp(self):
        super(TestSerialization, self).setUp()

        # set up dataset and dataset media
        self.ds_1 = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client,
                                                     helpers.GENERIC_SCHEMA)
        self.dataset_media_1 = factories.DatasetMediaFactory(dataset=self.ds_1)
        self.assertEqual(self.dataset_media_1.dataset.id, self.ds_1.id)

    def test_returned_fields_format(self):
        """
        Should return a json response with the file as a url
        :return:
        """
        url = reverse('api:dataset-media-detail', kwargs={'pk': self.dataset_media_1.pk})
        client = self.data_engineer_1_client
        resp = client.get(url)
        self.assertEqual(resp['content-type'], 'application/json')
        data = resp.json()
        # should include the following keys
        expected_keys = ['id', 'dataset', 'file', 'created', 'filesize']
        received_keys = data.keys()
        for key in expected_keys:
            self.assertIn(key, received_keys)
        # dataset is returned as a pk
        self.assertEqual(data.get('dataset'), self.ds_1.pk)
        # file is return as a url
        url = data.get('file')
        self.assertIsNotNone(url)
        # validate url. Can't use the django URLValidator here it will fail because of the domain name.
        # Typical test url http://testserver/media/project_1/dataset_60/record_60/chubby-bat_{id}.png
        self.assertTrue(url.startswith('http://'))
        file_name = url.split('/').pop()
        self.assertTrue(file_name.startswith('chubby-bat'))
        self.assertTrue(file_name.endswith('.png'))

    def test_multipart_upload(self):
        """
        Test that we can upload a new dataset media using multipart form.
        """
        client = self.data_engineer_1_client
        url = reverse('api:dataset-media-list')
        format_ = 'multipart'
        dataset = self.ds_1
        # dataset should have one media already
        self.assertEqual(DatasetMedia.objects.filter(dataset=dataset).count(), 1)
        with open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
            payload = {
                'dataset': self.ds_1.pk,
                'file': fp
            }
            resp = client.post(url, data=payload, format=format_)
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            dataset.refresh_from_db()
            self.assertEqual(DatasetMedia.objects.filter(dataset=dataset).count(), 2)
            # retrieve list
            resp = client.get(url, format='json')
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            data = resp.json()
            self.assertEqual(len(data), 2)

    def test_json_base64_upload_no_type(self):
        """
        Test that we can upload a dataset media using json with pure base64 string as data (no data mime provided)
        also test that the serializer infer the file type
        """
        client = self.data_engineer_1_client
        url = reverse('api:dataset-media-list')
        dataset = self.ds_1
        # first delete all dataset media
        DatasetMedia.objects.filter(dataset=dataset).delete()
        b64s = factories.get_chubby_bat_img_base64()
        payload = {
            'dataset': dataset.id,
            'file': b64s
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # test that the file type (extension) has been rightly inferred
        data = resp.json()
        self.assertIn('file', data)
        file = data['file']
        # should be an url
        self.assertTrue(file.startswith('http://'))
        # expect png extension
        self.assertTrue(file.endswith('.png'))
        # compare image
        dataset_media = DatasetMedia.objects.filter(id=data['id']).first()
        self.assertIsNotNone(dataset_media)
        self.assertEqual(
            open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb').read(),
            open(dataset_media.path, 'rb').read()
        )

    def test_json_base64_upload_html_format(self):
        """
        Test that we can upload a dataset media using json with string like
        data:image/png;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7
        """
        client = self.data_engineer_1_client
        url = reverse('api:dataset-media-list')
        dataset = self.ds_1
        # first delete all dataset media
        DatasetMedia.objects.filter(dataset=dataset).delete()
        b64s = factories.get_chubby_bat_img_base64()
        payload = {
            'dataset': dataset.id,
            'file': 'data:image/png;base64,{}'.format(b64s.decode('ascii'))
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # test that the file type (extension) has been rightly inferred
        data = resp.json()
        self.assertIn('file', data)
        file = data['file']
        # should be an url
        self.assertTrue(file.startswith('http://'))
        # expect png extension
        self.assertTrue(file.endswith('.png'))
        # compare image
        dataset_media = DatasetMedia.objects.filter(id=data['id']).first()
        self.assertIsNotNone(dataset_media)
        self.assertEqual(
            open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb').read(),
            open(dataset_media.path, 'rb').read()
        )

        # test that even if we put the wrong file type it will infer the right one
        # send with data:image/gif
        payload = {
            'dataset': dataset.id,
            'file': 'data:image/gif;base64,{}'.format(b64s.decode('ascii'))
        }
        resp = client.post(url, data=payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # test that the file type (extension) has been rightly inferred
        data = resp.json()
        # expect png extension
        self.assertTrue(data['file'].endswith('.png'))


class TestFilters(helpers.BaseUserTestCase):
    def setUp(self):
        super(TestFilters, self).setUp()


    def test_filter_by_dataset(self):
        """
        Test that we can filter dataset media by 'dataset', 'dataset__id' or 'dataset__name'
        """
        # set up dataset and dataset media
        ds_1 = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 1')

        ds_2 = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 2')

        ds_3 = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 3')

        self.assertEqual(Dataset.objects.count(), 3)

        # 1 image for ds_1
        factories.DatasetMediaFactory.create(dataset=ds_1)
        self.assertEqual(DatasetMedia.objects.filter(dataset=ds_1).count(), 1)

        # 2 images for ds_2
        factories.DatasetMediaFactory.create_batch(2, dataset=ds_2)
        self.assertEqual(DatasetMedia.objects.filter(dataset=ds_2).count(), 2)

        # 2 images for ds_2
        factories.DatasetMediaFactory.create_batch(3, dataset=ds_3)
        self.assertEqual(DatasetMedia.objects.filter(dataset=ds_3).count(), 3)

        url = reverse('api:dataset-media-list')
        client = self.data_engineer_1_client

        # filter for ds_1 using the dataset filter
        filter_ = {
            'dataset': ds_1.pk
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), DatasetMedia.objects.filter(dataset=ds_1).count())

        # verify ids
        expected_ids = [dm.id for dm in DatasetMedia.objects.filter(dataset=ds_1)]
        received_ids = [dm['id'] for dm in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))

        # filter for ds_2 using the dataset__id filter
        filter_ = {
            'dataset__id': ds_2.pk
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), DatasetMedia.objects.filter(dataset=ds_2).count())

        # verify ids
        expected_ids = [m.id for m in DatasetMedia.objects.filter(dataset=ds_2)]
        received_ids = [m['id'] for m in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))

        # filter for ds_2 using the dataset__name filter
        filter_ = {
            'dataset__name': ds_3.name
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), DatasetMedia.objects.filter(dataset=ds_3).count())

        # verify ids
        expected_ids = [m.id for m in DatasetMedia.objects.filter(dataset=ds_3)]
        received_ids = [m['id'] for m in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))


    def test_filter_by_project(self):
        """
        Test that we can filter media by 'dataset__project', 'dataset__project__id' or
        'dataset__project__name'
        """
        # set up dataset and dataset media
        ds_1 = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 1')

        ds_2 = self._create_dataset_with_schema(self.project_1, self.data_engineer_1_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 2')

        ds_3 = self._create_dataset_with_schema(self.project_2, self.data_engineer_2_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 3')

        ds_4 = self._create_dataset_with_schema(self.project_2, self.data_engineer_2_client,
                                                     helpers.GENERIC_SCHEMA, dataset_name='Test DS 4')

        self.assertEqual(Dataset.objects.count(), 4)

        # 1 image for ds_1
        factories.DatasetMediaFactory.create(dataset=ds_1)
        self.assertEqual(DatasetMedia.objects.filter(dataset=ds_1).count(), 1)

        # 2 images for ds_2
        factories.DatasetMediaFactory.create_batch(2, dataset=ds_2)
        self.assertEqual(DatasetMedia.objects.filter(dataset=ds_2).count(), 2)

        project_1_datasetmedia_qs = DatasetMedia.objects.filter(dataset__project=self.project_1)

        self.assertEqual(project_1_datasetmedia_qs.count(),
                         DatasetMedia.objects.filter(dataset__in=[ds_1, ds_2]).count())

        # 3 image for ds_3
        factories.DatasetMediaFactory.create_batch(3, dataset=ds_3)
        self.assertEqual(DatasetMedia.objects.filter(dataset=ds_3).count(), 3)

        # 4 images for ds_4
        factories.DatasetMediaFactory.create_batch(4, dataset=ds_4)
        self.assertEqual(DatasetMedia.objects.filter(dataset=ds_4).count(), 4)

        project_2_datasetmedia_qs = DatasetMedia.objects.filter(dataset__project=self.project_2)

        self.assertEqual(project_2_datasetmedia_qs.count(),
                         DatasetMedia.objects.filter(dataset__in=[ds_3, ds_4]).count())

        url = reverse('api:dataset-media-list')
        client = self.data_engineer_1_client

        # filter for project_1 using the dataset__project filter
        filter_ = {
            'dataset__project': self.project_1.pk
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), project_1_datasetmedia_qs.count())

        # verify ids
        expected_ids = [dm.id for dm in project_1_datasetmedia_qs]
        received_ids = [dm['id'] for dm in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))

        # filter for project_1 using the dataset__project__id filter
        filter_ = {
            'dataset__project__id': self.project_1.pk
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), project_1_datasetmedia_qs.count())

        # verify ids
        expected_ids = [dm.id for dm in project_1_datasetmedia_qs]
        received_ids = [dm['id'] for dm in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))

        # filter for project_2 using the dataset__project__name filter
        filter_ = {
            'dataset__project__name': self.project_2.name
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), project_2_datasetmedia_qs.count())

        # verify ids
        expected_ids = [dm.id for dm in project_2_datasetmedia_qs]
        received_ids = [dm['id'] for dm in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))

        # filter for project_2 using the dataset__project__code filter
        filter_ = {
            'dataset__project__code': self.project_2.code
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), project_2_datasetmedia_qs.count())

        # verify ids
        expected_ids = [dm.id for dm in project_2_datasetmedia_qs]
        received_ids = [dm['id'] for dm in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))
