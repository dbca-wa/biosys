from __future__ import absolute_import, unicode_literals, print_function, division

MODEL_SRID = 4326
DATUM_CHOICES = [
    (MODEL_SRID, 'WGS84'),
    (4283, 'GDA94'),
    (4203, 'AGD84'),
    (4202, 'AGD66'),

    (28348, 'GDA94 / MGA zone 48'),
    (28349, 'GDA94 / MGA zone 49'),
    (28350, 'GDA94 / MGA zone 50'),
    (28351, 'GDA94 / MGA zone 51'),
    (28352, 'GDA94 / MGA zone 52'),
    (28353, 'GDA94 / MGA zone 53'),
    (28354, 'GDA94 / MGA zone 54'),
    (28355, 'GDA94 / MGA zone 55'),
    (28356, 'GDA94 / MGA zone 56'),
    (28357, 'GDA94 / MGA zone 57'),
    (28358, 'GDA94 / MGA zone 58'),

    (20348, 'AGD84 / MGA zone 48'),
    (20349, 'AGD84 / MGA zone 49'),
    (20350, 'AGD84 / MGA zone 50'),
    (20351, 'AGD84 / MGA zone 51'),
    (20352, 'AGD84 / MGA zone 52'),
    (20353, 'AGD84 / MGA zone 53'),
    (20354, 'AGD84 / MGA zone 54'),
    (20355, 'AGD84 / MGA zone 55'),
    (20356, 'AGD84 / MGA zone 56'),
    (20357, 'AGD84 / MGA zone 57'),
    (20358, 'AGD84 / MGA zone 58'),

    (20248, 'AGD66 / MGA zone 48'),
    (20249, 'AGD66 / MGA zone 49'),
    (20250, 'AGD66 / MGA zone 50'),
    (20251, 'AGD66 / MGA zone 51'),
    (20252, 'AGD66 / MGA zone 52'),
    (20253, 'AGD66 / MGA zone 53'),
    (20254, 'AGD66 / MGA zone 54'),
    (20255, 'AGD66 / MGA zone 55'),
    (20256, 'AGD66 / MGA zone 56'),
    (20257, 'AGD66 / MGA zone 57'),
    (20258, 'AGD66 / MGA zone 58'),

]
SUPPORTED_DATUMS = dict(DATUM_CHOICES).values()

"""
Given a datum and a zone number the srid can be calculated with the following offsets.
E.g: GDA94 Zone 50 = AUSTRALIAN_ZONE_SRID_OFFSET['GDA94'] + zone
"""
AUSTRALIAN_ZONE_SRID_OFFSET = {
    'GDA94': 28300,
    'AGD84': 20300,
    'AGD66': 20200
}


def is_supported_datum(datum):
    return get_datum_srid(datum) is not None


def is_projected_srid(srid):
    return srid > 20000


def get_datum_srid(datum):
    # case insensitive search
    for srid, datum_name in DATUM_CHOICES:
        if datum_name.lower() == datum.lower():
            return srid
    return None


def get_australian_zone_srid(datum, zone):
    """
    Given a datum and a zone number return the srid (espg) number.
    This function will raise an exception if anything is wrong
    :param datum: string
    :param zone: integer
    :return:
    """
    zone = int(zone)  # will raise an exception if zone not a number
    offset = AUSTRALIAN_ZONE_SRID_OFFSET.get(datum.strip(), -1)
    if offset == -1:
        raise Exception('Unsupported datum for Australian zone projection. Must be one of {}'
                        .format(AUSTRALIAN_ZONE_SRID_OFFSET.keys()))
    if zone < 48 or zone > 58:
        raise Exception('Unsupported zone. Must be an integer between 48 and 58')
    return offset + zone
