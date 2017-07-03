from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from main.views import DashboardView
from .api import urls as api_urls
from main.urls import download_urlpatterns


def home_view_selection_view(request):
    if request.user.is_authenticated():
        return redirect('dashboard')
    else:
        return redirect('login')


def admin_view_selection_view(request):
    if request.user.is_superuser:
        return admin.site.index(request)
    elif request.user.is_authenticated():
        return redirect('dashboard')
    else:
        return redirect('login')

urlpatterns = \
    [
        # Authentication URLs
        url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),
        # url(r'^login/$', auth_views.login),
        url('^', include('django.contrib.auth.urls')),
        # Application URLs
        url(r'^download/', include(download_urlpatterns, namespace='download')),
        url(r'^admin/logout/$', auth_views.logout, {'next_page': '/'}),
        # use a function to determine where admin/ will resolve to, based on the user
        url(r'^admin/$', admin_view_selection_view),
        url(r'^admin/', include(admin.site.urls)),
        url(r'^publish/', include('publish.urls', namespace='publish')),
        url(r'^$', home_view_selection_view, name='home'),
        url(r'^dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
        url(r'^about/', TemplateView.as_view(template_name='main/about.html'), name='about'),

        # api
        url(r'^api/', include(api_urls, namespace='api')),
        url(r'^sso-api/', include(api_urls, namespace='sso-api')),

        # legacy
        url(r'^grappelli/', include('grappelli.urls')),  # Grappelli URLS

    ] \
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
