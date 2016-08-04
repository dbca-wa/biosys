from jsontableschema.exceptions import *
import datetime
import dateutil
import copy

from django.test import TestCase
from main.utils_data_package import *

BASE_CONSTRAINTS = {
    "required": False
}

NOT_REQUIRED_CONSTRAINTS = {
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
    "constraints": copy.deepcopy(BASE_CONSTRAINTS)
}

GENERIC_SCHEMA = {
    "fields": [
        copy.deepcopy(BASE_FIELD)
    ]
}

GENERIC_DATA_PACKAGE = {
    "name": "test",
    "resources": [
        {
            "name": "test",
            "format": "CSV",
            "title": "test",
            "bytes": 0,
            "mediatype": "text/csv",
            "path": "test.csv",
            "schema": copy.deepcopy(GENERIC_SCHEMA)
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
        cts = copy.deepcopy(BASE_CONSTRAINTS)
        self.assertFalse(cts['required'])
        self.assertFalse(SchemaConstraints(cts).required)

        cts = copy.deepcopy(BASE_CONSTRAINTS)
        cts['required'] = True
        self.assertTrue(cts['required'])
        self.assertTrue(SchemaConstraints(cts).required)

    def test_get_method(self):
        """
        test that the SchemaField has the dict-like get('key', default)
        """
        cts = copy.deepcopy(BASE_CONSTRAINTS)
        sch = SchemaConstraints(cts)
        self.assertTrue(hasattr(sch, 'get'))
        self.assertEquals(cts.get('required'), sch.get('required'))
        self.assertEquals(cts.get('constraints'), sch.get('constraints'))
        self.assertEquals(None, sch.get('bad_keys'))
        self.assertEquals('default', sch.get('bad_keys', 'default'))


class TestSchemaField(TestCase):
    def setUp(self):
        self.base_field = copy.deepcopy(BASE_FIELD)

    def test_name_mandatory(self):
        """
        A schema field without name should throw an exception
        """
        field = self.base_field
        del field['name']
        with self.assertRaises(FieldSchemaError):
            SchemaField(field)
        # no blank
        field = self.base_field
        field['name'] = ''
        with self.assertRaises(FieldSchemaError):
            SchemaField(field)

    def test_get_method(self):
        """
        test that the SchemaField has the dict-like get('key', default)
        """
        field = self.base_field
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
        field = self.base_field
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
        field = self.base_field
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
    def setUp(self):
        self.base_field = copy.deepcopy(BASE_FIELD)

    def test_boolean(self):
        true_values = [True, 'True', 'true', 'YES', 'yes', 'y', 't', '1', 1]
        false_values = [False, 'FALSE', 'false', 'NO', 'no', 'n', 'f', '0', 0]
        wrong_values = [2, 3, 'FLSE', 'flse', 'NON', 'oui', 'maybe', 'not sure']
        descriptor = self.base_field
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
        descriptor = copy.deepcopy(BASE_FIELD)
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
        null_values = ['null', 'none', 'nil', 'nan', '-', '']
        desc = copy.deepcopy(BASE_FIELD)
        desc['type'] = 'string'
        desc['constraints'] = copy.deepcopy(REQUIRED_CONSTRAINTS)
        f = SchemaField(desc)
        for v in null_values:
            with self.assertRaises(Exception):
                f.cast(v)

        # test non unicode (python 2)
        value = 'not unicode'
        self.assertIsInstance(f.cast(value), unicode)  # will fail on python 3 (type = str)
        self.assertEqual(f.cast(value), value)


class TestBaseSchema(TestCase):
    def setUp(self):
        self.descriptor = copy.deepcopy(GENERIC_SCHEMA)
        self.sch = Schema(self.descriptor)


class TestObservationSchema(TestCase):
    def setUp(self):
        self.descriptor = copy.deepcopy(GENERIC_SCHEMA)
        self.schema = Schema(self.descriptor)

    def test_no_date_field(self):
        # schema without date throw an exception
        descriptor = self.descriptor
        with self.assertRaises(ObservationDateSchemaError):
            ObservationSchema.get_observation_date_field_or_throw(descriptor)

    def test_one_date_field_with_required(self):
        # happy path: one date field only and
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Date Field",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS
            }
        )
        try:
            field = ObservationSchema.get_observation_date_field_or_throw(descriptor)
            self.assertEqual(field.name, "Date Field")
        except Exception as e:
            self.fail("Should not raise an exception!: {}: '{}'".format(e.__class__, e))

    def test_one_date_field_without_required(self):
        # the required is always needed
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Expected Date Field",
                "type": "date",
                "format": "any",
                "constraints": NOT_REQUIRED_CONSTRAINTS
            }
        )
        with self.assertRaises(ObservationDateSchemaError):
            ObservationSchema.get_observation_date_field_or_throw(descriptor)

    def test_two_date_fields_throws(self):
        # two date fields without more information throw an error
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Date Field #1",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS
            }
        )
        descriptor['fields'].append(
            {
                "name": "Date Field #2",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS
            }
        )

    def test_two_date_fields_one_with_biosys_type(self):
        # Happy path: two required date fields one with a biosys type
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Date Field #1",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS
            }
        )
        descriptor['fields'].append(
            {
                "name": "Biosys Observation Date",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": "observationDate"
                }
            }
        )
        try:
            field = ObservationSchema.get_observation_date_field_or_throw(descriptor)
            self.assertEqual(field.name, "Biosys Observation Date")
        except Exception as e:
            self.fail("Should not raise an exception!: {}: '{}'".format(e.__class__, e))

    def test_two_date_fields_one_with_biosys_type_not_required(self):
        # Sad path: two date fields one required and one with a biosys type not required
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Date Field #1",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS
            }
        )
        descriptor['fields'].append(
            {
                "name": "Biosys Observation Date",
                "type": "date",
                "format": "any",
                "constraints": NOT_REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": "observationDate"
                }
            }
        )
        with self.assertRaises(ObservationDateSchemaError):
            ObservationSchema.get_observation_date_field_or_throw(descriptor)

    def test_two_biosys_observation_date(self):
        # Sad path: two date fields tagged as a biosys observation date
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Date Field #1",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": "observationDate"
                }
            }
        )
        descriptor['fields'].append(
            {
                "name": "Date field2",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": "observationDate"
                }
            }
        )
        with self.assertRaises(ObservationDateSchemaError):
            ObservationSchema.get_observation_date_field_or_throw(descriptor)

    def test_two_date_one_with_correct_name(self):
        # happy path: two required date but one correctly named 'Observation Date'
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": ObservationSchema.OBSERVATION_DATE_FIELD_NAME,
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
            }
        )
        descriptor['fields'].append(
            {
                "name": "Date field2",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
            }
        )
        try:
            field = ObservationSchema.get_observation_date_field_or_throw(descriptor)
            self.assertEqual(field.name, ObservationSchema.OBSERVATION_DATE_FIELD_NAME)
        except Exception as e:
            self.fail("Should not raise an exception!: {}: '{}'".format(e.__class__, e))

    def test_two_date_with_correct_name(self):
        # sad path: two required date both correctly named 'Observation Date'
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": ObservationSchema.OBSERVATION_DATE_FIELD_NAME,
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
            }
        )
        descriptor['fields'].append(
            {
                "name": ObservationSchema.OBSERVATION_DATE_FIELD_NAME,
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
            }
        )
        with self.assertRaises(ObservationDateSchemaError):
            ObservationSchema.get_observation_date_field_or_throw(descriptor)

    def test_two_date_one_biosys_one_correct_name(self):
        # happy path?: two required date one named 'Observation Date' the other tag as biosys. Biosys has precedence
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": ObservationSchema.OBSERVATION_DATE_FIELD_NAME,
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
            }
        )
        descriptor['fields'].append(
            {
                "name": "The expected date",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS,
                "biosys": {
                    "type": "observationDate"
                }
            }
        )
        try:
            field = ObservationSchema.get_observation_date_field_or_throw(descriptor)
            self.assertNotEqual(field.name, ObservationSchema.OBSERVATION_DATE_FIELD_NAME)
            self.assertEqual(field.name, "The expected date")
        except Exception as e:
            self.fail("Should not raise an exception!: {}: '{}'".format(e.__class__, e))


class TestSpeciesObservation(TestCase):
    pass


class TestBaseDataValidation(TestCase):
    pass


class TestObservationDataValidation(TestCase):
    pass


class TestSpeciesObservationdataValidation(TestCase):
    pass
