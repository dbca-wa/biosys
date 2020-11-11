import copy

from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from django.utils import timezone

from main.models import Dataset, Project, Record
from main.utils_data_package import *
from main.tests import factories


def clone(descriptor):
    return copy.deepcopy(descriptor)


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
    "constraints": clone(BASE_CONSTRAINTS)
}

GENERIC_SCHEMA = {
    "fields": [
        clone(BASE_FIELD)
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
            "schema": clone(GENERIC_SCHEMA)
        }
    ],
    "title": "Test"
}

LAT_LONG_OBSERVATION_SCHEMA = {
    "fields": [
        {
            "name": "Observation Date",
            "type": "date",
            "format": "any",
            "constraints": {
                "required": True,
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
        },
    ]
}

DATUM_FIELD = {
    "name": "Datum",
    "type": "string",
    "format": "default",
    "constraints": {
        "required": False
    },
    "biosys": {
        "type": "datum"
    }
}

LAT_LONG_OBSERVATION_DATA_PACKAGE = clone(GENERIC_DATA_PACKAGE)
LAT_LONG_OBSERVATION_DATA_PACKAGE['resources'][0]['schema'] = clone(LAT_LONG_OBSERVATION_SCHEMA)

LAT_LONG_WITH_DATUM_OBSERVATION_SCHEMA = clone(LAT_LONG_OBSERVATION_SCHEMA)
LAT_LONG_WITH_DATUM_OBSERVATION_SCHEMA['fields'].append(clone(DATUM_FIELD))

EASTING_NORTHING_OBSERVATION_SCHEMA = {
    "fields": [
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
            "biosys": {
                "type": "latitude"
            }
        },
        {
            "name": "Easting",
            "type": "number",
            "format": "default",
            "constraints": {
                "required": True,
            },
            "biosys": {
                "type": "longitude"
            }
        },
        {
            "name": "Datum",
            "type": "string",
            "format": "default",
            "constraints": {
                "required": False
            },
            "biosys": {
                "type": "datum"
            }
        }
    ]
}

SPECIES_NAME_FIELD = {
    "name": "Species Name",
    "type": "string",
    "format": "default",
    "constraints": {
        "required": True
    },
    "biosys": {
        "type": "speciesName"
    }
}

SPECIES_OBSERVATION_SCHEMA = clone(LAT_LONG_OBSERVATION_SCHEMA)
SPECIES_OBSERVATION_SCHEMA['fields'].append(clone(SPECIES_NAME_FIELD))

SPECIES_OBSERVATION_DATA_PACKAGE = clone(GENERIC_DATA_PACKAGE)
SPECIES_OBSERVATION_DATA_PACKAGE['resources'][0]['schema'] = clone(SPECIES_OBSERVATION_SCHEMA)


class TestSchemaConstraints(TestCase):
    def test_none_or_empty(self):
        """
        None or empty is accepted
        """
        self.assertEqual({}, SchemaConstraints(None).descriptor)
        self.assertEqual({}, SchemaConstraints({}).descriptor)

    def test_required_property(self):
        # no constraints -> require = False
        self.assertFalse(SchemaConstraints(None).required)
        cts = clone(BASE_CONSTRAINTS)
        self.assertFalse(cts['required'])
        self.assertFalse(SchemaConstraints(cts).required)

        cts = clone(BASE_CONSTRAINTS)
        cts['required'] = True
        self.assertTrue(cts['required'])
        self.assertTrue(SchemaConstraints(cts).required)

    def test_get_method(self):
        """
        test that the SchemaField has the dict-like get('key', default)
        """
        cts = clone(BASE_CONSTRAINTS)
        sch = SchemaConstraints(cts)
        self.assertTrue(hasattr(sch, 'get'))
        self.assertEqual(cts.get('required'), sch.get('required'))
        self.assertEqual(cts.get('constraints'), sch.get('constraints'))
        self.assertEqual(None, sch.get('bad_keys'))
        self.assertEqual('default', sch.get('bad_keys', 'default'))


