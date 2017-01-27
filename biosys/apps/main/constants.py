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
]
SUPPORTED_DATUMS = dict(DATUM_CHOICES).values()


def is_supported_datum(datum):
    return get_datum_srid(datum) is not None


def get_datum_srid(datum):
    # case insensitive search
    for srid, datum_name in DATUM_CHOICES:
        if datum_name.lower() == datum.lower():
            return srid
    return None
