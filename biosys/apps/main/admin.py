import logging
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.admin import OSMGeoAdmin, GeoModelAdmin
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.views.generic import RedirectView
from reversion.admin import VersionAdmin

from upload.models import SiteVisitDataFileError
from upload.validation import SiteDataFileValidator, SiteVisitDataBuilder
from upload.utils import get_sitevisit_from_datasheet

from main.models import *
from main import forms

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
    list_display = ('title', 'id', 'code', 'custodian')
    fields = ['title', 'code', 'custodian', 'email', 'objectives', 'methodology',
              'funding', 'duration', 'datum', 'extent_lat_min', 'extent_lat_max',
              'extent_long_min', 'extent_long_max', 'comments']
    readonly_fields = ['id']
    search_fields = ['title', 'code', 'custodian', 'objectives', 'methodology']
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
        'site_code', 'project', 'site_ID', 'site_name', 'date_established', 'established_by',
        'parent_site']
    list_filter = ['project', 'parent_site']
    readonly_fields = ['site_ID']
    fieldsets = [
        (None, {
            'fields': (
                'project', 'site_ID', 'parent_site', 'site_code', 'site_name', 'date_established', 'established_by',
                'datum', 'latitude', 'longitude', 'accuracy')
        }),
        ('Plot orientation and size (for rectangular quadrats)', {
            'classes': ('grp-collapse',),
            'fields': (('bearing', 'width', 'height'))
        }),
        ('Circular plots', {
            'classes': ('grp-collapse', 'grp-closed'),
            'fields': ('radius',)
        }),
        ('Map', {
            'classes': ('grp-collapse',),
            'fields': ('geometry',)
        }),
        (None, {
            'fields': ('aspect', 'slope', 'altitude', 'location',
                       'geology_group', 'vegetation_group', 'tenure', 'underlaying_geology',
                       'closest_water_distance', 'closest_water_type', 'landform_pattern', 'landform_element',
                       'soil_surface_texture', 'soil_colour', 'photos_taken', 'historical_info', 'comments')
        }),
    ]
    date_hierarchy = 'date_established'
    form = forms.SiteForm
    default_lon = 125.0
    default_lat = -18.0
    default_zoom = 6
    modifiable = False

    openlayers_url = '//static.dpaw.wa.gov.au/static/libs/openlayers/2.13.1/OpenLayers.js'

    class Media:
        css = {'all': ('css/site_admin.css',)}


@admin.register(DataDescriptor)
class DataDescriptorAdmin(MainAppAdmin):
    change_form_template = 'main/data_descriptor_change_form.html'
    list_display = ['name', 'project', 'type']


@admin.register(DataSet)
class DataSetAdmin(VersionAdmin):
    pass


@admin.register(Observation)
class ObservationAdmin(VersionAdmin):
    pass


@admin.register(SpeciesObservation)
class SpeciesObservationAdmin(VersionAdmin):
    pass


