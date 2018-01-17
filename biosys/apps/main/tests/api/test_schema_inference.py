from rest_framework.test import APIClient

from main.tests.api import helpers


class InferTestBase(helpers.BaseUserTestCase):
    def verify_data_package(descriptor):
        """
        Test that the descriptor (returned by the infer endpoint)
        can be saved as a dataset through API
        :param descriptor:
        """


class TestGenericSchema(helpers.BaseUserTestCase):
    def _more_setup(self):
        pass

    def test_basic_type_inference(self):
        """

        :return:
        """
