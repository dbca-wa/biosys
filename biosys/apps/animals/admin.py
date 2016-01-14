from django.contrib import admin
from django.utils.text import Truncator
import reversion
from models import *
from main.admin import AbstractLookupAdmin


@admin.register(Trap)
class TrapAdmin(reversion.VersionAdmin):
    list_display = [
        'trapline_ID', 'trap_type', 'site_visit', 'open_date', 'close_date',
        'comments_display']
    list_filter = ['site_visit', 'trap_type']
    date_hierarchy = 'open_date'
    search_fields = ['trapline_ID', 'comments']

    def comments_display(self, obj):
        return Truncator(obj.comments).words(12)
    comments_display.short_description = 'comments'


@admin.register(AnimalObservation)
class AnimalObservationAdmin(reversion.VersionAdmin):
    list_display = [
        'site_visit', 'collector', 'date', 'trap_no', 'trap_type', 'species',
        'microchip_id',  'comments_display']
    list_filter = ['site_visit', 'sex', 'capture_type', 'species']
    date_hierarchy = 'date'
    search_fields = [
        'collector', 'trap_no', 'trap_type', 'microchip_id', 'comments']

    def comments_display(self, obj):
        return Truncator(obj.comments).words(12)
    comments_display.short_description = 'comments'


@admin.register(OpportunisticObservation)
class OpportunisticObservationAdmin(reversion.VersionAdmin):
    list_display = ['site_visit', 'date', 'observer', 'species', 'comments_display']
    list_filter = ['site_visit', 'species']
    date_hierarchy = 'date'
    search_fields = ['observer', 'comments']

    def comments_display(self, obj):
        return Truncator(obj.comments).words(12)
    comments_display.short_description = 'comments'

#########################
# Lookups
#########################


@admin.register(CaptureTypeLookup)
class CaptureTypeLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(SexLookup)
class SexLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(AgeLookup)
class AgeLookupAdmin(AbstractLookupAdmin):
    pass


@admin.register(TrapTypeLookup)
class TrapTypeLookupAdmin(AbstractLookupAdmin):
    pass
