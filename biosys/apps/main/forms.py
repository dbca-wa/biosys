from __future__ import absolute_import, unicode_literals, print_function, division

import datetime
import json

import pytz
from django import forms
from django.contrib.postgres.forms import JSONField
from django.core.exceptions import ValidationError
from django.utils import six

from .models import Project, Site, Dataset

DATUM_BOUNDS = {
    4326: (-180.0, -90.0, 180.0, 90.0),
    4283: (108.0, -45.0, 155.0, -10.0),
    4203: (108.0, -39.0, 155.0, -10.0),
    4202: (129.0, -45.0, 155.0, -1.0)
}


class BetterJSONField(JSONField):
    """
    A form field for the JSONField.
    It fixes the double 'stringification' (see prepare_value), avoid the null text and indent the json.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('widget', forms.Textarea(attrs={'cols': 80, 'rows': 20}))
        super(JSONField, self).__init__(**kwargs)

    def prepare_value(self, value):
        if value is None:
            return ""
        if isinstance(value, six.string_types):
            # already a string
            return value
        else:
            return json.dumps(value, indent=4)


class BetterTimeZoneFormField(forms.TypedChoiceField):
    """
    A fixed version of the TimeZoneFormField from timezone_field (but when updating a model)
    It just ensure that the coerce test if it is already a timezone.
    """

    def __init__(self, *args, **kwargs):

        def coerce_to_pytz(val):
            if isinstance(val, datetime.tzinfo):
                return val
            else:
                try:
                    return pytz.timezone(val)
                except pytz.UnknownTimeZoneError:
                    raise ValidationError("Unknown time zone: '%s'" % val)

        defaults = {
            'coerce': coerce_to_pytz,
            'choices': [(tz, tz) for tz in pytz.common_timezones],
            'empty_value': None,
        }
        defaults.update(kwargs)
        super(BetterTimeZoneFormField, self).__init__(*args, **defaults)


class DataSetForm(forms.ModelForm):
    data_package = BetterJSONField()

    class Meta:
        model = Dataset
        exclude = []


class ProjectForm(forms.ModelForm):
    attributes = BetterJSONField(required=False)
    site_data_package = BetterJSONField(required=False)
    timezone = BetterTimeZoneFormField(initial=Project.DEFAULT_TIMEZONE)

    class Meta:
        model = Project
        exclude = []


class SiteForm(forms.ModelForm):
    attributes_schema = BetterJSONField(required=False)
    attributes = BetterJSONField(required=False)

    class Meta:
        model = Site
        exclude = []

    def clean_latitude(self):
        latitude = self.cleaned_data['latitude']
        bounds = DATUM_BOUNDS[self.cleaned_data['datum']]

        if latitude is not None:
            if latitude < bounds[1] or latitude > bounds[3]:
                raise forms.ValidationError('Latitude must be between %.1f and %.1f' % (bounds[1], bounds[3]))

        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data['longitude']
        bounds = DATUM_BOUNDS[self.cleaned_data['datum']]

        if longitude is not None:
            if longitude < bounds[0] or longitude > bounds[2]:
                raise forms.ValidationError('Longitude must be between %.1f and %.1f' % (bounds[0], bounds[2]))

        return longitude


class UploadDatasetForm(forms.Form):
    file = forms.FileField(required=True, help_text='CSV files only')
    append_mode = forms.BooleanField(required=False, initial=False,
                                     help_text="If checked data will be added to the current set")
    create_site = forms.BooleanField(required=False, initial=False,
                                     help_text="Check if you want to dynamically create site (not recommended)")

    def clean(self):
        if 'file' in self.cleaned_data and hasattr(self.cleaned_data['file'], 'content_type'):
            # cvs only (possibly others in future).
            mime = [
                'text/csv',
                'application/vnd.ms-excel',
                'application/vnd.msexcel'
                'text/comma-separated-values',
                'application/csv'
            ]
            f = self.cleaned_data['file'].content_type
            if f not in mime:
                msg = '{} is not an allowed file type'.format(f)
                self._errors['file'] = self.error_class([msg])
            return self.cleaned_data
