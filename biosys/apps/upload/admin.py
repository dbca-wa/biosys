from django.contrib import admin
from reversion.admin import VersionAdmin

from models import *


@admin.register(SiteVisitDataFileError)
class SiteVisitDataFileErrorAdmin(VersionAdmin):
    list_display = ['file', 'message']
    readonly_fields = ['file']
    change_form_template = 'upload/sitevisitdatafile_change_form.html'

    def get_readonly_fields(self, request, obj=None):
        """Superusers can edit everything, always.
        """
        if request.user.is_superuser:
            return ()
        return super(SiteVisitDataFileErrorAdmin, self).get_readonly_fields(request, obj)

    def get_actions(self, request):
        actions = super(SiteVisitDataFileErrorAdmin, self).get_actions(request)
        # Conditionally remove the "Delete selected" action for non-superusers.
        if not request.user.is_superuser and 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser
