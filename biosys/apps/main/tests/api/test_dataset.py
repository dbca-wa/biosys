from django.test import TestCase
from rest_framework.test import APIClient


class TestACL(TestCase):
    """
    Test Permissions
    """
    pass


class TestDataDescriptorValidation(TestCase):
    """
    Testing that that the validation of data descriptor is called when creating data set.
    Note: the goal is not to test all the validation case here (see other unit tests) but
    to check that the validation is called when using the api
    """
