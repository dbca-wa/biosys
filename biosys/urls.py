from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from main.views import DashboardView
from main.api import urls as main_api_urls


def home_view_selection_view(request):
    if request.user.is_authenticated() and request.user.is_staff:
        return redirect('dashboard')
    else:
        return redirect('login')


def admin_view_selection_view(request):
    if request.user.is_superuser:
        return admin.site.index(request)
    elif request.user.is_authenticated() and request.user.is_staff:
        return redirect('dashboard')
    else:
        return redirect('login')

rest_api_urlpatterns = \
    [
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    ] \
    + main_api_urls.urlpatterns

urlpatterns = \
    [
        # Authentication URLs
        url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}),
        url('^', include('django.contrib.auth.urls')),
        # Application URLs
        url(r'^main/', include('main.urls', namespace='main')),
        url(r'^admin/logout/$', auth_views.logout, {'next_page': '/'}),
        # use a function to determine where admin/ will resolve to, based on the user
        url(r'^admin/$', admin_view_selection_view),
        url(r'^admin/', include(admin.site.urls)),
        url(r'^publish/', include('publish.urls', namespace='publish')),
        url(r'^$', home_view_selection_view, name='home'),
        url(r'^dashboard/', login_required(DashboardView.as_view()), name='dashboard'),
        url(r'^about/', TemplateView.as_view(template_name='main/about.html'), name='about'),

        # legacy
        url(r'^grappelli/', include('grappelli.urls')),  # Grappelli URLS

    ] \
    + rest_api_urlpatterns \
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
