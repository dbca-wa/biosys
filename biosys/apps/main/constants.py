from __future__ import absolute_import, unicode_literals, print_function, division

MODEL_SRID = 4326
DATUM_CHOICES = [
    (MODEL_SRID, 'WGS84'),
    (4283, 'GDA94'),
    (4203, 'AGD84'),
    (4202, 'AGD66'),
    (28350, 'GDA94 / MGA zone 50'),
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


DEFAULT_SITE_ID = 16120
