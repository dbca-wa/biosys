from django.test import TestCase

from main.tests.api import helpers
from main.utils_data_package import *


class LatLongValidation(TestCase):
    """
    Test validation rules only.
    """

    def test_happy_path(self):
        schema_fields = [
            {
                "name": "Latitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Longitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_lat_long)
        self.assertTrue(parser.is_lat_long_only)
        self.assertFalse(parser.is_easting_northing)
        self.assertFalse(parser.is_easting_northing_only)
        self.assertFalse(parser.is_site_code)
        self.assertFalse(parser.is_site_code_only)
        self.assertIsNotNone(parser.latitude_field)
        self.assertIsNotNone(parser.longitude_field)

    def test_without_required(self):
        """
        If the schema contains only lat/long they must have a required constraint
        """
        schema_fields = [
            {
                "name": "Latitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Longitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(parser.errors[0],
                         "The field named 'Latitude' must have the 'required' constraint set to true.")
        self.assertTrue(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)

        schema_fields = [
            {
                "name": "Latitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Longitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 1)
        self.assertEqual(parser.errors[0],
                         "The field named 'Longitude' must have the 'required' constraint set to true.")
        self.assertTrue(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)

    def test_biosys_tag_happy_path(self):
        """
        columns not named latitude or longitude but with biosys tags
        """
        schema_fields = [
            {
                "name": "Lat",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'latitude'
                },
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Long",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'longitude'
                },
                "constraints": {
                    "required": True,
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNotNone(parser.latitude_field)
        self.assertIsNotNone(parser.longitude_field)
        self.assertFalse(parser.is_site_code)
        self.assertFalse(parser.is_site_code_only)
        self.assertEqual(parser.latitude_field.name, 'Lat')
        self.assertEqual(parser.longitude_field.name, 'Long')

    def test_biosys_tag_without_required(self):
        """
        columns not named latitude or longitude but with biosys tags must be required.
        """
        schema_fields = [
            {
                "name": "Lat",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'latitude'
                },
            },
            {
                "name": "Long",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'longitude'
                },
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 2)
        expected_errors = [
            "The field named 'Lat' must have the 'required' constraint set to true.",
            "The field named 'Long' must have the 'required' constraint set to true."
        ]
        self.assertIn(parser.errors[0], expected_errors)
        self.assertIn(parser.errors[1], expected_errors)
        self.assertNotEqual(parser.errors[0], parser.errors[1])
        self.assertTrue(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNotNone(parser.latitude_field)
        self.assertIsNotNone(parser.longitude_field)
        self.assertEqual(parser.latitude_field.name, 'Lat')
        self.assertEqual(parser.longitude_field.name, 'Long')

    def test_biosys_tag_precedence(self):
        """
        Two fields one name 'Latitude' and another one tagged as biosys type latitude
        The biosys one is chosen
        """
        schema_fields = [
            {
                "name": "The Observation Latitude",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'latitude'
                },
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Longitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNotNone(parser.latitude_field)
        self.assertIsNotNone(parser.longitude_field)
        self.assertEqual(parser.latitude_field.name, 'The Observation Latitude')
        self.assertEqual(parser.longitude_field.name, 'Longitude')

    def test_two_biosys_type_is_error(self):
        """
        Can't have two fields of the same type
        :return:
        """
        schema_fields = [
            {
                "name": "Lat",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'latitude'
                },
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Another lat",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'latitude'
                },
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Long",
                "type": "number",
                "format": "default",
                "biosys": {
                    "type": 'longitude'
                },
                "constraints": {
                    "required": True,
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 1)
        expected_errors = [
            "More than one Biosys type latitude field found: ['Lat', 'Another lat']",
        ]
        self.assertIn(parser.errors[0], expected_errors)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNone(parser.latitude_field)
        self.assertIsNotNone(parser.longitude_field)

    def test_two_latitude_name_is_error(self):
        """
        Can't have two fields Latitude (no biosys tag)
        """
        schema_fields = [
            {
                "name": "Latitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -90.0,
                    "maximum": 90.0,
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "format": "default",
            },
            {
                "name": "Longitude",
                "type": "number",
                "format": "default",
                "constraints": {
                    "required": True,
                    "minimum": -180.0,
                    "maximum": 180.0,
                }
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 1)
        expected_errors = [
            "More than one field named Latitude found.",
        ]
        self.assertIn(parser.errors[0], expected_errors)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNone(parser.latitude_field)
        self.assertIsNotNone(parser.longitude_field)


class EastNorthingValidation(TestCase):
    def test_without_datum_zone(self):
        """
        A schema without datum/zone can be accepted as it will use the project's
        :return:
        """
        schema_fields = [
            {
                "name": "Easting",
                "type": "number",
                "format": "default",
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
                }
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_easting_northing)
        self.assertTrue(parser.is_easting_northing_only)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_lat_long_only)
        self.assertFalse(parser.is_site_code)
        self.assertFalse(parser.is_site_code_only)
        self.assertIsNotNone(parser.easting_field)
        self.assertIsNotNone(parser.northing_field)

    def test_with_datum_zone(self):
        """
        A schema with datum/zone
        :return:
        """
        schema_fields = [
            {
                "name": "Easting",
                "type": "number",
                "format": "default",
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
                }
            },
            {
                "name": "Datum",
                "type": "string"
            },
            {
                "name": "Zone",
                "type": "integer"
            }
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_easting_northing)
        self.assertFalse(parser.is_lat_long)
        self.assertIsNotNone(parser.easting_field)
        self.assertIsNotNone(parser.northing_field)
        self.assertIsNotNone(parser.datum_field)
        self.assertIsNotNone(parser.zone_field)


class SiteCodeOnly(TestCase):
    def test_with_column_name_only(self):
        schema_fields = [
            {
                "name": "Site Code",
                "type": "string",
                "format": "default",
                "constraints": {
                    "required": True,
                }
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_site_code_only)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNotNone(parser.site_code_field)
        self.assertEqual(parser.site_code_field.name, 'Site Code')

    def test_with_wrong_column_name(self):
        """
        The coloumn name must be Site Code not Site
        :return:
        """
        schema_fields = [
            {
                "name": "Site",
                "type": "string",
                "format": "default",
                "constraints": {
                    "required": True,
                }
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 1)
        expected_error = "The schema must contain some geometry fields: latitude/longitude or easting/northing " \
                         "or alternatively a reference to the Site Code."
        self.assertEqual(parser.errors[0], expected_error)

    def test_with_column_name_only_without_required(self):
        """
        If it is a site code only schema, the column must be required
        """
        schema_fields = [
            {
                "name": "Site Code",
                "type": "string",
                "format": "default",
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 1)
        expected_error = "The field named 'Site Code' must have the 'required' constraint set to true."
        self.assertEqual(parser.errors[0], expected_error)
        self.assertTrue(parser.is_site_code_only)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNotNone(parser.site_code_field)
        self.assertEqual(parser.site_code_field.name, 'Site Code')

    def test_with_biosys_type(self):
        schema_fields = [
            {
                "name": "Site",
                "type": "string",
                "format": "default",
                "biosys": {
                    "type": "siteCode"
                },
                "constraints": {
                    "required": True,
                }
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_site_code_only)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNotNone(parser.site_code_field)
        self.assertEqual(parser.site_code_field.name, 'Site')

    def test_biosys_type_without_required(self):
        """
        If it is a site code only schema, the column must be required
        """
        schema_fields = [
            {
                "name": "Site",
                "type": "string",
                "format": "default",
                "biosys": {
                    "type": "siteCode"
                },
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertFalse(parser.is_valid())
        self.assertEqual(len(parser.errors), 1)
        expected_error = "The field named 'Site' must have the 'required' constraint set to true."
        self.assertEqual(parser.errors[0], expected_error)
        self.assertTrue(parser.is_site_code_only)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_easting_northing)
        self.assertIsNotNone(parser.site_code_field)
        self.assertEqual(parser.site_code_field.name, 'Site')

    def test_with_foreign_key(self):
        """
        Alternatively to naming or tagging the column we can use a foreign key
        """
        schema_fields = [
            {
                "name": "Island",
                "type": "string",
                "format": "default",
                "constraints": {
                    "required": True,
                }
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        schema = helpers.add_foreign_key_to_schema(schema, {
            'schema_field': 'Island',
            'model': 'Site',
            'model_field': 'code'
        })
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertTrue(parser.is_site_code_only)
        self.assertFalse(parser.is_lat_long)
        self.assertFalse(parser.is_lat_long_only)
        self.assertFalse(parser.is_easting_northing)
        self.assertFalse(parser.is_easting_northing_only)
        self.assertIsNotNone(parser.site_code_field)
        self.assertEqual(parser.site_code_field.name, 'Island')


class LatLongAndSiteCode(TestCase):
    def test_lat_long_and_site_code_fk_not_required(self):
        """
        Schema with lat/long and a site code foreign key
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
                "constraints": helpers.REQUIRED_CONSTRAINTS,
                "format": "any",
                "biosys": {
                    'type': 'observationDate'
                }
            },
            {
                "name": "Latitude",
                "type": "number",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'latitude'
                }
            },
            {
                "name": "Longitude",
                "type": "number",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": 'longitude'
                }
            },
            {
                "name": "Site Code",
                "type": "string",
                "constraints": helpers.NOT_REQUIRED_CONSTRAINTS
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        schema = helpers.add_foreign_key_to_schema(schema, {
            'schema_field': 'Site Code',
            'model': 'Site',
            'model_field': 'code'
        })
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertFalse(parser.is_site_code_only)
        self.assertTrue(parser.is_lat_long)
        self.assertFalse(parser.is_lat_long_only)
        self.assertFalse(parser.is_easting_northing)
        self.assertFalse(parser.is_easting_northing_only)
        self.assertIsNotNone(parser.site_code_field)
        self.assertEqual(parser.site_code_field.name, 'Site Code')
