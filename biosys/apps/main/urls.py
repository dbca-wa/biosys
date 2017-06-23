from django.conf.urls import url

from main import views as main_views

urlpatterns = [
    url(r'download/templates/site/lat-long/?',
        main_views.SiteTemplateView.as_view(model='lat_long'),
        name="site-template-lat-long"
        ),
    url(r'download/templates/site/easting-northing/?',
        main_views.SiteTemplateView.as_view(model='easting_northing'),
        name="site-template-easting-northing"
        ),
]
