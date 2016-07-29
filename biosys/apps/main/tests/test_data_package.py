from jsontableschema.exceptions import *
import datetime
import dateutil

from django.test import TestCase
from main.utils_data_package import *

BASE_CONSTRAINTS = {
    "required": False
}

REQUIRED_CONSTRAINTS = {
    "required": True
}

BASE_FIELD = {
    "name": "Name",
    "tile": "Title",
    "type": "string",
    "format": "default",
    "constraints": BASE_CONSTRAINTS.copy()
}

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
                    BASE_FIELD.copy()
                ]
            }
        }
    ],
    "title": "Test"
}


class TestSchemaConstraints(TestCase):
    def test_none_or_empty(self):
        """
        None or empty is accepted
        """
        self.assertEquals({}, SchemaConstraints(None).data)
        self.assertEquals({}, SchemaConstraints({}).data)

    def test_required_property(self):
        # no constraints -> require = False
        self.assertFalse(SchemaConstraints(None).required)
        cts = BASE_CONSTRAINTS.copy()
        self.assertFalse(cts['required'])
        self.assertFalse(SchemaConstraints(cts).required)

        cts = BASE_CONSTRAINTS.copy()
        cts['required'] = True
        self.assertTrue(cts['required'])
        self.assertTrue(SchemaConstraints(cts).required)

    def test_get_method(self):
        """
        test that the SchemaField has the dict-like get('key', default)
        """
        cts = BASE_CONSTRAINTS.copy()
        sch = SchemaConstraints(cts)
        self.assertTrue(hasattr(sch, 'get'))
        self.assertEquals(cts.get('required'), sch.get('required'))
        self.assertEquals(cts.get('constraints'), sch.get('constraints'))
        self.assertEquals(None, sch.get('bad_keys'))
        self.assertEquals('default', sch.get('bad_keys', 'default'))


class TestSchemaField(TestCase):
    def test_name_mandatory(self):
        """
        A schema field without name should throw an exception
        """
        field = BASE_FIELD.copy()
        del field['name']
        with self.assertRaises(FieldSchemaError):
            SchemaField(field)
        # no blank
        field = BASE_FIELD.copy()
        field['name'] = ''
        with self.assertRaises(FieldSchemaError):
            SchemaField(field)

    def test_get_method(self):
        """
        test that the SchemaField has the dict-like get('key', default)
        """
        field = BASE_FIELD.copy()
        sch = SchemaField(field)
        self.assertTrue(hasattr(sch, 'get'))
        self.assertEquals(field.get('Name'), sch.get('Name'))
        self.assertEquals(field.get('constraints'), sch.get('constraints'))
        self.assertEquals(None, sch.get('bad_keys'))
        self.assertEquals('default', sch.get('bad_keys', 'default'))

    def test_column_name(self):
        """
        'column_name' is a property that is equal to name
        """
        field = BASE_FIELD.copy()
        sch = SchemaField(field)
        self.assertEquals(sch.name, sch.column_name)
        self.assertNotEqual(sch.column_name, sch.title)

    def test_constraints(self):
        """
        test that the constraints property returned a SchemaConstraints
        """
        self.assertIsInstance(SchemaField(BASE_FIELD).constraints, SchemaConstraints)

    def test_aliases(self):
        """
        aliases is a biosys specific property.
        """
        field = BASE_FIELD.copy()
        self.assertFalse(field.get('aliases'))
        self.assertEquals([], SchemaField(field).aliases)
        field['aliases'] = []
        self.assertEquals([], SchemaField(field).aliases)
        field['aliases'] = ['alias1', 'Alias2']
        sch = SchemaField(field)
        self.assertEquals(field['aliases'], sch.aliases)
        # test some related method
        self.assertTrue(sch.has_alias('alias1'))
        self.assertTrue(sch.has_alias('Alias2'))
        self.assertFalse(sch.has_alias('alias2'))
        self.assertTrue(sch.has_alias('alias2', icase=True))
        self.assertFalse(sch.has_alias(field['name']))
        self.assertTrue(sch.has_name_or_alias(field['name'], 'aaaa'))
        self.assertFalse(sch.has_name_or_alias(field['name'].lower(), 'aaaa'))
        self.assertTrue(sch.has_name_or_alias(field['name'].lower(), 'aaaa', icase=True))
        self.assertFalse(sch.has_name_or_alias('aaaa', 'alias2'))
        self.assertTrue(sch.has_name_or_alias('aaaa', 'alias2', icase=True))


class TestSchemaFieldCast(TestCase):
    def test_boolean(self):
        true_values = [True, 'True', 'true', 'YES', 'yes', 'y', 't', '1', 1]
        false_values = [False, 'FALSE', 'false', 'NO', 'no', 'n', 'f', '0', 0]
        wrong_values = [2, 3, 'FLSE', 'flse', 'NON', 'oui', 'maybe', 'not sure']
        descriptor = BASE_FIELD.copy()
        descriptor['type'] = 'boolean'
        # only 'default' format
        descriptor['format'] = 'default'
        f = SchemaField(descriptor)
        for v in true_values:
            self.assertTrue(f.cast(v))
        for v in false_values:
            self.assertFalse(f.cast(v))
        for v in wrong_values:
            with self.assertRaises(Exception):
                f.cast(v)

    def test_date(self):
        descriptor = BASE_FIELD.copy()
        descriptor['type'] = 'date'
        # 'default' format = ISO
        descriptor['format'] = 'default'
        f = SchemaField(descriptor)
        valid_values = ['2016-07-29']
        for v in valid_values:
            date = f.cast(v)
            self.assertIsInstance(date, datetime.date)
            self.assertEqual(datetime.date(2016, 07, 29), date)
        invalid_value = ['29/07/2016', '07/29/2016', '2016-07-29 15:28:37']
        for v in invalid_value:
            with self.assertRaises(Exception):
                f.cast(v)

        # format='any'. Auto-detect but will use the bloody mm/dd/yyyy american format by default
        descriptor['format'] = 'any'
        f = SchemaField(descriptor)
        valid_values = [
            '2016-07-29',
            '07/29/2016',
            '07/29/16',
            '2016-07-29 15:28:37',
            '29/07/2016',
            '29-July-2016',
            '29-JUlY-16',
            '29-07-2016',
            '29-07-16'
        ]
        expected_date = datetime.date(2016, 07, 29)
        for v in valid_values:
            date = f.cast(v)
            self.assertIsInstance(date, datetime.date)
            self.assertEqual(expected_date, date)
        invalid_value = ['djskdj']
        for v in invalid_value:
            with self.assertRaises(Exception):
                f.cast(v)
        # test that it works in dd/mm/yyyy not mm/dd/yyy
        date = '01/12/2016'
        expected = datetime.date(2016, 12, 1)
        self.assertEqual(f.cast(date), expected)

    def test_string(self):
        # test that a blank string '' is not accepted when the field is required
        null_values = ['', None]
        desc = BASE_FIELD.copy()
        desc['type'] = 'string'
        desc['constraints'] = REQUIRED_CONSTRAINTS.copy()
        f = SchemaField(desc)
        for v in null_values:
            with self.assertRaises(Exception):
                f.cast(v)

        # test non unicode (python 2)
        value = 'not unicode'
        self.assertIsInstance(f.cast(value), unicode) # will fail on python 3 (type = str)
        self.assertEqual(f.cast(value), value)


class TestBaseSchemaValidation(TestCase):
    def test_resources_mandatory(self):
        descriptor = GENERIC_SCHEMA
        del descriptor['resources']
        with self.assertRaises(InvalidSchemaError):
            Schema(descriptor)


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
