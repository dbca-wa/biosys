from django.test import TestCase

from main.api.serializers import DatasetSerializer
from main.tests.api import helpers


class TestDatsetSerializer(helpers.BaseUserTestCase):

    def test_name_uniqueness(self):
        """
        Test that the serializer report an error if the dataset name is not unique within a project
        """
        # create a dataset
        dataset = self._create_dataset_from_rows([
            ['What', 'Comment'],
            ['what', 'comments']
        ])
        dataset.name = 'Test'
        dataset.save()

        # Try serializer with a dataset with the same name
        data = {
            'name': dataset.name,
            'project': dataset.project.pk,
            'data_package': dataset.data_package,
            'type': 'generic'
        }
        ser = DatasetSerializer(data=data)
        self.assertFalse(ser.is_valid(()))
        # the errors should be of the form
        # {'non_field_errors': ['The fields project, name must make a unique set.']}
        errors = ser.errors
        self.assertEquals(['non_field_errors'], list(errors.keys()))
        self.assertEquals(1, len(errors.get('non_field_errors')))
        self.assertIn('A dataset with this name already exists in the project.', errors.get('non_field_errors')[0])
