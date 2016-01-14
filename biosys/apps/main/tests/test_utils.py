import tempfile
import os

from openpyxl import load_workbook
from django.test import TestCase

from main.utils import create_lookups_book, is_species_observation_field
from main.models import SpeciesObservation
from vegetation.models import StratumSpecies


class TestModelUtils(TestCase):
    def setUp(self):
        pass

    def test_create_lookups_book_creation(self):
        tf = tempfile.mkstemp(suffix='.xlsx')[1]
        try:
            create_lookups_book(tf)
            self.assertTrue(os.stat(tf).st_size > 0, msg="The Site Visit datasheet should not be empty")
        except Exception as e:
            self.assertTrue(False, msg="Creating a Site Visit datasheet should not throw an exception: " + str(e))

        # test that we can open it with openpyxl
        try:
            load_workbook(tf)
        except Exception as e:
            self.assertTrue(False, msg="Site Visit datasheet is not a valid format: " + str(e))

    def test_is_species_field(self):
        # filter species field from the StratumSpecies model. There should only be one
        species_name_fields = [f for f in StratumSpecies._meta.fields if is_species_observation_field(f)]
        self.assertEqual(1, len(species_name_fields),
                         msg="There should be only one species field in StratumSpecies model")
        field = species_name_fields[0]
        self.assertTrue(field.related_model == SpeciesObservation)


class TestLookup(TestCase):
    fixtures = ['lookups.json']

    def setUp(self):
        pass

