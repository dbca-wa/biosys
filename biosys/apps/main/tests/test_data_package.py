from jsontableschema.exceptions import *
from django.test import TestCase
from main.utils_data_package import *

GENERIC_SCHEMA = {
    "name": "test",
    "resources": [
        {
            "name": "test",
            "format": "CSV",
            "title": "test",
            "bytes": 0,
            "mediatype": "text/csv",
            "path": "test.csv",
            "schema": {
                "fields": [
                    {
                        "name": "Name",
                        "type": "string",
                        "format": "default"
                    },
                ]
            }
        }
    ],
    "title": "Test"
}


class TestBaseSchemaValidation(TestCase):
    def test_resources_mandatory(self):
        descriptor = GENERIC_SCHEMA
        del descriptor['resources']
        with self.assertRaises(InvalidSchemaError):
            schema = Schema(descriptor)


class TestTypeValidation(TestCase):
    pass


class TestGenericSchema(TestCase):
    pass


class TestObservationSchema(TestCase):
    pass


class TestSpeciesObservation(TestCase):
    pass


class TestBaseDataValidation(TestCase):
    pass


class TestObservationDataValidation(TestCase):
    pass


class TestSpeciesObservationdataValidation(TestCase):
    pass
