from django.test import TestCase

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


class TestSchema(TestCase):
    pass