@admin.register(Visit)
class VisitAdmin(MainAppAdmin):
    change_form_template = 'main/visit_change_form.html'
    list_display = [
        'name', 'id', 'project', 'sites_display', 'start_date', 'end_date',
        'data_files', 'validation_error_count']
    list_filter = ['project', 'sites']
    date_hierarchy = 'start_date'
    filter_horizontal = ['sites']
    form = forms.VisitForm
    fields = ['project', 'sites', 'name', 'start_date', 'end_date', 'trap_nights',
              'comments']
    readonly_fields = ['id']

    def get_fields(self, request, obj=None):
        if obj is None:
            return self.fields
        else:
            return ['id'] + self.fields

    def sites_display(self, obj):
        return ', '.join([s.site_code for s in obj.sites.all()])

    sites_display.short_description = 'sites'

    def validation_error_count(self, obj):
        return obj.get_errors().count()

    validation_error_count.short_description = 'validation errors'

    def data_files(self, obj):
        url_ = reverse('admin:main_sitevisitdatafile_changelist')
        url_ = url_ + '?' + urlencode({'visit__id__exact': obj.pk})
        count = obj.sitevisitdatafile_set.count()
        return '<a href="{}">Uploaded files: {}</a>'.format(url_, count)

    data_files.allow_tags = True

    def get_urls(self):
        """Add extra views for downloading a blank datasheet,
        and uploading a completed datasheet.
        """
        urls = super(VisitAdmin, self).get_urls()
        app, mdl = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            # url(r'^(\d+)/download-datasheet/$',
            # self.admin_site.admin_view(self.download_datasheet),
            # name='{}_{}_download_datasheet'.format(app, mdl)),
            url(r'^(?P<pk>\d+)/download-datasheet/$',
                RedirectView.as_view(pattern_name='download_visit_datasheet', permanent=False),
                name='{}_{}_download_datasheet'.format(app, mdl)),
            url(r'^(\d+)/upload-datasheet/$',
                self.admin_site.admin_view(self.upload_datasheet),
                name='{}_{}_upload_datasheet'.format(app, mdl)),
            url(r'^(\d+)/confirm_datasheet_upload/(\d+)/$',
                self.admin_site.admin_view(self.confirm_datasheet_upload),
                name='{}_{}_confirm_datasheet_upload'.format(app, mdl))]

        return custom_urls + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Insert a DatasheetForm into the change_view context.
        form = forms.DownloadDatasheetForm()
        context = {'d_form': form}
        return super(VisitAdmin, self).change_view(request, object_id, extra_context=context)

    def download_datasheet(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        self.message_user(request, 'Datasheet for {} downloaded!'.format(obj))
        return super(VisitAdmin, self).change_view(request, object_id)

    def upload_datasheet(self, request, object_id):
        # Read-only users cannot upload datasheets.
        if readonly_user(request.user):
            raise PermissionDenied

        obj = self.get_object(request, unquote(object_id))

        if request.method == 'POST':
            form = forms.UploadDatasheetForm(request.POST, request.FILES)

            if request.POST.get('_cancel'):
                self.message_user(request, 'Datasheet upload cancelled.'.format(obj), level=logging.WARNING)
                return HttpResponseRedirect(reverse('publish_report'))
                # return HttpResponseRedirect(reverse('admin:main_visit_change', args=[object_id]))
            if form.is_valid():
                # create the SiteVisitDataFile
                file_ = form.cleaned_data['file']
                sv_file = SiteVisitDataFile.objects.create(file=file_, visit=obj, user=request.user)

                # get site visit if it exists so that user can be informed that the site visit has
                # already been approved before they have to fix all the errors
                site_visit = get_sitevisit_from_datasheet(sv_file)
                if site_visit is not None and site_visit.data_status == 'approved':
                    self.message_user(request, """Datasheet for this site visit has already been uploaded and approved by the
                    curator, so cannot be overwritten.""".format(obj), level=logging.WARNING)
                    return HttpResponseRedirect(reverse('publish_report'))
                    # return HttpResponseRedirect(reverse('admin:main_visit_change', args=[object_id]))

                validator = SiteDataFileValidator(sv_file)
                error_obj = validator.validate()

                if error_obj:
                    html_error_message = 'The file contains errors:'
                    for error in error_obj.message.split('\n'):
                        html_error_message += '<p>{}</p>'.format(error)

                    self.message_user(request, html_error_message, level=logging.ERROR)
                else:
                    if site_visit is not None:
                        # check if sitevisit already exists here and redirect to confirm page
                        return HttpResponseRedirect(
                            reverse('admin:main_visit_confirm_datasheet_upload', args=[object_id, sv_file.id]))

                    # no error
                    # create the objects
                    self.message_user(request, 'Datasheet for {} successfully uploaded!'.format(obj))
                    builder = SiteVisitDataBuilder(sv_file)
                    builder.build_all(keep_invalid=False)

                    # Return to the publish/data view.
                    return HttpResponseRedirect(reverse('publish_report'))
                    # return HttpResponseRedirect(reverse('admin:main_visit_change', args=[object_id]))

        else:
            form = forms.UploadDatasheetForm()

        context = {
            'original': obj,
            'has_permission': True,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, obj),
            'title': 'Upload a completed datasheet for {}'.format(obj),
            'site_url': admin.site.site_url,
            'errors': form.errors,
            'opts': self.model._meta,
            'is_popup': False,
            'save_as': False,
            'form': form,
        }
        request.current_app = 'main'
        return TemplateResponse(request, "main/visit_upload_datasheet.html", context)

    def confirm_datasheet_upload(self, request, visit_id, sitevisitfile_id):
        # Read-only users cannot upload datasheets.
        if readonly_user(request.user):
            raise PermissionDenied

        obj = self.get_object(request, unquote(visit_id))

        sv_file = SiteVisitDataFile.objects.get(id=sitevisitfile_id)

        if request.method == 'POST':
            if request.POST.get('_confirm'):
                # delete existing sitevisit (which will delete all associated objects)
                SiteVisit.objects.filter(visit=sv_file.visit, site=sv_file.site).delete()

                # create the objects
                self.message_user(request, 'Datasheet for {} successfully uploaded!'.format(obj))
                builder = SiteVisitDataBuilder(sv_file)
                builder.build_all(keep_invalid=False)
            elif request.POST.get('_cancel'):
                self.message_user(request, 'Datasheet upload cancelled.'.format(obj),
                                  level=logging.WARNING)

            return HttpResponseRedirect(reverse('publish_report'))
            # return HttpResponseRedirect(reverse('admin:main_visit_change', args=[visit_id]))

        context = {
            'original': obj,
            'has_permission': True,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request, sv_file.visit),
            'title': 'Confirm upload of a completed datasheet for {}'.format(sv_file.visit),
            'site_url': admin.site.site_url,
            'opts': self.model._meta,
            'is_popup': False,
            'save_as': False,
        }
        return TemplateResponse(request, "main/visit_confirm_datasheet_upload.html", context, current_app='main')


