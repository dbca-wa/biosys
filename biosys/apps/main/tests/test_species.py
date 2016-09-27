from django.test import TestCase

from main.utils_species import HerbieFacade


class TestHerbieFacade(TestCase):
    def setUp(self):
        self.facade = HerbieFacade()

    def test_all_species(self):
        try:
            species = self.facade.get_all_species()
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
            species = self.facade.get_all_species([self.facade.PROPERTY_SPECIES_NAME, self.facade.PROPERTY_NAME_ID])
            # at least 10000 species
            self.assertTrue(len(species) > 1000)
            # check the properties
            sp = species[0]
            props = sp.keys()
            self.assertTrue(len(props) == 2)
            # some important ones
            self.assertTrue(self.facade.PROPERTY_SPECIES_NAME.herbie_name in sp)
            self.assertTrue(self.facade.PROPERTY_NAME_ID.herbie_name in sp)
        except Exception as e:
            self.fail("Should not raise an exception!: {}: '{}'".format(e.__class__, e))
