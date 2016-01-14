from django.conf.urls import url
import views


urlpatterns = [
    url(r'^datasheet/visit/(?P<pk>\d+)/?$', views.download_visit_datasheet_view, name='download_visit_datasheet')
]
