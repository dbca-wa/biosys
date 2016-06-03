import json
from django import forms
from django.contrib.postgres.forms import JSONField
from envelope.forms import ContactForm

from .models import Project, SiteVisitDataSheetTemplate, Visit, Site, DataSet

DATUM_BOUNDS = {
    4326: (-180.0, -90.0, 180.0, 90.0),
    4283: (108.0, -45.0, 155.0, -10.0),
    4203: (108.0, -39.0, 155.0, -10.0),
    4202: (129.0, -45.0, 155.0, -1.0)
}


class BetterJSONField(JSONField):
    """
    A form field for the JSONField.
    It fixes the double 'stringification' (see prepare_value)
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('widget', forms.Textarea(attrs={'cols': 80, 'rows': 40}))
        super(JSONField, self).__init__(**kwargs)

    def prepare_value(self, value):
        if isinstance(value, basestring):
            # already a string
            return value
        else:
            return json.dumps(value)


class DataSetForm(forms.ModelForm):
    data_package = BetterJSONField()

    class Meta:
        model = DataSet
        exclude = []


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = []

    def clean_extent_long_min(self):
        extent_long_min = self.cleaned_data['extent_long_min']
        bounds = DATUM_BOUNDS[self.cleaned_data['datum']]

        if extent_long_min is not None and extent_long_min < bounds[0]:
            raise forms.ValidationError('Must be greater than or equal to %.1f' % bounds[0])

        return extent_long_min

    def clean_extent_lat_min(self):
        extent_lat_min = self.cleaned_data['extent_lat_min']
        bounds = DATUM_BOUNDS[self.cleaned_data['datum']]

        if extent_lat_min is not None and extent_lat_min < bounds[1]:
            raise forms.ValidationError('Must be greater than or equal to  %.1f' % bounds[1])

        return extent_lat_min

    def clean_extent_long_max(self):
        extent_long_max = self.cleaned_data['extent_long_max']
        bounds = DATUM_BOUNDS[self.cleaned_data['datum']]

        if extent_long_max is not None and extent_long_max > bounds[2]:
            raise forms.ValidationError('Must be less than or equal to  %.1f' % bounds[2])

        return extent_long_max

    def clean_extent_lat_max(self):
        extent_lat_max = self.cleaned_data['extent_lat_max']
        bounds = DATUM_BOUNDS[self.cleaned_data['datum']]

        if extent_lat_max is not None and extent_lat_max > bounds[3]:
            raise forms.ValidationError('Must be less than or equal to  %.1f' % bounds[3])

        return extent_lat_max

    def clean(self):
        extent_long_min = self.cleaned_data.get('extent_long_min')
        extent_lat_min = self.cleaned_data.get('extent_lat_min')
        extent_long_max = self.cleaned_data.get('extent_long_max')
        extent_lat_max = self.cleaned_data.get('extent_lat_max')

        if extent_long_min is not None and extent_lat_min is not None and extent_long_max is not None and \
                        extent_lat_max is not None:
            if extent_lat_min >= extent_lat_max:
                raise forms.ValidationError('Extent latitude min must be less than Extent latitude max')

            if extent_long_min >= extent_long_max:
                raise forms.ValidationError('Extent longitude min must be less than Extent longitude max')

        return self.cleaned_data


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        exclude = []

    def __init__(self, *args, **kwargs):
        super(VisitForm, self).__init__(*args, **kwargs)
        if self.instance.pk and self.instance.project:
            self.fields['sites'].queryset = Site.objects.filter(project=self.instance.project)
        else:
            self.fields['sites'].queryset = Site.objects.none()

        # override clean method of form field for sites so that it doesn't force site to be in existing
        # queryset - instead do this check in clean
        def sites_clean(value):
            if value is not None and value != '':
                return Site.objects.filter(pk__in=value)
            else:
                return Site.objects.none()

        self.fields['sites'].clean = sites_clean

    def clean(self):
        if 'project' in self.cleaned_data and 'sites' in self.cleaned_data:
            project = self.cleaned_data.get('project')
            sites = self.cleaned_data.get('sites')
            for site in sites:
                if site.project != project:
                    raise forms.ValidationError('Please Choose only sites that '
                                                'belong to project {}'.format(project))
        return self.cleaned_data


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        exclude = []

    def __init__(self, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        if self.instance.pk and self.instance.project:
            self.fields['parent_site'].queryset = Site.objects.filter(project=self.instance.project).exclude(
                pk=self.instance.pk)
        else:
            self.fields['parent_site'].queryset = Site.objects.all()

        # override clean method of form field for parent site so that it doesn't force parent site to be in existing
        # queryset - instead do this check in clean
        def parent_site_clean(value):
            if value is not None and value != '':
                return Site.objects.get(pk=value)
            else:
                return None

        self.fields['parent_site'].clean = parent_site_clean

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

    def clean_bearing(self):
        bearing = self.cleaned_data['bearing']

        if bearing is not None:
            if bearing < 0.0 or bearing > 360.0:
                raise forms.ValidationError('Bearing must be between 0.0 and 360.0')

        return bearing

    def clean_slope(self):
        slope = self.cleaned_data['slope']

        if slope is not None:
            if slope < 0.0 or slope > 90.0:
                raise forms.ValidationError('Slope must be between 0.0 and 90.0')

        return slope

    def clean(self):
        if 'project' in self.cleaned_data and 'parent_site' in self.cleaned_data:
            project = self.cleaned_data.get('project')
            parent_site = self.cleaned_data.get('parent_site')
            if parent_site is not None and parent_site.project != project:
                raise forms.ValidationError('Please Choose only parent site that belongs to project {}'.format(project))
        return self.cleaned_data


class SiteVisitDataSheetTemplateForm(forms.ModelForm):
    """Upload form for local property register spreadsheets.
    """

    class Meta:
        model = SiteVisitDataSheetTemplate
        exclude = []

    def __init__(self, *args, **kwargs):
        super(SiteVisitDataSheetTemplateForm, self).__init__(*args, **kwargs)
        self.fields['file'].help_text = '.xlsx files only'

    def clean(self):
        # Only clean the file field if a file has been uploaded (will skip
        # when updating an existing object that already has a file).
        if 'file' in self.cleaned_data and hasattr(self.cleaned_data['file'], 'content_type'):
            # Allow Excel 2007 mimetype only (possibly others in future).
            mime = [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
            f = self.cleaned_data['file'].content_type
            if f not in mime:
                msg = '{} is not an allowed file type'.format(f)
                self._errors['file'] = self.error_class([msg])
            return self.cleaned_data


class DownloadDatasheetForm(forms.Form):
    datasheets = forms.ModelChoiceField(
        queryset=SiteVisitDataSheetTemplate.objects.all(),
        label='Download blank datasheet')


class UploadDatasheetForm(forms.Form):
    file = forms.FileField(required=True, help_text='.xlsx files only')

    def clean(self):
        if 'file' in self.cleaned_data and hasattr(self.cleaned_data['file'], 'content_type'):
            # Allow Excel 2007 mimetype only (possibly others in future).
            mime = [
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
            f = self.cleaned_data['file'].content_type
            if f not in mime:
                msg = '{} is not an allowed file type'.format(f)
                self._errors['file'] = self.error_class([msg])
            return self.cleaned_data


class UploadDataForm(forms.Form):
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
            ]
            f = self.cleaned_data['file'].content_type
            if f not in mime:
                msg = '{} is not an allowed file type'.format(f)
                self._errors['file'] = self.error_class([msg])
            return self.cleaned_data


class FeedbackForm(ContactForm):
    subject_intro = '[BioSys Feedback]  '
    template_name = 'envelope/email_body.txt'
