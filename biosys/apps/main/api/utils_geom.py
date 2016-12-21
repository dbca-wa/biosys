from django.contrib.gis.geos import Point

from main.constants import is_supported_datum, get_datum_srid, MODEL_SRID
from main.utils_misc import get_value


class PointParser:
    """
    Given a dictionary this class try to create a point
    Accept latitude/longitude, easting/northing and a datum and return a Point
    If no x or y is found it returns None else returns a Point
    Will raise error if something wrong
    """

    def __init__(self, data, default_srid=MODEL_SRID):
        self.data = data
        self.default_srid = default_srid

    def to_geom(self):
        x = get_value(
            ['longitude', 'long', 'lon', 'easting'],
            self.data
        )
        y = get_value(
            ['latitude', 'lat', 'northing'],
            self.data
        )
        if not x and not y:
            # don't raise for that
            return None
        # from here we should have x and y
        if not x:
            raise Exception("Missing longitude or easting")
        else:
            try:
                x = float(x)
            except:
                raise Exception('{} is not a valid decimal'.format(x))
        if not y:
            raise Exception("Missing latitude or longitude")
        else:
            try:
                y = float(y)
            except:
                raise Exception('{} is not a valid decimal'.format(y))

        datum = get_value(['datum'], self.data)
        if datum and not is_supported_datum(datum):
            raise Exception('Unsupported Datum')
        srid = get_datum_srid(datum) if datum else self.default_srid
        return Point(x, y, srid=srid)