class TestSchemaField(TestCase):
    def setUp(self):
        self.base_field = clone(BASE_FIELD)

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
        self.assertEqual(field.get('Name'), sch.get('Name'))
        self.assertEqual(field.get('constraints'), sch.get('constraints'))
        self.assertEqual(None, sch.get('bad_keys'))
        self.assertEqual('default', sch.get('bad_keys', 'default'))

    def test_column_name(self):
        """
        'column_name' is a property that is equal to name
        """
        field = self.base_field
        sch = SchemaField(field)
        self.assertEqual(sch.name, sch.column_name)
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
        self.assertEqual([], SchemaField(field).aliases)
        field['aliases'] = []
        self.assertEqual([], SchemaField(field).aliases)
        field['aliases'] = ['alias1', 'Alias2']
        sch = SchemaField(field)
        self.assertEqual(field['aliases'], sch.aliases)
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
        self.base_field_descriptor = clone(BASE_FIELD)

    def test_boolean_default_values(self):
        """
        Test possible values for a boolean
        Since TableSchema V1.0 the default true values are [ "true", "True", "TRUE", "1" ]
        We want to be sure that 'yes' and 'no' (and variations) are included by default.
        """
        true_values = ['True', 'true', 'True', 'YES', 'yes', 'y', 'Y', 'Yes']
        false_values = ['FALSE', 'false', 'False', 'NO', 'no', 'n', 'N', 'No']
        wrong_values = [2, 3, 'FLSE', 'flse', 'NON', 'oui', 'maybe', 'not sure', 't', '1', 1, '0', 0]
        descriptor = self.base_field_descriptor
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

    def test_boolean_custom_values(self):
        """
        The schema specifications allows to override the true and false values with 'trueValues' and 'falseValues'
        (see https://frictionlessdata.io/specs/table-schema/)
        We want only 'yes' and 'no'
        """
        true_values = ['YES', 'yes', 'Yes']
        false_values = ['NO', 'no', 'No']
        wrong_values = ['true', 'false', 'True', 'False', 'y', 'n', 'Y', 'N', 't', '1', 1, '0', 0]
        descriptor = self.base_field_descriptor
        descriptor['type'] = 'boolean'
        # only 'default' format
        descriptor['format'] = 'default'
        descriptor['trueValues'] = true_values
        descriptor['falseValues'] = false_values

        f = SchemaField(descriptor)
        for v in true_values:
            self.assertTrue(f.cast(v))
        for v in false_values:
            self.assertFalse(f.cast(v))
        for v in wrong_values:
            with self.assertRaises(Exception):
                f.cast(v)

    def test_date(self):
        descriptor = clone(BASE_FIELD)
        descriptor['type'] = 'date'
        # 'default' format = ISO
        descriptor['format'] = 'default'
        f = SchemaField(descriptor)
        valid_values = ['2016-07-29']
        for v in valid_values:
            date = f.cast(v)
            self.assertIsInstance(date, datetime.date)
            self.assertEqual(datetime.date(2016, 7, 29), date)
        invalid_value = ['29/07/2016', '07/29/2016', '2016-07-29 15:28:37']
        for v in invalid_value:
            with self.assertRaises(Exception):
                f.cast(v)

        # The main problem is to be sure that a dd/mm/yyyy is not interpreted as mm/dd/yyyy
        descriptor['format'] = 'any'
        f = SchemaField(descriptor)
        valid_values = [
            '2016-07-10',
            '10/07/2016',
            '10/07/16',
            '2016-07-10 15:28:37',
            '10-July-2016',
            '10-JUlY-16',
            '10-07-2016',
            '10-07-16'
        ]
        expected_date = datetime.date(2016, 7, 10)
        for v in valid_values:
            date = f.cast(v)
            self.assertIsInstance(date, datetime.date)
            self.assertEqual(expected_date, date)
        invalid_value = ['djskdj']
        for v in invalid_value:
            with self.assertRaises(Exception):
                f.cast(v)

    def test_date_custom_format(self):
        format_ = '%d %b %y'  # ex 30 Nov 14
        descriptor = {
            'name': 'Date with fmt',
            'type': 'date',
            'format': format_
        }
        field = SchemaField(descriptor)
        value = '30 Nov 14'
        self.assertEqual(field.cast(value), datetime.date(2014, 11, 30))

        format_ = '%Y_%m_%d'
        descriptor = {
            'name': 'Date with fmt',
            'type': 'date',
            'format': format_
        }
        field = SchemaField(descriptor)
        value = '2012_03_05'
        self.assertEqual(field.cast(value), datetime.date(2012, 3, 5))

    def test_string(self):
        # test that a blank string '' or '  ' is not accepted when the field is required
        null_values = ['', '   ']
        desc = clone(BASE_FIELD)
        desc['type'] = 'string'
        desc['constraints'] = clone(REQUIRED_CONSTRAINTS)
        f = SchemaField(desc)
        for v in null_values:
            with self.assertRaises(Exception):
                f.cast(v)

        # test non unicode (python 2)
        value = 'not unicode'
        self.assertIsInstance(f.cast(value), str)
        self.assertEqual(f.cast(value), value)


class TestGenericSchemaValidation(TestCase):
    def setUp(self):
        self.descriptor = clone(GENERIC_SCHEMA)
        self.sch = GenericSchema(self.descriptor)