@admin.register(SiteCharacteristic)
class SiteCharacteristicAdmin(VersionAdmin):
    list_display = [
        'site_visit', 'underlaying_geology', 'closest_water_distance',
        'closest_water_type', 'landform_pattern', 'landform_element',
        'soil_surface_texture', 'soil_colour']


@admin.register(SiteVisit)
class SiteVisitAdmin(MainAppAdmin):
    list_display = ['site', 'visit', 'data_file', 'data_status']
    actions = ['make_approved']
    change_form_template = 'main/sitevisit_change_form.html'
    readonly_fields = ['data_status']
    list_filter = ['visit', 'site']

    def get_readonly_fields(self, request, obj=None):
        """Superusers can edit everything, always.
        """
        if request.user.is_superuser:
            return ()
        return super(SiteVisitAdmin, self).get_readonly_fields(request, obj)

    def get_urls(self):
        """Add extra view for approving a SiteVisit.
        """
        urls = super(SiteVisitAdmin, self).get_urls()
        app, mdl = self.model._meta.app_label, self.model._meta.model_name
        custom_urls = [
            url(r'^(\d+)/approve/$',
                self.admin_site.admin_view(self.approve_view),
                name='{}_{}_approve'.format(app, mdl))]
        return custom_urls + urls

    def get_actions(self, request):
        """Conditionally add the 'approve' action to the list of actions.
        """
        actions = super(SiteVisitAdmin, self).get_actions(request)
        if not user_can_approve(request.user):
            if 'make_approved' in actions:
                del actions['make_approved']
        return actions

    def make_approved(self, request, queryset):
        """Custom action to allow multiple SiteVisit objects to have their
        data_status altered to 'Approved' by a user with the required permissions.
        """
        if not user_can_approve(request.user):
            raise PermissionDenied
        opts = self.model._meta

        if request.POST.get('post'):
            count = 0
            for obj in queryset:
                if not obj.is_approved:
                    message = 'Approved {} "{}".'.format(opts.verbose_name, obj)
                    self.log_approval(request, obj, message)
                    obj.approve()
                    count += 1
            self.message_user(
                request,
                'Data for {} site visits was approved successfully.'.format(count),
                messages.SUCCESS)
            return HttpResponseRedirect(request.get_full_path())

        context = {
            'title': 'Are you sure?',
            'object_name': opts.verbose_name_plural,
            'queryset': queryset,
            'opts': opts,
            'app_label': opts.app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(request, 'main/approve_confirmation_selected.html', context)

    make_approved.short_description = 'Mark selected site visit data as approved'

    def log_approval(self, request, obj, message):
        """Log that an object has been approved.
        """
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get(model='sitevisit').pk,
            object_id=obj.pk,
            object_repr=force_text(obj),
            action_flag=CHANGE,
            change_message=message
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['has_approve_permission'] = user_can_approve(request.user)
        return self.changeform_view(request, object_id, form_url, extra_context)

    def approve_view(self, request, object_id, extra_context=None):
        """The 'approve' view for this model. Approves, and then returns the
        response to approving a single SiteVisit object.
        """
        opts = self.model._meta
        app_label = opts.app_label
        obj = self.get_object(request, unquote(object_id))

        if not user_can_approve(request.user):
            raise PermissionDenied

        if obj.is_approved:
            post_url = reverse(
                'admin:{}_{}_change'.format(opts.app_label, opts.model_name),
                args=(object_id))
            return HttpResponseRedirect(post_url)

        if request.POST:
            obj_display = force_text(obj)
            message = 'Approved {} "{}".'.format(opts.verbose_name, obj)
            self.log_approval(request, obj, message)
            obj.approve()
            self.message_user(
                request,
                'The {} "{}" was approved successfully.'.format(opts.verbose_name, obj_display),
                messages.SUCCESS)
            post_url = reverse(
                'admin:{}_{}_change'.format(opts.app_label, opts.model_name),
                args=(object_id))
            return HttpResponseRedirect(post_url)

        object_name = force_text(opts.verbose_name)
        context = {
            'title': 'Are your sure?',
            'object_name': object_name,
            'object': obj,
            'opts': opts,
            'app_label': app_label}
        context.update(extra_context or {})

        return TemplateResponse(request, 'main/approve_confirmation.html', context)


@admin.register(SiteVisitDataFile)
class SiteVisitDataFileAdmin(MainAppAdmin):
    list_display = ['__str__', 'site', 'visit', 'uploaded_date', 'uploaded_by', 'errors_link']
    list_filter = ['site', 'visit', 'user']
    change_form_template = 'main/sitevisitdatafile_change_form.html'
    readonly_fields = ['errors']

    def errors(self, obj):
        # Callable to insert a text field of errors into the change form.
        if obj.errors():
            return '\n'.join([e.message for e in obj.errors()])
        return 'None'

    def uploaded_by(self, obj):
        return obj.user

    def errors_link(self, obj):
        # Callable to display errors for for list_display.
        errors = SiteVisitDataFileError.objects.filter(file=obj)
        if len(errors) == 0:
            return ''
        else:
            error = errors[0]
            url_ = reverse('admin:upload_sitevisitdatafileerror_change', args=(error.pk,))
            return '{text} ...  <a href="{url}">details</a>' \
                .format(text=str(error)[0:100],
                        url=url_)

    errors_link.allow_tags = True
    errors_link.short_description = "Errors"

    def get_model_perms(self, request):
        """This override hides this model from the admin index pages.
        """
        if not request.user.is_superuser:
            return {}
        return super(MainAppAdmin, self).get_model_perms(request)


@admin.register(SiteVisitDataSheetTemplate)
class SiteVisitDataSheetTemplateAdmin(VersionAdmin):
    list_display = ['filename', 'version']
    form = forms.SiteVisitDataSheetTemplateForm


@admin.register(OldSpeciesObservation)
class OldSpeciesObservationAdmin(VersionAdmin):
    list_display = ['input_name', 'name_id', 'valid', 'site_visit']
    pass


#########################
# Lookups
#########################

class AbstractLookupAdmin(VersionAdmin):
    list_display = ['value', 'code', 'deprecated']


@admin.register(GeologyGroupLookup)
class GeologyGroupLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(LocationLookup)
class LocationLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(VegetationGroupLookup)
class VegetationGroupAdmin(AbstractLookupAdmin):
    pass


@admin.register(SoilSurfaceTextureLookup)
class SoilSurfaceTextureLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(LandformElementLookup)
class LandformElementLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(LandformPatternLookup)
class LandformPatternLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(WaterTypeLookup)
class WaterTypeLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(GeologyLookup)
class GeologyLookupAdmin(AbstractLookupAdmin):
    pass
