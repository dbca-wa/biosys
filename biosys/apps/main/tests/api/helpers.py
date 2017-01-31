from django.conf import settings

from main.utils_species import SpeciesFacade

SOME_SPECIES_NAME_NAME_ID_MAP = {
    "Canis lupus subsp. familiaris": 30883,
    "Canis lupus": 25454,
    "Vespadelus douglasorum": 24204
}

REST_FRAMEWORK_TEST_SETTINGS = settings.REST_FRAMEWORK
if 'rest_framework.authentication.SessionAuthentication' \
        not in REST_FRAMEWORK_TEST_SETTINGS['DEFAULT_AUTHENTICATION_CLASSES']:
    REST_FRAMEWORK_TEST_SETTINGS['DEFAULT_AUTHENTICATION_CLASSES'] \
        .append('rest_framework.authentication.SessionAuthentication')


class LightSpeciesFacade(SpeciesFacade):
    def name_id_by_species_name(self):
        """
        :return: a dict where key is species_name and the value is name_id
        """
        return SOME_SPECIES_NAME_NAME_ID_MAP

    def get_all_species(self, properties=None):
        """
        :param properties: a sequence of Property, e.g [PROPERTY_SPECIES_NAME, PROPERTY_NAME_ID] or None for all
        attributes
        :return: Return a list of species properties (see structure above) but with only the specified attributes.
        NOTE: limiting the number of properties speed-up the request.
        """
        return []


def set_site(record_data, dataset, site):
    """
    Update the 'Site' column value with the given site code
    :param record_data:
    :param dataset:
    :param site:
    :return:
    """
    schema = dataset.schema
    site_column = schema.get_fk_for_model('Site').data_field
    record_data[site_column] = site.code
    return record_data
