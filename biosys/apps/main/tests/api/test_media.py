from django.core.urlresolvers import reverse
from rest_framework import status

from main.models import Media, Record
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
        # create dataset with record
        self.ds_1 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Comments'],
            ['Canis lupus', '2018-06-11', 'A big dog']
        ])
        self.record_1 = self.ds_1.record_set.last()
        self.assertIsNotNone(self.record_1)
        # set media
        self.media_1 = factories.MediaFactory(record=self.record_1)
        self.assertEqual(self.media_1.record.id, self.record_1.id)

    def test_get(self):
        urls = [
            reverse('api:media-list'),
            reverse('api:media-detail', kwargs={'pk': self.media_1.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
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
            reverse('api:media-list'),
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }
        for client in access['forbidden']:
            for url in urls:
                with open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
                    payload = {
                        'record': self.record_1.pk,
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
                        'record': self.record_1.pk,
                        'file': fp
                    }
                    self.assertEqual(
                        client.post(url, data=payload, format='multipart').status_code,
                        status.HTTP_201_CREATED
                    )

    def test_put_patch(self):
        urls = [
            reverse('api:media-detail', kwargs={'pk': self.media_1.pk}),
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
                        'record': self.record_1.pk,
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
                        'record': self.record_1.pk,
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
        urls = [reverse('api:media-detail', kwargs={'pk': self.media_1.pk})]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
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
        # create dataset with record
        self.ds_1 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Comments'],
            ['Canis lupus', '2018-06-11', 'A big dog']
        ])
        self.record_1 = self.ds_1.record_set.last()
        self.assertIsNotNone(self.record_1)
        # set media
        self.media_1 = factories.MediaFactory(record=self.record_1)
        self.assertEqual(self.media_1.record.id, self.record_1.id)

    def test_returned_fields_format(self):
        """
        Should return a json response with the file as a url
        :return:
        """
        url = reverse('api:media-detail', kwargs={'pk': self.media_1.pk})
        client = self.custodian_1_client
        resp = client.get(url)
        self.assertEqual(resp['content-type'], 'application/json')
        data = resp.json()
        # should include the following keys
        expected_keys = ['id', 'record', 'file', 'created']
        received_keys = data.keys()
        for key in expected_keys:
            self.assertIn(key, received_keys)
        # record is returned as a pk
        self.assertEqual(data.get('record'), self.record_1.pk)
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
        Test that we can upload a new media using multipart form.
        """
        client = self.custodian_1_client
        url = reverse('api:media-list')
        format_ = 'multipart'
        record = self.record_1
        # record should have one media already
        self.assertEqual(Media.objects.filter(record=record).count(), 1)
        with open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb') as fp:
            payload = {
                'record': self.record_1.pk,
                'file': fp
            }
            resp = client.post(url, data=payload, format=format_)
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
            record.refresh_from_db()
            self.assertEqual(Media.objects.filter(record=record).count(), 2)
            # retrieve list
            resp = client.get(url, format='json')
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            data = resp.json()
            self.assertEqual(len(data), 2)

    def test_json_base64_upload_no_type(self):
        """
        Test that we can upload a media using json with pure base64 string as data (no data mime provided)
        also test that the serializer infer the file type
        """
        client = self.custodian_1_client
        url = reverse('api:media-list')
        record = self.record_1
        # first delete all media
        Media.objects.filter(record=record).delete()
        b64s = factories.get_chubby_bat_img_base64()
        payload = {
            'record': record.id,
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
        media = Media.objects.filter(id=data['id']).first()
        self.assertIsNotNone(media)
        self.assertEqual(
            open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb').read(),
            open(media.path, 'rb').read()
        )

    def test_json_base64_upload_html_format(self):
        """
        Test that we can upload a media using json with string like
        data:image/png;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7
        """
        client = self.custodian_1_client
        url = reverse('api:media-list')
        record = self.record_1
        # first delete all media
        Media.objects.filter(record=record).delete()
        b64s = factories.get_chubby_bat_img_base64()
        payload = {
            'record': record.id,
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
        media = Media.objects.filter(id=data['id']).first()
        self.assertIsNotNone(media)
        self.assertEqual(
            open(factories.CHUBBY_BAT_IMAGE_PATH, 'rb').read(),
            open(media.path, 'rb').read()
        )

        # test that even if we put the wrong file type it will infer the right one
        # send with data:image/gif
        payload = {
            'record': record.id,
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
        # create dataset with 3 records
        self.ds_1 = self._create_dataset_and_records_from_rows([
            ['What', 'When', 'Comments'],
            ['Canis lupus', '2018-06-11', 'A big dog'],
            ['Chubby bat', '2018-06-11', 'A fat bat'],
            ['Koala', '2018-06-11', 'drop bear']
        ])
        self.records = Record.objects.all()
        self.assertEqual(self.records.count(), 3)

    def test_filter_by_record(self):
        """
        Test that we can filter media by record id with the 'record' or 'record__id
        """
        record_1, record_2, record_3 = self.records
        # 2 images for record_1
        factories.MediaFactory.create_batch(2, record=record_1)
        media_1 = Media.objects.filter(record=record_1)
        self.assertEqual(media_1.count(), 2)
        # 1 image for record_2
        factories.MediaFactory.create(record=record_2)
        media_2 = Media.objects.filter(record=record_2)
        self.assertEqual(media_2.count(), 1)
        # no image for record_3
        media_3 = Media.objects.filter(record=record_3)
        self.assertEqual(media_3.count(), 0)

        url = reverse('api:media-list')
        client = self.custodian_1_client

        # filter for record_1
        filter_ = {
            'record': record_1.pk
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), len(media_1))
        # verify ids
        expected_ids = [m.id for m in media_1]
        received_ids = [m['id'] for m in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))

        # filter for record_2 using the record__id filter
        filter_ = {
            'record__id': record_2.pk
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), len(media_2))
        # verify ids
        expected_ids = [m.id for m in media_2]
        received_ids = [m['id'] for m in data]
        self.assertEqual(sorted(received_ids), sorted(expected_ids))

        # filter for record_3 using the record filter
        filter_ = {
            'record': record_3.pk
        }
        resp = client.get(url, data=filter_)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data), 0)
