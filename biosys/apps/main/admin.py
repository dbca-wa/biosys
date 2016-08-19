import logging

from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin, GeoModelAdmin
from reversion.admin import VersionAdmin

from main import forms
from main.models import *

logger = logging.getLogger(__name__)

UPLOADERS = 'Uploaders'
CUSTODIANS = 'Data custodians'


def readonly_user(user):
    """Function to return True or False if the passed-in user is not in a
    BioSys user group or a superuser.
    """
    if user.is_superuser or \
            user.groups.filter(name=UPLOADERS).exists() or \
            user.groups.filter(name=CUSTODIANS).exists():
        return False
    return True


def user_can_approve(user):
    """Returns True if the passed-in user is in the 'Data custodians' group,
    or is a superuser.
    """
    return user.is_superuser or user.groups.filter(name=CUSTODIANS).exists()


class MainAppAdmin(VersionAdmin):
    change_form_template = 'main/main_change_form.html'
    change_list_template = 'main/main_change_list.html'

    def get_readonly_fields(self, request, obj=None):
        if not readonly_user(request.user):
            return self.readonly_fields
        else:  # Return all model fields.
            return [f.name for f in self.model._meta.fields]

    def get_actions(self, request):
        actions = super(MainAppAdmin, self).get_actions(request)
        # Conditionally remove the "Delete selected" action.
        if readonly_user(request.user) and 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        # Override changelist_view to add context.
        extra_context = extra_context or {}
        if readonly_user(request.user):
            extra_context.update({
                'title': self.model._meta.verbose_name_plural.capitalize(),
                'readonly_user': True})
        return super(MainAppAdmin, self).changelist_view(request, extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # Override changeform_view to add extra context.
        extra_context = extra_context or {}
        if readonly_user(request.user):
            extra_context.update({
                'title': self.model._meta.verbose_name.capitalize(),
                'readonly_user': True})
        return super(MainAppAdmin, self).changeform_view(request, object_id, form_url, extra_context)


@admin.register(Project)
class ProjectAdmin(MainAppAdmin, OSMGeoAdmin):
    list_display = ('title', 'id', 'code')
    readonly_fields = ['id']
    search_fields = ['title', 'code']
    modifiable = False
    openlayers_url = '//static.dpaw.wa.gov.au/static/libs/openlayers/2.13.1/OpenLayers.js'
    form = forms.ProjectForm

    def get_fields(self, request, obj=None):
        if obj is None:
            fields = self.fields
        else:
            fields = ['id'] + self.fields

            if obj.geometry is not None:
                # if there is a geometry, insert it as second to last field
                fields = fields[:-1] + ['geometry'] + fields[-1:]

        return fields


@admin.register(Site)
class SiteAdmin(MainAppAdmin, GeoModelAdmin):
    change_form_template = 'main/site_change_form.html'
    list_display = [
        'site_code', 'project', 'site_ID', 'site_name', 'parent_site']
    list_filter = ['project', 'parent_site']
    readonly_fields = ['site_ID']
    form = forms.SiteForm
    default_lon = 125.0
    default_lat = -18.0
    default_zoom = 6
    modifiable = False

    openlayers_url = '//static.dpaw.wa.gov.au/static/libs/openlayers/2.13.1/OpenLayers.js'

    class Media:
        css = {'all': ('css/site_admin.css',)}


@admin.register(Dataset)
class DatasetAdmin(MainAppAdmin):
    change_form_template = 'main/dataset_change_form.html'
    list_display = ['name', 'project', 'type']
    list_filter = ['project']
    form = forms.DataSetForm


@admin.register(GenericRecord)
class GenericRecordAdmin(MainAppAdmin):
    list_display = ['dataset', 'data']
    list_filter = ['dataset']
    readonly_fields = ['data']


@admin.register(Observation)
class ObservationAdmin(GenericRecordAdmin):
    pass


@admin.register(SpeciesObservation)
class SpeciesObservationAdmin(GenericRecordAdmin):
    pass