from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf.urls import url
from rest_framework import response, schemas
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer

from main.api.urls import urls as api_urls


# swagger schema
@api_view()
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Biosys API', url='/api/', patterns=api_urls)
    return response.Response(generator.get_schema(request=request))


url_patterns = [
    url(r'explorer/', schema_view, name='explorer'),
]

urls = api_urls + url_patterns