class TestObservationSchemaCast(TestCase):
    def setUp(self):
        self.descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)

    def test_cast_observation_date_happy_path(self):
        descriptor = self.descriptor
        schema = ObservationSchema(descriptor)
        record = {
            'Latitude': "-32", 'Observation Date': '23/12/2016', 'Longitude': "115.3"
        }
        self.assertEqual(schema.cast_record_observation_date(record), datetime.date(2016, 12, 23))

    def test_cast_observation_date_sad_path(self):
        """
        A record without date should not throw an exception but return None when trying to casting the observation date.
        Only a wrong format should throw
        :return:
        """
        # a record without date value should throw an exception
        descriptor = self.descriptor
        schema = ObservationSchema(descriptor)
        record = {
            'Latitude': "-32", 'Longitude': "115.3"
        }
        self.assertIsNone(schema.cast_record_observation_date(record))

        record = {
            'Latitude': "-32", 'Observation Date': '', 'Longitude': "115.3"
        }
        self.assertIsNone(schema.cast_record_observation_date(record))

        record = {
            'Latitude': "-32", 'Observation Date': 'bullshit', 'Longitude': "115.3"
        }
        with self.assertRaises(InvalidDateType):
            schema.cast_record_observation_date(record)

        record = {
            'Latitude': "-32", 'Observation Date': 1200, 'Longitude': "115.3"
        }
        with self.assertRaises(InvalidDateType):
            schema.cast_record_observation_date(record)

    def test_cast_point_happy_path(self):
        """
        Test a simple lat/long record. No datum provided.
        The datum should be the default.
        :return:
        """
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        schema = ObservationSchema(descriptor)
        record = {
            'Latitude': "-32", 'Observation Date': '23/12/2016', 'Longitude': "115.3"
        }
        point = schema.cast_geometry(record)
        self.assertIsNotNone(point)
        self.assertTrue(isinstance(point, GEOSGeometry))
        self.assertTrue(isinstance(point, Point))
        self.assertEqual((115.3, -32), point.coords)
        self.assertEqual(MODEL_SRID, point.srid)

    def test_cast_point_with_datum(self):
        """
        Happy path: Lat/Long with datum provided.
        Test that the geometry has the correct datum
        :return:
        """
        datum = 'GDA94'
        descriptor = clone(LAT_LONG_WITH_DATUM_OBSERVATION_SCHEMA)
        schema = ObservationSchema(descriptor)
        self.assertIsNotNone(schema.datum_field)
        record = {
            'Observation Date': '23/12/2016', 'Latitude': "-32", 'Longitude': "115.3", 'Datum': datum
        }
        point = schema.cast_geometry(record)
        self.assertIsNotNone(point)
        self.assertTrue(isinstance(point, Point))
        self.assertEqual((115.3, -32), point.coords)
        expected_srid = get_datum_srid(record['Datum'])
        self.assertEqual(expected_srid, point.srid)

    def test_cast_point_with_invalid_datum(self):
        """
        Sad path: Lat/Long with unsupported datum.
        This should throw an exception instead of reverting to the default DATUM
        :return:
        """
        datum = 'GDA2064'
        self.assertFalse(is_supported_datum(datum))
        descriptor = clone(LAT_LONG_WITH_DATUM_OBSERVATION_SCHEMA)
        schema = ObservationSchema(descriptor)
        self.assertIsNotNone(schema.datum_field)
        record = {
            'Observation Date': '23/12/2016', 'Latitude': "-32", 'Longitude': "115.3", 'Datum': datum
        }
        with self.assertRaises(Exception):
            schema.cast_geometry(record)

    def test_cast_point_easting_northing_no_zone_field(self):
        """
        Use case:
         - Location entered with easting and northing instead of lat/long
         - The datum (with zone) is specified in a single column 'datum'
        The easting/northing problem can be solved by tagging easting=longitude and northing=longitude
        """
        datum = 'GDA94 / MGA zone 50'
        self.assertTrue(is_supported_datum(datum))
        descriptor = clone(EASTING_NORTHING_OBSERVATION_SCHEMA)
        schema = ObservationSchema(descriptor)
        self.assertIsNotNone(schema.datum_field)
        easting = 405542.537
        northing = 6459127.469
        record = {
            'Observation Date': '23/12/2016', 'Easting': easting, 'Northing': northing, 'Datum': datum
        }
        point = schema.cast_geometry(record)
        self.assertIsNotNone(point)
        self.assertTrue(isinstance(point, Point))
        self.assertEqual((easting, northing), point.coords)
        self.assertEqual(get_datum_srid(datum), point.srid)

        # create a db record with geometry = east/north and check geometry conversion
        # create dataset
        program = factories.ProgramFactory.create()
        project = factories.ProjectFactory.create(
            program=program,
            name="Test"
        )
        ds = Dataset.objects.create(
            project=project,
            name='test',
            data_package=GENERIC_DATA_PACKAGE
        )
        record = Record.objects.create(
            dataset=ds,
            datetime=timezone.now(),
            geometry=point,
            data=record)
        record.refresh_from_db()
        self.assertEqual(MODEL_SRID, record.geometry.srid)
        self.assertEqual((116, -31), (int(record.geometry.x), int(record.geometry.y)))

    def test_cast_point_easting_northing_with_zone_field(self):
        """
        Use case:
         - Location entered with easting and northing instead of lat/long
         - The datum is specified in a column and the zone in another
        """
        datum = 'GDA94'
        zone = 50
        expected_srid = 28350

        descriptor = clone(EASTING_NORTHING_OBSERVATION_SCHEMA)
        # add a Zone column
        descriptor['fields'].append({
            "name": "Zone",
            "type": "integer",
            "constraints": {
                "required": False
            },
        })
        schema = ObservationSchema(descriptor)
        self.assertIsNotNone(schema.datum_field)
        easting = 405542.537
        northing = 6459127.469
        record = {
            'Observation Date': '23/12/2016', 'Easting': easting, 'Northing': northing, 'Datum': datum, 'Zone': zone
        }
        srid = schema.cast_srid(record)
        self.assertEqual(srid, expected_srid)
        point = schema.cast_geometry(record)
        self.assertIsNotNone(point)
        self.assertTrue(isinstance(point, Point))
        self.assertEqual((easting, northing), point.coords)
        self.assertEqual(expected_srid, point.srid)

        # create a db record with geometry = east/north and check geometry conversion
        # create dataset
        program = factories.ProgramFactory.create()
        project = factories.ProjectFactory.create(
            program=program,
            name="Test"
        )
        ds = Dataset.objects.create(
            project=project,
            name='test',
            data_package=GENERIC_DATA_PACKAGE
        )
        record = Record.objects.create(
            dataset=ds,
            datetime=timezone.now(),
            geometry=point,
            data=record)
        record.refresh_from_db()
        self.assertEqual(MODEL_SRID, record.geometry.srid)
        self.assertEqual((116, -31), (int(record.geometry.x), int(record.geometry.y)))


