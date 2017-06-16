from django.test import TestCase

from main.tests.api import helpers
from main.utils_data_package import *


class TestGeometryParser(TestCase):
    def test_lat_long_only_happy_path(self):
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
            },
        ]
        schema = helpers.create_schema_from_fields(schema_fields)
        parser = GeometryParser(schema)
        self.assertTrue(parser.is_valid())
        self.assertEqual(len(parser.errors), 0)
        self.assertEqual(parser.type, GeometryParser.TYPE_LAT_LONG)
