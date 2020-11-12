from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import re_path
from django.views.generic import TemplateView
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from main.api.permissions import CanViewSwagger
from main.views import DashboardView
from main.api.urls import urls as api_endpoints
from main.urls import download_urlpatterns
from publish.urls import publish_urlpatterns


def home_view_selection_view(request):
    if request.user.is_authenticated:
        return redirect('api/explorer')
    else:
        return redirect('login')


def admin_view_selection_view(request):
    if request.user.is_superuser:
        return admin.site.index(request)
    elif request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')


web_urls = [
    # Authentication URLs
    re_path(r'^logout/$', LogoutView.as_view(), {'next_page': '/login/'}, name='logout'),
    # re_path(r'^login/$', auth_views.login),
    re_path('^', include('django.contrib.auth.urls')),
    # Application URLs
    re_path(r'^download/', include(download_urlpatterns, namespace='download')),
    re_path(r'^admin/logout/$', LogoutView.as_view(), {'next_page': '/'}),
    # use a function to determine where admin/ will resolve to, based on the user
    re_path(r'^admin/$', admin_view_selection_view),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^publish/', include(publish_urlpatterns, namespace='publish')),
    re_path(r'^$', home_view_selection_view, name='home'),
    re_path(r'^dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
    re_path(r'^about/', TemplateView.as_view(template_name='main/about.html'), name='about'),

    # legacy
    re_path(r'^grappelli/', include('grappelli.urls')),  # Grappelli URLS
]

api_urls = [
    re_path(r'^api/', include((api_endpoints, 'api'))),
]

sso_api_urls = [
    re_path(r'^sso-api/', include((api_endpoints, 'sso-api'))),
]

media_urls = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

schema_view = get_schema_view(
    openapi.Info(
        title="Biosys API",
        default_version='v1',
        description="Biosys API Documentation",
    ),
    public=True,
    patterns=api_urls,
    authentication_classes=(SessionAuthentication, BasicAuthentication, TokenAuthentication),
    permission_classes=(CanViewSwagger,)
)

api_doc_urls = [
    re_path(r'^api/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=None), name='doc-json'),
    re_path(r'^api/explorer/$', schema_view.with_ui('swagger', cache_timeout=None), name='doc-swagger'),
    re_path(r'^api/redoc/$', schema_view.with_ui('redoc', cache_timeout=None), name='doc-redoc'),
]

urlpatterns = web_urls + api_urls + api_doc_urls + media_urls + sso_api_urls