class TestSpeciesObservationSchemaCast(TestCase):
    def test_happy_path(self):
        descriptor = clone(SPECIES_OBSERVATION_SCHEMA)
        species_name = 'Chubby Bat'
        record = {
            'Observation Date': "18/08/2016",
            'Latitude': -32,
            'Longitude': 115,
            'Species Name': 'Chubby Bat'
        }
        schema = SpeciesObservationSchema(descriptor)
        self.assertEqual(species_name, schema.cast_species_name(record))

    def test_space_stripping(self):
        """
        The cast should strip leading and trailing spaces
        """
        descriptor = clone(SPECIES_OBSERVATION_SCHEMA)
        species_name = 'Chubby Bat'
        record = {
            'Observation Date': "18/08/2016",
            'Latitude': -32,
            'Longitude': 115,
            'Species Name': '  Chubby Bat  '
        }
        schema = SpeciesObservationSchema(descriptor)
        self.assertEqual(species_name, schema.cast_species_name(record))

    def test_blank(self):
        """
        Blank string should raise an exception
        :return:
        """
        descriptor = clone(SPECIES_OBSERVATION_SCHEMA)
        record = {
            'Observation Date': "18/08/2016",
            'Latitude': -32,
            'Longitude': 115,
            'Species Name': '   '
        }
        schema = SpeciesObservationSchema(descriptor)
        with self.assertRaises(Exception):
            schema.cast_species_name(record)

    def test_none(self):
        """
        None should raise an exception
        :return:
        """
        descriptor = clone(SPECIES_OBSERVATION_SCHEMA)
        record = {
            'Observation Date': "18/08/2016",
            'Latitude': -32,
            'Longitude': 115,
            'Species Name': None
        }
        schema = SpeciesObservationSchema(descriptor)
        with self.assertRaises(Exception):
            schema.cast_species_name(record)

    def test_number(self):
        """
        Number should raise an exception
        :return:
        """
        descriptor = clone(SPECIES_OBSERVATION_SCHEMA)
        record = {
            'Observation Date': "18/08/2016",
            'Latitude': -32,
            'Longitude': 115,
            'Species Name': 1234
        }
        schema = SpeciesObservationSchema(descriptor)
        with self.assertRaises(Exception):
            schema.cast_species_name(record)
