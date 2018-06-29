import json

from django.contrib.gis.geos import GEOSGeometry
from django.core.urlresolvers import reverse
from rest_framework import status

from main.models import Site
from main.tests import factories
from main.tests.api import helpers


class TestPermissions(helpers.BaseUserTestCase):
    """
    Test Permissions
    Get: authenticated
    Update: admin, custodians
    Create: admin, custodians
    Delete: admin, custodians
    """

    def setUp(self):
        super(TestPermissions, self).setUp()
        self.site_1 = factories.SiteFactory.create(project=self.project_1)
        self.site_2 = factories.SiteFactory.create(project=self.project_2)

    def test_get(self):
        urls = [
            reverse('api:site-list'),
            reverse('api:site-detail', kwargs={'pk': self.site_1.pk})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [
                self.readonly_client,
                self.custodian_1_client,
                self.custodian_2_client,
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
        Admin and custodians
        :return:
        """
        project = self.project_1
        urls = [reverse('api:site-list')]
        data = {
            "name": "A new project for Unit test",
            "code": "C12",
            "project": project.pk
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                # site code must be unique
                data['code'] += '1'
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )

    def test_bulk_create(self):
        """
        Cannot create bulk with this end point
        :return:
        """
        project = self.project_1
        urls = [reverse('api:site-list')]
        data = [
            {
                "name": "A new project for Unit test",
                "code": "C1111",
                "project": project.pk
            },
            {
                "name": "A new project for Unit test",
                "code": "C2222",
                "project": project.pk
            }
        ]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client, self.admin_client,
                          self.custodian_1_client],
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
                # site code must be unique
                for site in data:
                    site['code'] += '1'
                self.assertEqual(
                    client.post(url, data, format='json').status_code,
                    status.HTTP_201_CREATED
                )

    def test_update1(self):
        """
        admin + custodian of project for site 1
        :return:
        """
        site = self.site_1
        previous_code = site.code
        updated_code = previous_code + "-updated"
        urls = [reverse('api:site-detail', kwargs={'pk': site.pk})]
        data = {
            "code": updated_code,
        }
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                site.code = previous_code
                site.save()
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                site.refresh_from_db()
                self.assertEqual(site.code, updated_code)

    def test_update2(self):
        """
        admin + custodian of project for site 2
        :return:
        """
        site = self.site_2
        previous_code = site.code
        updated_code = previous_code + "-updated"
        urls = [reverse('api:site-detail', kwargs={'pk': site.pk})]
        data = {
            "code": updated_code,
        }
        access = {
            "forbidden": [
                self.anonymous_client,
                self.readonly_client,
                self.custodian_1_client,
                self.data_engineer_1_client,

            ],
            "allowed": [
                self.admin_client,
                self.data_engineer_2_client,
                self.custodian_2_client
            ]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.patch(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )
        count = 0
        for client in access['allowed']:
            count += 1
            for url in urls:
                site.code = previous_code
                site.save()
                self.assertEqual(
                    client.patch(url, data, format='json').status_code,
                    status.HTTP_200_OK
                )
                site.refresh_from_db()
                self.assertEqual(site.code, updated_code)

    def test_delete(self):
        """
        Currently admin + custodian
        :return:
        """
        site = self.site_1
        urls = [reverse('api:site-detail', kwargs={'pk': site.pk})]
        data = None
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, self.custodian_1_client]
        }

        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.delete(url, data, format='json').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        for client in access['allowed']:
            for url in urls:
                site.save()
                site_count = Site.objects.count()
                self.assertEqual(
                    client.delete(url, data, format='json').status_code,
                    status.HTTP_204_NO_CONTENT
                )
                self.assertTrue(Site.objects.count(), site_count - 1)

    def test_options(self):
        urls = [
            reverse('api:site-list'),
            reverse('api:site-detail', kwargs={'pk': 1})
        ]
        access = {
            "forbidden": [self.anonymous_client],
            "allowed": [self.readonly_client, self.custodian_1_client, self.custodian_2_client, self.admin_client]
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


class TestSiteUpload(helpers.BaseUserTestCase):

    def test_permissions(self):
        """
        Only custodian or admin
        :return:
        """
        project = self.project_1
        custodian_client = self.custodian_1_client

        urls = [reverse('api:upload-sites', kwargs={'pk': project.pk})]
        access = {
            "forbidden": [self.anonymous_client, self.readonly_client, self.custodian_2_client],
            "allowed": [self.admin_client, custodian_client]
        }
        data = {
            'file': 'dsddsds'
        }
        for client in access['forbidden']:
            for url in urls:
                self.assertIn(
                    client.post(url, data=data, format='multipart').status_code,
                    [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
                )

        csv_file = helpers.rows_to_csv_file([
            ['Site Code'],
            ['C1']
        ])
        for client in access['allowed']:
            for url in urls:
                with open(csv_file) as fp:
                    self.assertIn(
                        client.post(url, data={'file': fp}, format='multipart').status_code,
                        [status.HTTP_200_OK]
                    )

    def test_upload_csv_happy_path(self):
        csv_data = [
            ['Site Code', 'Site Name', 'Description', 'Latitude', 'Longitude', 'Datum', 'Attribute1', 'Attribute2'],
            ['C1', 'Site 1', 'Description1', -32, 116, '', 'attr11', 'attr12'],
            ['C2', 'Site 2', 'Description2', -31, 117, '', 'attr21', 'attr22']
        ]
        csv_file = helpers.rows_to_csv_file(csv_data)
        project = self.project_1
        client = self.custodian_1_client
        url = reverse('api:upload-sites', kwargs={'pk': project.pk})
        self.assertEqual(0, Site.objects.filter(project=project).count())
        with open(csv_file) as fp:
            data = {
                'file': fp
            }
            resp = client.post(url, data=data, format='multipart')
            self.assertEqual(status.HTTP_200_OK, resp.status_code)
            qs = Site.objects.filter(project=project)
            self.assertEqual(len(csv_data) - 1, qs.count())
            self.assertEqual(['C1', 'C2'], [s.code for s in qs.order_by('code')])
            self.assertEqual(['Site 1', 'Site 2'], [s.name for s in qs.order_by('name')])
            self.assertEqual(['Description1', 'Description2'], [s.description for s in qs.order_by('description')])

            # test geom and attr
            s = qs.filter(code='C1').first()
            self.assertEqual((116, -32), (s.geometry.x, s.geometry.y))
            expected_attributes = {
                'Latitude': '-32',
                'Longitude': '116',
                'Datum': '',
                'Attribute1': 'attr11',
                'Attribute2': 'attr12'}

            self.assertEqual(expected_attributes, s.attributes)

            self.assertEqual(project.site_count, len(csv_data) - 1)

    def test_upload_xlsx_happy_path(self):
        csv_data = [
            ['Site Code', 'Site Name', 'Description', 'Latitude', 'Longitude', 'Datum', 'Attribute1', 'Attribute2'],
            ['C1', 'Site 1', 'Description1', -32, 116, '', 'attr11', 'attr12'],
            ['C2', 'Site 2', 'Description2', -31, 117, '', 'attr21', 'attr22']
        ]
        xlsx_file = helpers.rows_to_xlsx_file(csv_data)
        project = self.project_1
        client = self.custodian_1_client
        url = reverse('api:upload-sites', kwargs={'pk': project.pk})
        self.assertEqual(0, Site.objects.filter(project=project).count())
        with open(xlsx_file, 'rb') as fp:
            data = {
                'file': fp
            }
            resp = client.post(url, data=data, format='multipart')
            self.assertEqual(status.HTTP_200_OK, resp.status_code)
            qs = Site.objects.filter(project=project)
            self.assertEqual(len(csv_data) - 1, qs.count())
            self.assertEqual(['C1', 'C2'], [s.code for s in qs.order_by('code')])
            self.assertEqual(['Site 1', 'Site 2'], [s.name for s in qs.order_by('name')])
            self.assertEqual(['Description1', 'Description2'], [s.description for s in qs.order_by('description')])

            # test geom and attr
            s = qs.filter(code='C1').first()
            self.assertEqual((116, -32), (s.geometry.x, s.geometry.y))
            expected_attributes = {
                'Latitude': '-32',
                'Longitude': '116',
                'Datum': '',
                'Attribute1': 'attr11',
                'Attribute2': 'attr12'}

            self.assertEqual(expected_attributes, s.attributes)

            self.assertEqual(project.site_count, len(csv_data) - 1)

    def test_easting_northing_geometry_extraction(self):
        csv_data = [
            ['Code', 'Name', 'Description', 'Easting', 'Northing', 'Datum', 'Zone', 'Attribute1', 'Attribute2'],
            ['C1', 'Site 1', 'Description1', '405542.537', '6459127.469', 'GDA94', '50', 'attr11', 'attr12'],
        ]
        xlsx_file = helpers.rows_to_xlsx_file(csv_data)
        project = self.project_1
        client = self.custodian_1_client
        url = reverse('api:upload-sites', kwargs={'pk': project.pk})
        self.assertEqual(0, Site.objects.filter(project=project).count())
        with open(xlsx_file, 'rb') as fp:
            data = {
                'file': fp
            }
            resp = client.post(url, data=data, format='multipart')
            self.assertEqual(status.HTTP_200_OK, resp.status_code)
            qs = Site.objects.filter(project=project)
            self.assertEqual(qs.count(), 1)
            site = qs.first()
            self.assertEqual(site.code, 'C1')
            self.assertEqual(site.name, 'Site 1')
            self.assertEqual(site.description, 'Description1')

            # test geom and attr
            self.assertAlmostEqual(site.geometry.x, 116, places=4)
            self.assertAlmostEqual(site.geometry.y, -32, places=4)
            expected_attributes = {
                'Easting': '405542.537',
                'Northing': '6459127.469',
                'Datum': 'GDA94',
                'Zone': '50',
                'Attribute1': 'attr11',
                'Attribute2': 'attr12'}

            self.assertEqual(expected_attributes, site.attributes)

    def test_site_code_column_name(self):
        """
        Test that a column named 'site_code' can be used to extract the site code
        """
        csv_data = [
            ['site_code', 'Site Name', 'Description', 'Latitude', 'Longitude', 'Datum', 'Attribute1', 'Attribute2'],
            ['C1', 'Site 1', 'Description1', -32, 116, '', 'attr11', 'attr12'],
            ['C2', 'Site 2', 'Description2', -31, 117, '', 'attr21', 'attr22']
        ]
        csv_file = helpers.rows_to_csv_file(csv_data)
        project = self.project_1
        client = self.custodian_1_client
        url = reverse('api:upload-sites', kwargs={'pk': project.pk})
        self.assertEqual(0, Site.objects.filter(project=project).count())
        with open(csv_file) as fp:
            data = {
                'file': fp
            }
            resp = client.post(url, data=data, format='multipart')
            self.assertEqual(status.HTTP_200_OK, resp.status_code)
            qs = Site.objects.filter(project=project)
            self.assertEqual(len(csv_data) - 1, qs.count())
            self.assertEqual(['C1', 'C2'], [s.code for s in qs.order_by('code')])


class TestSerialization(helpers.BaseUserTestCase):

    def test_centroid(self):
        project = self.project_1
        client = self.custodian_1_client
        site = factories.SiteFactory.create(
            project=project,
            geometry="SRID=4326;"
                     "LINESTRING (124.18701171875 -17.6484375, 126.38427734375 -18.615234375, 123.35205078125 "
                     "-20.65869140625, 124.1650390625 -17.71435546875)",)
        self.assertIsNotNone(site)
        url = reverse('api:site-detail', kwargs={'pk': site.pk})
        resp = client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertTrue('centroid' in data)
        centroid = GEOSGeometry(json.dumps(data['centroid']))
        self.assertEqual(centroid.geojson, site.geometry.centroid.geojson)

