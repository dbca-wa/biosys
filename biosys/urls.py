from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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
    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),
    # url(r'^login/$', auth_views.login),
    url('^', include('django.contrib.auth.urls')),
    # Application URLs
    url(r'^download/', include(download_urlpatterns, namespace='download')),
    url(r'^admin/logout/$', auth_views.logout, {'next_page': '/'}),
    # use a function to determine where admin/ will resolve to, based on the user
    url(r'^admin/$', admin_view_selection_view),
    url(r'^admin/', admin.site.urls),
    url(r'^publish/', include(publish_urlpatterns, namespace='publish')),
    url(r'^$', home_view_selection_view, name='home'),
    url(r'^dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
    url(r'^about/', TemplateView.as_view(template_name='main/about.html'), name='about'),

    # legacy
    url(r'^grappelli/', include('grappelli.urls')),  # Grappelli URLS
]

api_urls = [
    url(r'^api/', include(api_endpoints, namespace='api')),
]

sso_api_urls = [
    url(r'^sso-api/', include(api_endpoints, namespace='sso-api')),
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
    permission_classes=(IsAuthenticated,)
)

api_doc_urls = [
    url(r'^api/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=None), name='doc-json'),
    url(r'^api/explorer/$', schema_view.with_ui('swagger', cache_timeout=None), name='doc-swagger'),
    url(r'^api/redoc/$', schema_view.with_ui('redoc', cache_timeout=None), name='doc-redoc'),
]

urlpatterns = web_urls + api_urls + api_doc_urls + media_urls + sso_api_urls
