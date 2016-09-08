"""
Facade methods to WFS HERBIE
Note: Herbie Species is a WFS 'feature' with the following structure (as of 18/08/2016).
All species information are in the properties field.
{
    'geometry': None,
    'id': 'herbie_hbvspecies_public.fid--57d0ec5d_156a0d39c8d_-2266',
    'type': 'Feature'
    'properties': {
        'added_on': '1997-11-02Z',
        'all_vernaculars': None,
        'author': '(C.E.Hubb.) Lazarides',
        'comments': None,
        'consv_code': None,
        'editor': None,
        'family_code': '031',
        'family_nid': 22751,
        'genus': 'Triodia',
        'informal': None,
        'infra_name': None,
        'infra_name2': None,
        'infra_rank': None,
        'infra_rank2': None,
        'is_current': 'Y',
        'is_eradicated': None,
        'kingdom_id': 3,
        'linear_sequence': None,
        'md5_rowhash': '0bb686e50b38be0ffc2d5b4f0f4870ff',
        'name_id': 17879,
        'naturalised': None,
        'naturalised_certainty': None,
        'naturalised_comments': None,
        'naturalised_status': 'N',
        'ogc_fid': 100,
        'rank_id': 220,
        'rank_name': 'Species',
        'reference': 'Austral.Syst.Bot. 10:434 (1997)',
        'species': 'helmsii',
        'species_code': 'TRIHEL',
        'species_name': 'Triodia helmsii',
        'updated_on': '2004-12-09Z',
        'vernacular': None
        },
}

"""
from __future__ import absolute_import, unicode_literals, print_function, division

import logging
import requests

from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = settings.HERBIE_SPECIES_WFS_URL


class HerbieError(Exception):
    pass


class Property:
    def __init__(self, herbie_name):
        self.herbie_name = herbie_name


PROPERTY_SPECIES_NAME = Property('species_name')
PROPERTY_NAME_ID = Property('name_id')


def name_id_by_species_name():
    """
    :return: a dict where key is species_name and the value is name_id
    """
    species = get_all_species([PROPERTY_SPECIES_NAME, PROPERTY_NAME_ID])
    return dict(
        [(sp[PROPERTY_SPECIES_NAME.herbie_name], sp[PROPERTY_NAME_ID.herbie_name]) for sp in species]
    )


def get_all_species(properties=None):
    """
    :param properties: a sequence of Property, e.g [PROPERTY_SPECIES_NAME, PROPERTY_NAME_ID] or None for all
    attributes
    :return: Return a list of species properties (see structure above) but with only the specified attributes.
    NOTE: limiting the number of properties speed-up the request.
    """
    return _query_species(_add_attributes_filter_to_params(properties))


def _add_attributes_filter_to_params(properties, params=None):
    """
    :param properties: al sequence of Property
    :param params: an initial parameter dictionary
    :return:
    """
    if properties:
        if params is None:
            params = {}
            # WFS spec: {'propertyName': (p1,p2,..)}
        params['propertyName'] = "({list})".format(
            list=','.join([a.herbie_name for a in properties])
        )
    return params


def _query_species(params=None):
    r = requests.get(BASE_URL, params=params)
    r.raise_for_status()
    try:
        return [f['properties'] for f in r.json()['features']]
    except Exception as e:
        # If we have an exception here it's probably because the request is not correct (XML error from geoserver)
        message = 'Herbie returned an error: {}. \nURL: {}. \nResponse: {}'.format(e, r.url, r.content)
        logger.warning(message)
        raise HerbieError(message)
