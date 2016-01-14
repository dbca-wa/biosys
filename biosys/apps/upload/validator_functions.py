from main import utils as util_model
from main.forms import DATUM_BOUNDS
from main.models import DATUM_CHOICES
from vegetation.models import AbstractGroundCoverObservation

DATUM_VERBOSE_TO_CODE = dict((verbose, code) for code, verbose in DATUM_CHOICES)

def ground_cover_validate(row_data):
    fields = util_model.get_datasheet_fields_for_model(AbstractGroundCoverObservation)
    percentage_total = 0

    verbose_field_names = []
    for field in fields:
        field_sheet_name = util_model.get_datasheet_field_name(field)
        for name, value in row_data:
            if name == field_sheet_name:
                verbose_field_names.append(name)
                if value is not None:
                    percentage_total += value
                break

    if percentage_total != 100.0:
        raise Exception('Ground cover fields ({}) of a row must add up to 100%'.format(', '.join(verbose_field_names)))


def lat_lon_validate(row_data):
    datum = None
    latitude_fields = []
    longitude_fields = []

    for name, value in row_data:
        if 'datum' in name.lower():
            datum = value
        elif 'latitude' in name.lower():
            latitude_fields.append((name, value))
        elif 'longitude' in name.lower():
            longitude_fields.append((name, value))

    bounds = DATUM_BOUNDS[DATUM_VERBOSE_TO_CODE[datum]]

    for lat in latitude_fields:
        if lat[1] < bounds[1] or lat[1] > bounds[3]:
            raise Exception('%s must be between %.1f and %.1f' % (lat[0], bounds[1], bounds[3]))

    for lon in longitude_fields:
        if lon[1] < bounds[0] or lon[1] > bounds[2]:
            raise Exception('%s must be between %.1f and %.1f' % (lon[0], bounds[0], bounds[2]))
