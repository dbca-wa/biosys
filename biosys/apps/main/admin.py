from __future__ import absolute_import, unicode_literals, print_function, division

from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin, GeoModelAdmin

from main import forms
from main.models import *

logger = logging.getLogger(__name__)


class MainAppAdmin(admin.ModelAdmin):
    change_form_template = 'main/main_change_form.html'
    change_list_template = 'main/main_change_list.html'


@admin.register(Project)
class ProjectAdmin(MainAppAdmin, OSMGeoAdmin):
    fields = ('name', 'code', 'datum', 'timezone', 'custodians', 'attributes',
              'description', 'site_data_package', 'geometry')
    filter_horizontal = ('custodians',)  # TODO: why it's not working?
    list_display = ('name', 'id', 'code')
    readonly_fields = ['id']
    search_fields = ['name', 'code']
    openlayers_url = '//static.dpaw.wa.gov.au/static/libs/openlayers/2.13.1/OpenLayers.js'
    form = forms.ProjectForm


@admin.register(Site)
class SiteAdmin(MainAppAdmin, GeoModelAdmin):
    change_form_template = 'main/site_change_form.html'
    fields = ('project', 'parent_site',  'code', 'name', 'geometry', 'description', 'attributes')
    list_display = ['code', 'project', 'name', 'parent_site']
    list_filter = ['project', 'parent_site']
    form = forms.SiteForm
    default_lon = 125.0
    default_lat = -18.0
    default_zoom = 6

    openlayers_url = '//static.dpaw.wa.gov.au/static/libs/openlayers/2.13.1/OpenLayers.js'

    class Media:
        css = {'all': ('css/site_admin.css',)}


@admin.register(Dataset)
class DatasetAdmin(MainAppAdmin):
    change_form_template = 'main/dataset_change_form.html'
    list_display = ['name', 'project', 'type', 'description']
    list_filter = ['project']
    form = forms.DataSetForm


@admin.register(Record)
class RecordAdmin(MainAppAdmin):
    list_display = ['dataset', 'data']
    list_filter = ['dataset']
    readonly_fields = ['data']
