from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf.urls import url
from rest_framework import routers
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import response, schemas
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from main.api import views as main_views


# swagger schema
@api_view()
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Biosys API')
    return response.Response(generator.get_schema(request=request))


router = routers.DefaultRouter()
router.register(r'projects?', main_views.ProjectViewSet, 'project')
router.register(r'sites?', main_views.SiteViewSet, 'site')
router.register(r'datasets?', main_views.DatasetViewSet, 'dataset')
router.register(r'genericRecords?', main_views.GenericRecordViewSet, 'genericRecord')
router.register(r'observations?', main_views.ObservationViewSet, 'observation')
router.register(r'speciesObservations?', main_views.SpeciesObservationViewSet, 'speciesObservation')

url_patterns = [
    url(r'auth-token/', obtain_auth_token, name="auth_token")
]

urls = router.urls + url_patterns
