from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.contrib import admin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
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
    path('logout/', auth_views.LogoutView.as_view(), {'next_page': '/login/'}, name='logout'),
    # url(r'^login/$', auth_views.login),
    path('', include('django.contrib.auth.urls')),
    # Application URLs
    path('download/', include(download_urlpatterns, namespace='download')),
    path('admin/logout/', auth_views.LogoutView.as_view(), {'next_page': '/'}),
    # use a function to determine where admin/ will resolve to, based on the user
    path('admin/', admin_view_selection_view),
    path('admin/', admin.site.urls),
    path('publish/', include(publish_urlpatterns, namespace='publish')),
    path('', home_view_selection_view, name='home'),
    path('dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
    path('about/', TemplateView.as_view(template_name='main/about.html'), name='about'),

    # legacy
    path('grappelli/', include('grappelli.urls')),  # Grappelli URLS
]

api_urls = [
    # path('api/', include(api_endpoints, namespace='api')),
    path('api/', include((api_endpoints, 'api'), namespace=None)),
]

sso_api_urls = [
    # path('sso-api/', include(api_endpoints, namespace='sso-api')),
    path('sso-api/', include((api_endpoints, 'sso-api'), namespace=None)),
]

media_urls = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

schema_view = get_schema_view(
    openapi.Info(
        title="Biosys API",
        default_version='v1',
        description="Biosys API Documentation",
    ),
    public=True,
    patterns=api_urls
)

api_doc_urls = [
    re_path(r'^api/swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=None), name='doc-json'),
    path('api/explorer/', schema_view.with_ui('swagger', cache_timeout=None), name='doc-swagger'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=None), name='doc-redoc'),
]

urlpatterns = web_urls + api_urls + api_doc_urls + media_urls + sso_api_urls