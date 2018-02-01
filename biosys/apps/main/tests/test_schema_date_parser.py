import datetime

from django.test import TestCase

from main.utils_data_package import ObservationSchema, ObservationDateParser, InvalidDateType

from main.tests.test_data_package import clone, GENERIC_SCHEMA, REQUIRED_CONSTRAINTS, NOT_REQUIRED_CONSTRAINTS


class TestObservationDateParser(TestCase):
    def setUp(self):
        self.descriptor = clone(GENERIC_SCHEMA)

    def test_no_date_field(self):
        """
        A schema without date should not be an error, just no date field
        """
        descriptor = self.descriptor
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNone(parser.observation_date_field)
        # casting anything should return none
        for dt in ['20/12/2017', None, 'kdjhj', '']:
            self.assertIsNone(parser.cast_date({
                'Date': dt,
                'Another Column': dt
            }))

    def test_one_date_field_with_required(self):
        """
        One single field of type date should be pick-up as the observation date
        """
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Date Field",
                "type": "date",
                "format": "any",
                "constraints": REQUIRED_CONSTRAINTS
            }
        )
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNotNone(parser.observation_date_field)
        self.assertEqual(parser.observation_date_field.name, 'Date Field')
        # try casting dates
        expected_date = datetime.date(2017, 6, 1)
        for dt in ['01/06/2017', '2017-06-01']:
            self.assertEqual(parser.cast_date({
                'Date Field': dt,
            }), expected_date)
        for dt in ['', None]:
            self.assertIsNone(parser.cast_date({
                'Date Field': dt,
            }))
        for dt in ['blah blah']:
            with self.assertRaises(InvalidDateType):
                parser.cast_date({
                    'Date Field': dt
                })

    def test_one_date_field_without_required(self):
        """
        The require constraint is not mandatory
        """
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": "Expected Date Field",
                "type": "date",
                "format": "any",
                "constraints": NOT_REQUIRED_CONSTRAINTS
            }
        )
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNotNone(parser.observation_date_field)
        self.assertEqual(parser.observation_date_field.name, 'Expected Date Field')
        # try casting dates
        expected_date = datetime.date(2017, 6, 1)
        for dt in ['01/06/2017', '2017-06-01']:
            self.assertEqual(parser.cast_date({
                'Expected Date Field': dt,
                'Another Date Field': '12/12/2017'
            }), expected_date)
        for dt in ['', None]:
            self.assertIsNone(parser.cast_date({
                'Expected Date Field': dt,
            }))
        for dt in ['blah blah']:
            with self.assertRaises(InvalidDateType):
                parser.cast_date({
                    'Expected Date Field': dt
                })

    def test_two_date_fields(self):
        """
        Two date field without more information is like no observation date
        :return:
        """
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
        descriptor = self.descriptor
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNone(parser.observation_date_field)
        # casting anything should return none
        for dt in ['20/12/2017', None, 'kdjhj', '']:
            self.assertIsNone(parser.cast_date({
                'Date': dt,
                'Another Column': dt
            }))

    def test_two_date_fields_one_with_biosys_type(self):
        """
        Test that if we provide two date field but one is tagged as an observationDate,
        it is the tagged one that is picked-up
        """
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
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNotNone(parser.observation_date_field)
        self.assertEqual(parser.observation_date_field.name, 'Biosys Observation Date')
        # try casting dates
        expected_date = datetime.date(2017, 6, 1)
        for dt in ['01/06/2017', '2017-06-01']:
            self.assertEqual(parser.cast_date({
                'Biosys Observation Date': dt,
                'Date Field #1': '12/12/2017'
            }), expected_date)
        for dt in ['', None]:
            self.assertIsNone(parser.cast_date({
                'Biosys Observation Date': dt,
                'Date Field #1': '12/12/2017',
            }))
        for dt in ['blah blah']:
            with self.assertRaises(InvalidDateType):
                parser.cast_date({
                    'Biosys Observation Date': dt
                })

    def test_two_date_fields_one_with_biosys_type_not_required(self):
        """
        Same as above
        The required constraint is not mandatory even for a tagged field
        """
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
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNotNone(parser.observation_date_field)
        self.assertEqual(parser.observation_date_field.name, 'Biosys Observation Date')
        # try casting dates
        expected_date = datetime.date(2017, 6, 1)
        for dt in ['01/06/2017', '2017-06-01']:
            self.assertEqual(parser.cast_date({
                'Biosys Observation Date': dt,
                'Date Field #1': '12/12/2017'
            }), expected_date)
        for dt in ['', None]:
            self.assertIsNone(parser.cast_date({
                'Biosys Observation Date': dt,
                'Date Field #1': '12/12/2017',
            }))
        for dt in ['blah blah']:
            with self.assertRaises(InvalidDateType):
                parser.cast_date({
                    'Biosys Observation Date': dt
                })

    def test_two_biosys_observation_date(self):
        """
        Two fields tagged as observationDate should result in an error and no date field
        """
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
        parser = ObservationDateParser(descriptor)
        self.assertFalse(parser.is_valid())
        self.assertTrue(len(parser.errors) == 1)
        expected_message = "More than one Biosys type observationDate field found: ['Date Field #1', 'Date field2']"
        self.assertEqual(parser.errors[0], expected_message)
        self.assertIsNone(parser.observation_date_field)
        # the cast should return none even if we pass date
        for dt in ['01/06/2017', '2017-06-01', '', None, 'Blah Blah']:
            self.assertIsNone(parser.cast_date({
                'Date Field #1': dt,
                'Date Field #2': '12/12/2017'
            }))

    def test_two_date_one_with_correct_name(self):
        # happy path: two dates but one correctly named 'Observation Date'
        descriptor = self.descriptor
        descriptor['fields'].append(
            {
                "name": ObservationSchema.OBSERVATION_DATE_FIELD_NAME,
                "type": "date",
                "format": "any",
            }
        )
        descriptor['fields'].append(
            {
                "name": "Date field2",
                "type": "date",
                "format": "any",
            }
        )
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNotNone(parser.observation_date_field)
        self.assertEqual(parser.observation_date_field.name, ObservationSchema.OBSERVATION_DATE_FIELD_NAME)
        # try casting dates
        expected_date = datetime.date(2017, 6, 1)
        for dt in ['01/06/2017', '2017-06-01']:
            self.assertEqual(parser.cast_date({
                ObservationSchema.OBSERVATION_DATE_FIELD_NAME: dt,
                'Date Field #1': '12/12/2017'
            }), expected_date)
        for dt in ['', None]:
            self.assertIsNone(parser.cast_date({
                ObservationSchema.OBSERVATION_DATE_FIELD_NAME: dt,
                'Date Field #1': '12/12/2017',
            }))
        for dt in ['blah blah']:
            with self.assertRaises(InvalidDateType):
                parser.cast_date({
                    ObservationSchema.OBSERVATION_DATE_FIELD_NAME: dt
                })

    def test_two_date_with_correct_name(self):
        """
        Sad path: two column named ObservationSchema.OBSERVATION_DATE_FIELD_NAME.
        Should result with a parser error and the date casting returning None
        """
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
        parser = ObservationDateParser(descriptor)
        self.assertFalse(parser.is_valid())
        self.assertTrue(len(parser.errors) == 1)
        expected_message = "More than one field named Observation Date found."
        self.assertEqual(parser.errors[0], expected_message)
        self.assertIsNone(parser.observation_date_field)
        # the cast should return none even if we pass date
        for dt in ['01/06/2017', '2017-06-01', '', None, 'Blah Blah']:
            self.assertIsNone(parser.cast_date({
                ObservationSchema.OBSERVATION_DATE_FIELD_NAME: dt,
            }))

    def test_two_date_one_biosys_one_correct_name(self):
        """
        Two date fields one named 'Observation Date' the other tagged as biosys observationDate.
        Test that the Biosys field has precedence
        :return:
        """
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
        parser = ObservationDateParser(descriptor)
        self.assertTrue(parser.is_valid())
        self.assertTrue(len(parser.errors) == 0)
        self.assertIsNotNone(parser.observation_date_field)
        self.assertEqual(parser.observation_date_field.name, "The expected date")
        # try casting dates
        expected_date = datetime.date(2017, 6, 1)
        for dt in ['01/06/2017', '2017-06-01']:
            self.assertEqual(parser.cast_date({
                "The expected date": dt,
                ObservationSchema.OBSERVATION_DATE_FIELD_NAME: '12/12/2017'
            }), expected_date)
        for dt in ['', None]:
            self.assertIsNone(parser.cast_date({
                "The expected date": dt,
                ObservationSchema.OBSERVATION_DATE_FIELD_NAME: '12/12/2017',
            }))
        for dt in ['blah blah']:
            with self.assertRaises(InvalidDateType):
                parser.cast_date({
                    "The expected date": dt
                })
