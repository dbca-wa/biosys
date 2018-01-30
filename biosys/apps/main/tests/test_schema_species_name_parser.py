from django.test import TestCase

from main.utils_data_package import SpeciesNameParser
from main.tests.api.helpers import LAT_LONG_OBSERVATION_SCHEMA, clone


class TestSpeciesNameOnly(TestCase):

    def test_species_name_only(self):
        """
        Happy path: One field named Species Name and required
        """
        field_desc = {
            "name": "Species Name",
            "type": "string",
            "constraints": {
                'required': True
            }
        }
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append(field_desc)
        parser = SpeciesNameParser(descriptor)
        self.assertTrue(parser.valid)
        self.assertTrue(parser.has_species_name)
        self.assertTrue(parser.is_species_name_only)
        self.assertEquals(parser.species_name_field.name, 'Species Name')
        expected_species_name = 'Canis Lupus'
        data = {
            'Species Name': ' Canis Lupus  '
        }
        casted_value = parser.cast_species_name(data)
        self.assertEquals(expected_species_name, casted_value)

    def test_species_name_only_with_biosys_type(self):
        """
        Happy path: columns not name Species Name but tagged as biosys type = longitude
        """
        field_desc = {
            "name": "Species",
            "type": "string",
            "constraints": {
                'required': True
            }
        }
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append(field_desc)
        parser = SpeciesNameParser(descriptor)
        self.assertFalse(parser.valid)

        # add biosys type
        field_desc['biosys'] = {
            'type': 'speciesName'
        }
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append(field_desc)
        parser = SpeciesNameParser(descriptor)
        self.assertTrue(parser.valid)
        self.assertTrue(parser.has_species_name)
        self.assertTrue(parser.is_species_name_only)
        field = parser.species_name_field
        field.name = field_desc['name']
        expected_species_name = 'Canis Lupus'
        data = {
            'Species': ' Canis Lupus  '
        }
        casted_value = parser.cast_species_name(data)
        self.assertEquals(expected_species_name, casted_value)

    def test_must_be_required1(self):
        """
        The Species Name field must be set as required
        """
        field_desc = {
            "name": "Species Name",
            "type": "string",
        }
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append(field_desc)
        parser = SpeciesNameParser(descriptor)
        self.assertFalse(parser.valid)
        self.assertEquals(len(parser.errors), 1)
        error = parser.errors[0]
        self.assertIn('Species Name', error)
        self.assertIn('required', error)

        # set the  constraint explicitly
        field_desc['constraints'] = {
            'required': False
        }
        parser = SpeciesNameParser(descriptor)
        self.assertFalse(parser.valid)

    def test_must_be_required2(self):
        """
        The biosys speciesName field must be set as required
        """
        field_desc = {
            "name": "Species",
            "type": "string",
            "biosys": {
                "type": "speciesName"
            }
        }
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append(field_desc)
        parser = SpeciesNameParser(descriptor)
        self.assertFalse(parser.valid)
        self.assertEquals(len(parser.errors), 1)
        error = parser.errors[0]
        self.assertIn('Species', error)
        self.assertIn('required', error)

        # set the  constraint explicitly
        field_desc['constraints'] = {
            'required': False
        }
        parser = SpeciesNameParser(descriptor)
        self.assertFalse(parser.valid)

    def test_biosys_type_has_precedence(self):
        """
        Two fields one name 'Species Name' and another one tagged as biosys type speciesName
        The biosys one is chosen
        :return:
        """
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append({
            "name": "The Real Species Name",
            "type": "string",
            "constraints": {
                'required': True
            },
            "biosys": {
                "type": "speciesName"
            }
        })
        descriptor['fields'].append({
            "name": "Species Name",
            "type": "string",
            "constraints": {
                'required': True
            },
        })
        parser = SpeciesNameParser(descriptor)
        self.assertTrue(parser.valid)
        # if we provide two values the cast species should return the value of the biosys field
        expected_species_name = 'Canis Lupus'
        data = {
            'The Real Species Name': ' Canis Lupus ',
            'Species Name': 'Chubby Bat'
        }
        casted_value = parser.cast_species_name(data)
        self.assertEquals(expected_species_name, casted_value)

    def test_two_biosys_type_is_error(self):
        """
        Two fields tagged as biosys type speciesName should be invalid
        """
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append({
            "name": "The Real Species Name",
            "type": "string",
            "constraints": {
                'required': True
            },
            "biosys": {
                "type": "speciesName"
            }
        })
        descriptor['fields'].append({
            "name": "Species Name",
            "type": "string",
            "constraints": {
                'required': True
            },
            "biosys": {
                "type": "speciesName"
            }
        })
        parser = SpeciesNameParser(descriptor)
        self.assertFalse(parser.valid)

    def test_two_species_name_column_throws(self):
        """
        Two fields named Species Name (no biosys) is invalid
        """
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'].append({
            "name": "Species Name",
            "type": "string",
            "constraints": {
                'required': True
            },
        })
        descriptor['fields'].append({
            "name": "Species Name",
            "type": "string",
            "constraints": {
                'required': True
            },
        })
        parser = SpeciesNameParser(descriptor)
        self.assertFalse(parser.valid)


