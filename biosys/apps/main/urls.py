from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^dataset/upload/(?P<pk>\d+)/?$', views.UploadDataSetView.as_view(), name='dataset_upload'),

    # legacy
    url(r'^utils/dump_lookups/?$', views.dump_lookup_view, name="dump_lookup"),
    url(r'^datasheet/schema/?$', views.datasheet_schema_view, name='datasheet_schema'),
]
