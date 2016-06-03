from collections import OrderedDict
import csv
import json
from django.conf.urls import url
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest, HttpResponseForbidden
import StringIO
from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.authentication import SessionAuthentication
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash

from . import models
from .admin import readonly_user, user_can_approve
from .utils import flatten


class CSVSerializer(Serializer):
    formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'plist', 'csv']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
        'plist': 'application/x-plist',
        'csv': 'text/csv',
    }

    def to_csv(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        raw_data = StringIO.StringIO()
        first = True

        if 'meta' in data.keys():  # Multiple objects returned
            object_list = []
            objects = data.get('objects')

            for obj in objects:
                obj = flatten(obj)  # Object is now 'flat'
                # Need 2nd pass of flattening to ensure that all objects have all keys.
                for flat_obj in object_list:
                    for k in obj.keys():
                        if k not in flat_obj:
                            flat_obj[k] = None
                object_list.append(obj)

            # Last pass: replace each dict with an OrderedDict, keys sorted alphabetically.
            ordered_obj_list = []
            for d in object_list:
                ordered_obj_list.append(OrderedDict(sorted(d.items(), key=lambda t: t[0])))

            for d in ordered_obj_list:
                if first:
                    writer = csv.DictWriter(raw_data, d.keys(), quoting=csv.QUOTE_ALL)
                    writer.writeheader()
                    writer.writerow(d)
                    first = False
                else:
                    writer.writerow(d)
        else:  # Single object
            d = flatten(data)
            ordered_d = OrderedDict(sorted(d.items(), key=lambda t: t[0]))
            if first:
                writer = csv.DictWriter(raw_data, ordered_d.keys(), quoting=csv.QUOTE_ALL)
                writer.writeheader()
                writer.writerow(ordered_d)
                first = False
            else:
                writer.writerow(ordered_d)
        CSVContent = raw_data.getvalue()
        return CSVContent


class BaseMetaClass:
    """A base class to define comment Meta options for BioSys resource models.
    """
    authentication = SessionAuthentication()
    allowed_methods = ['get']
    serializer = CSVSerializer()


class UserResource(ModelResource):
    """django.contrib.auth User model
    """

    class Meta(BaseMetaClass):
        queryset = User.objects.all()


class ProjectResource(ModelResource):
    class Meta(BaseMetaClass):
        queryset = models.Project.objects.all().order_by('title')
        filtering = {
            'id': ALL,
            'title': ALL,
            'code': ALL,
            'custodian': ['contains', 'icontains'],
            'email': ['contains', 'icontains'],
            'objectives': ['contains', 'icontains'],
            'methodology': ['contains', 'icontains'],
            'funding': ['contains', 'icontains'],
            'duration': ['contains', 'icontains'],
            'datum': ['exact', 'in'],
            'extent_lat_min': ALL,
            'extent_lat_max': ALL,
            'extent_long_min': ALL,
            'extent_long_max': ALL,
            'comments': ['contains', 'icontains'],
        }


class DataSetResource(ModelResource):
    project = fields.ToOneField(
        ProjectResource, attribute='project', readonly=True, full=False)
    data_package = fields.DictField(attribute='data_package')

    class Meta:
        queryset = models.DataSet.objects.all()
        filtering = {
            'id': ALL,
            'name': ALL,
            'project': ALL_WITH_RELATIONS
        }
        authentication = SessionAuthentication()
        allowed_methods = ['get']


class DatumField(fields.IntegerField):
    def convert(self, value):
        if value is None:
            return None
        choices = models.DATUM_CHOICES
        values = [c[1] for c in choices if value == c[0]]
        return values[0] if len(values) > 0 else None


class YesNoBoolean(fields.BooleanField):
    def convert(self, value):
        if value is None:
            return None
        return 'yes' if value else 'no'


class SiteResource(ModelResource):
    project = fields.ToOneField(
        ProjectResource, attribute='project', readonly=True, full=True)
    parent_site = fields.ToOneField(
        'main.api.SiteResource', attribute='project', readonly=True, null=True)
    location = fields.ToOneField(
        'main.api.LocationLookupResource', attribute='location',
        readonly=True, null=True, full=True)
    geology_group = fields.ToOneField(
        'main.api.GeologyGroupLookupResource', attribute='geology_group',
        readonly=True, null=True, full=True)
    vegetation_group = fields.ToOneField(
        'main.api.VegetationGroupLookupResource', attribute='vegetation_group',
        readonly=True, null=True, full=True)
    underlaying_geology = fields.ToOneField(
        'main.api.GeologyLookupResource', attribute='underlaying_geology',
        readonly=True, null=True, full=True)
    closest_water_type = fields.ToOneField(
        'main.api.WaterTypeLookupResource', attribute='closest_water_type',
        readonly=True, null=True, full=True)
    landform_pattern = fields.ToOneField(
        'main.api.LandformPatternLookupResource', attribute='landform_pattern',
        readonly=True, null=True, full=True)
    landform_element = fields.ToOneField(
        'main.api.LandformElementLookupResource', attribute='landform_element',
        readonly=True, null=True, full=True)
    soil_surface_texture = fields.ToOneField(
        'main.api.SoilSurfaceTextureLookupResource', attribute='soil_surface_texture',
        readonly=True, null=True, full=True)

    class Meta(BaseMetaClass):
        queryset = models.Site.objects.all().order_by('site_code')
        filtering = {
            'id': ALL,
            'project': ALL_WITH_RELATIONS,
            'site_ID': ['in', 'exact'],
            'site_code': ALL,
            'date_established': ALL,
            'latitude': ALL,
            'longitude': ALL,
            'datum': ['in', 'exact'],
            'parent_site': ALL_WITH_RELATIONS,
            'custodian': ['contains', 'icontains'],
            'bearing': ALL,
            'width': ALL,
            'height': ALL,
            'aspect': ALL,
            'slope': ALL,
            'altitude': ALL,
            'radius': ALL,
            'location': ALL_WITH_RELATIONS,
            'geology_group': ALL_WITH_RELATIONS,
            'vegetation_group': ALL_WITH_RELATIONS,
            'tenure': ALL,
            'locality_description': ['contains', 'icontains'],
            'underlaying_geology': ALL_WITH_RELATIONS,
            'closest_water_distance': ALL,
            'closest_water_type': ALL_WITH_RELATIONS,
            'landform_pattern': ALL_WITH_RELATIONS,
            'landform_element': ALL_WITH_RELATIONS,
            'soil_surface_texture': ALL_WITH_RELATIONS,
            'soil_colour': ['contains', 'icontains'],
            'photos_taken': ['contains', 'icontains'],
            'historical_info': ['contains', 'icontains'],
            'comments': ['contains', 'icontains'],
        }


class VisitResource(ModelResource):
    project = fields.ToOneField(
        ProjectResource, attribute='project', readonly=True, full=True)
    validation_error_count = fields.IntegerField(readonly=True)

    class Meta(BaseMetaClass):
        queryset = models.Visit.objects.all().order_by('name')
        filtering = {
            'id': ALL,
            'project': ALL_WITH_RELATIONS,
            'name': ALL,
            'start_date': ['exact', 'gte'],
            'end_date': ['exact', 'lte'],
            'trap_nights': ALL,
            'comments': ['contains', 'icontains'],
        }

    def dehydrate_validation_error_count(self, bundle):
        """Custom dehydrate method to return a count of validation errors.
        """
        return bundle.obj.get_errors().count()


class SiteVisitDataFileResource(ModelResource):
    visit = fields.ToOneField(VisitResource, attribute='visit', readonly=True)
    user = fields.ToOneField(UserResource, attribute='user', readonly=True)
    site = fields.ToOneField(SiteResource, attribute='site', readonly=True, null=True)
    validation_error_count = fields.IntegerField(readonly=True)

    class Meta(BaseMetaClass):
        queryset = models.SiteVisitDataFile.objects.all()
        filtering = {
            'id': ALL,
            'visit': ALL_WITH_RELATIONS,
            'user': ALL_WITH_RELATIONS,
            'site': ALL_WITH_RELATIONS,
        }

    def dehydrate_validation_error_count(self, bundle):
        """Custom dehydrate method to return a count of validation errors.
        """
        return bundle.obj.errors().count()


class SiteVisitResource(ModelResource):
    site = fields.ToOneField(
        SiteResource, attribute='site', readonly=True, full=True)
    visit = fields.ToOneField(
        VisitResource, attribute='visit', readonly=True, full=True)
    data_file = fields.ToOneField(
        SiteVisitDataFileResource, attribute='data_file', readonly=True, full=True, null=True)

    class Meta(BaseMetaClass):
        queryset = models.SiteVisit.objects.all()
        filtering = {
            'id': ALL,
            'site': ALL_WITH_RELATIONS,
            'visit': ALL_WITH_RELATIONS,
            'data_file': ALL_WITH_RELATIONS,
            'data_status': ALL,
        }

    def get_object_list(self, request):
        """Filter the queryset based upon the request user.
        """
        object_list = super(SiteVisitResource, self).get_object_list(request)
        if readonly_user(request.user):
            return object_list.filter(data_status='approved')
        else:
            return object_list

    def prepend_urls(self):
        """Prepend custom endpoints to allow approval/quarantine of a
        SiteVisit object via the API.
        """
        return [
            url(
                r'^(?P<resource_name>{})/(?P<{}>.*?)/update-status{}$'.format(
                    self._meta.resource_name, self._meta.detail_uri_name, trailing_slash()),
                self.wrap_view('site_visit_change_status'),
                name='api_site_visit_change_status'
            ),
        ]

    def site_visit_change_status(self, request, **kwargs):
        """View to change the data_status for a SiteVisit object.
        View should be passed a request parameter called ``status``.
        """
        # Allow POST requests only.
        self.method_check(request, allowed=['post'])
        basic_bundle = self.build_bundle(request=request)
        # Get the object.
        try:
            obj = self.cached_obj_get(bundle=basic_bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpResponseBadRequest('Not found')
        # Test request user permission.
        if not user_can_approve(request.user):
            return HttpResponseForbidden('Forbidden')
        # Finally, call the suitable object method.
        new_status = request.POST.get('status', None) or request.GET.get('status', None)
        if new_status == 'approved':
            obj.approve()
        elif new_status == 'quarantined':
            obj.quarantine()
        else:
            return HttpResponseBadRequest('Invalid status')
        # Return the object serialised detail view.
        return self.get_detail(request, **kwargs)


class AbstractSiteVisitObservationResource(ModelResource):
    """
    The mother of all the models in the datasheet
    """
    site_visit = fields.ToOneField(
        SiteVisitResource, attribute='site_visit', readonly=True, full=True)

    class Meta(BaseMetaClass):
        filtering = {
            'id': ALL,
            'site_visit': ALL_WITH_RELATIONS
        }

    def get_object_list(self, request):
        """Filter the queryset based upon the request user.
        """
        object_list = super(AbstractSiteVisitObservationResource, self).get_object_list(request)
        if readonly_user(request.user):
            return object_list.filter(site_visit__data_status='approved')
        else:
            return object_list


class SpeciesObservationResource(AbstractSiteVisitObservationResource):
    class Meta(BaseMetaClass):
        queryset = models.OldSpeciesObservation.objects.all()
        filtering = {
            'id': ALL,
            'site_visit': ALL_WITH_RELATIONS,
            'input_name': ['contains', 'icontains'],
            'name_id': ALL,
        }


class SiteCharacteristicResource(AbstractSiteVisitObservationResource):
    underlaying_geology = fields.ToOneField(
        'main.api.GeologyLookupResource', attribute='underlaying_geology',
        readonly=True, null=True, full=True)
    closest_water_type = fields.ToOneField(
        'main.api.WaterTypeLookupResource', attribute='closest_water_type',
        readonly=True, null=True, full=True)
    landform_pattern = fields.ToOneField(
        'main.api.LandformPatternLookupResource', attribute='landform_pattern',
        readonly=True, null=True, full=True)
    landform_element = fields.ToOneField(
        'main.api.LandformElementLookupResource', attribute='landform_element',
        readonly=True, null=True, full=True)
    soil_surface_texture = fields.ToOneField(
        'main.api.SoilSurfaceTextureLookupResource', attribute='soil_surface_texture',
        readonly=True, null=True, full=True)

    class Meta(BaseMetaClass):
        queryset = models.SiteCharacteristic.objects.all()
        filtering = {
            'id': ALL,
            'site_visit': ALL_WITH_RELATIONS,
            'underlaying_geology': ALL_WITH_RELATIONS,
            'closest_water_distance': ALL,
            'closest_water_type': ALL_WITH_RELATIONS,
            'landform_pattern': ALL_WITH_RELATIONS,
            'landform_element': ALL_WITH_RELATIONS,
            'soil_surface_texture': ALL_WITH_RELATIONS,
            'soil_colour': ['contains', 'icontains'],
            'comments': ['contains', 'icontains'],
        }


#########################
# Lookup resources
#########################


class AbstractLookupResource(ModelResource):
    """Abstract ModelResource class for lookup models.
    """

    class Meta(BaseMetaClass):
        filtering = {
            'id': ALL,
            'value': ALL,
            'code': ALL,
        }


class LocationLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.LocationLookup.objects.all()


class GeologyGroupLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.GeologyGroupLookup.objects.all()


class VegetationGroupLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.VegetationGroupLookup.objects.all()


class GeologyLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.GeologyLookup.objects.all()


class WaterTypeLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.WaterTypeLookup.objects.all()


class LandformPatternLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.LandformPatternLookup.objects.all()


class LandformElementLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.LandformElementLookup.objects.all()


class SoilSurfaceTextureLookupResource(AbstractLookupResource):
    class Meta(AbstractLookupResource.Meta):
        queryset = models.SoilSurfaceTextureLookup.objects.all()