class TestGenusAndSpecies(TestCase):

    def test_genus_and_species_only(self):
        fields = [
            {
                "name": "Genus",
                "type": "string",
                "constraints": {
                    'required': True
                }
            },
            {
                "name": "Species",
                "type": "string",
                "constraints": {
                    'required': True
                }
            }
        ]
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'] += fields
        parser = SpeciesNameParser(descriptor)
        self.assertTrue(parser.valid)
        self.assertTrue(parser.has_genus_and_species)
        self.assertTrue(parser.is_genus_and_species_only)
        self.assertIsNotNone(parser.genus_field)
        self.assertEquals(parser.genus_field.name, 'Genus')
        self.assertIsNotNone(parser.species_field)
        self.assertEquals(parser.species_field.name, 'Species')
        expected_species_name = 'Canis Lupus'
        data = {
            'Genus': ' Canis ',
            'Species': ' Lupus '
        }
        casted_value = parser.cast_species_name(data)
        self.assertEquals(expected_species_name, casted_value)

    def test_genus_species_and_infra_specific(self):
        fields = [
            {
                "name": "Genus",
                "type": "string",
                "constraints": {
                    'required': True
                }
            },
            {
                "name": "Species",
                "type": "string",
                "constraints": {
                    'required': True
                }
            },
            {
                "name": "InfraSpecific rank",
                "type": "string",
            },
            {
                "name": "InfraSpecific Name",
                "type": "string",
            }
        ]
        descriptor = clone(LAT_LONG_OBSERVATION_SCHEMA)
        descriptor['fields'] += fields
        parser = SpeciesNameParser(descriptor)
        self.assertTrue(parser.valid)
        self.assertTrue(parser.has_genus_and_species)
        self.assertTrue(parser.is_genus_and_species_only)
        self.assertIsNotNone(parser.genus_field)
        self.assertEquals(parser.genus_field.name, 'Genus')
        self.assertIsNotNone(parser.species_field)
        self.assertEquals(parser.species_field.name, 'Species')
        self.assertIsNotNone(parser.infra_rank_field)
        self.assertEquals(parser.infra_rank_field.name, 'InfraSpecific rank')
        self.assertIsNotNone(parser.infra_name_field)
        self.assertEquals(parser.infra_name_field.name, 'InfraSpecific Name')
        expected_species_name = 'Canis Lupus infra name sub. rank'
        data = {
            'Genus': ' Canis ',
            'Species': ' Lupus ',
            'InfraSpecific rank': 'sub. rank ',
            'InfraSpecific Name': 'infra name ',
        }
        casted_value = parser.cast_species_name(data)
        self.assertEquals(expected_species_name, casted_value)
