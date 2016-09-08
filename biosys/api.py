from __future__ import absolute_import, unicode_literals, print_function, division

from rest_framework import routers
from main.api import views as main_views

from rest_framework.decorators import api_view, renderer_classes
from rest_framework import response, schemas
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer


# swagger schema
@api_view()
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Biosys API')
    return response.Response(generator.get_schema(request=request))


router = routers.DefaultRouter()
router.register(r'projects?', main_views.ProjectViewSet)
router.register(r'sites?', main_views.SiteViewSet)
router.register(r'datasets?', main_views.DatasetViewSet)
router.register(r'genericRecords?', main_views.GenericRecordViewSet)
router.register(r'observations?', main_views.ObservationViewSet)
router.register(r'speciesObservations?', main_views.SpeciesObservationViewSet)


