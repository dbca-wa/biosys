from django.test import TestCase

from main.utils_species import *


class TestHerbieFacade(TestCase):
    def test_all_species(self):
        try:
            species = get_all_species()
            # at least 10000 species
            self.assertTrue(len(species) > 1000)
            # check the properties
            sp = species[0]
            props = sp.keys()
            # at least 10 of them
            self.assertTrue(len(props) > 10)
            # some important ones
            self.assertTrue('species_name' in sp)
            self.assertTrue('name_id' in sp)
        except Exception as e:
            self.fail("Should not raise an exception!: {}: '{}'".format(e.__class__, e))

    def test_property_filter(self):
        try:
            species = get_all_species([PROPERTY_SPECIES_NAME, PROPERTY_NAME_ID])
            # at least 10000 species
            self.assertTrue(len(species) > 1000)
            # check the properties
            sp = species[0]
            props = sp.keys()
            self.assertTrue(len(props) == 2)
            # some important ones
            self.assertTrue(PROPERTY_SPECIES_NAME.herbie_name in sp)
            self.assertTrue(PROPERTY_NAME_ID.herbie_name in sp)
        except Exception as e:
            self.fail("Should not raise an exception!: {}: '{}'".format(e.__class__, e))
