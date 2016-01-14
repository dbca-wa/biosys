from __future__ import unicode_literals, print_function
import collections
import os

from openpyxl import Workbook
from django.conf import settings
from django.apps import apps
from django.core import serializers

from animals.models import *


def flatten(d, parent_key='', sep=' '):
    """Utility function to flatten nested dictionaries recursively.
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def is_species_observation_field(field):
    return field.is_relation and field.related_model == SpeciesObservation


def is_species_observation_extra_attribute(field):
    return field in get_extra_species_fields()


def is_lookup_field(field):
    return field.is_relation and is_lookup_model(field.related_model)


def is_strict_lookup_field(field):
    return is_lookup_field(field) and field.related_model.strict


def has_related_objects(field):
    return field.related_model.objects.count() > 0


def is_integer_field(field):
    # this also return true for SmallInteger and PositiveInteger
    return isinstance(field, models.IntegerField)


def is_boolean_field(field):
    return isinstance(field, models.BooleanField) or isinstance(field, models.NullBooleanField)


def is_float_field(field):
    return isinstance(field, models.FloatField)


def is_date_field(field):
    return isinstance(field, models.DateField)


def is_string_field(field):
    return isinstance(field, models.CharField) or isinstance(field, models.TextField)


def is_lookup_model(model):
    return model._meta.model_name.lower().endswith('lookup')


def get_lookup_fields(model):
    return [f for f in model._meta.fields if is_lookup_field(f)]


def has_choices(field):
    return field.choices is not None and len(field.choices) > 0


def get_field_choices(field):
    return field.choices


def is_mandatory(field):
    return field.blank is False


def get_field_lookup_values(field):
    return [l[0] for l in get_field_lookups(field)]


def get_field_lookup_codes(field):
    """
    WARNING: code can be blank. We filter them
    """
    return [l[1] for l in get_field_lookups(field) if len(l[1]) > 0]


def get_field_lookups(field):
    """
    :return [(value, code)]
    Only return the not deprecated lookups
    """
    if not is_lookup_field(field):
        raise Exception("The field {} is not a lookup field".format(field))
    else:
        return [(str(o.value), str(o.code)) for o in field.related_model.objects.filter(deprecated=False)]


def get_field_lookup_model_name(field):
    return get_field_related_model_name(field)


def get_field_related_model_name(field):
    return field.related_model._meta.model_name if field.related_model else None


def get_app_lookup_models(app_name):
    return [m for m in apps.get_app_config(app_name).models.values() if is_lookup_model(m)]


def get_field_verbose_name(model, field_name):
    return model._meta.get_field_by_name(field_name)[0].verbose_name


def is_template_field(field):
    is_pk = field.primary_key
    is_fk = field.is_relation
    is_lookup = is_lookup_field(field)
    is_species = is_fk and field.related_model == SpeciesObservation
    return not is_pk and (not is_fk or is_lookup or is_species)


def get_datasheet_name_for_model(model):
    return model._meta.verbose_name


def get_datasheet_fields_for_model(model):
    model_fields = [f for f in model._meta.fields if is_template_field(f)]
    # BIOSYS-117: add extra fields for species field (validation status/uncertainty)
    all_fields = []
    for field in model_fields:
        all_fields.append(field)
        if is_species_observation_field(field):
            all_fields.extend(get_extra_species_fields())
    return all_fields


def get_extra_species_fields():
    meta = SpeciesObservation._meta
    return [meta.get_field('validation_status'), meta.get_field('uncertainty')]


def get_datasheet_field_names_for_model(model):
    return [get_datasheet_field_name(f) for f in get_datasheet_fields_for_model(model)]


def get_datasheet_field_name(field):
    return field.verbose_name


def get_field_by_verbose_name(model, verbose_name):
    fields = [f for f in model._meta.fields if f.verbose_name == verbose_name]
    if len(fields) > 1:
        # It is important that each model fields has a unique verbose name.
        # Better raise an exception than mixing data.
        # Note: this should not happen, there is a test for that
        raise Exception("The model {model} has fields with same verbose name: {fields}".format(
            model=model,
            fields=fields
        ))
    return fields[0] if len(fields) > 0 else None


def create_lookups_book(destination=None):
    if destination is None:
        destination = './local/model_lookups.xlsx'
    dir_ = os.path.dirname(destination)
    if not os.path.exists(dir_):
        os.makedirs(dir_)
    wb = Workbook()
    all_apps = [apps.get_app_config(app_name) for app_name in settings.PROJECT_APPS
                if len(get_app_lookup_models(app_name)) > 0]
    for app in all_apps:
        lookup_models = [m for m in app.models.values() if is_lookup_model(m)]
        ws = wb.create_sheet(title=app.name)
        cols = ["Lookup Name", 'Strict', 'Initial Values']
        ws.append(cols)
        ws.append([])
        for model in lookup_models:
            name = model._meta.verbose_name
            strict = 'yes' if model.strict else 'no'
            values = [o.value for o in model.objects.all()]
            first_row = [name, strict]
            ws.append(first_row)
            for value in values:
                ws.append(['', '', value])
            ws.append([])
    wb.remove_sheet(wb.active)
    wb.save(destination)
    return destination


def dump_lookups_json(dest_dir='./local'):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    all_apps = [apps.get_app_config(app_name) for app_name in settings.PROJECT_APPS
                if len(get_app_lookup_models(app_name)) > 0]
    for app in all_apps:
        dest_file = os.path.join(dest_dir, app.name + '-lookups.json')
        acc = []
        lookup_models = [m for m in app.models.values() if is_lookup_model(m)]
        for model in lookup_models:
            for lookup in model.objects.all():
                acc.append(lookup)

        out = open(dest_file, "w")
        data = serializers.serialize("json", acc, indent=4)
        out.write(data)
        out.close()
