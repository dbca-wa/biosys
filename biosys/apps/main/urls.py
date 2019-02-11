from django.urls import path

from main import views as main_views

download_urlpatterns = ([
    path('templates/site/lat-long/',
        main_views.SiteTemplateView.as_view(model='lat_long'),
        name="site-template-lat-long"
        ),
    path('templates/site/easting-northing/',
        main_views.SiteTemplateView.as_view(model='easting_northing'),
        name="site-template-easting-northing"
        ),
], 'download')