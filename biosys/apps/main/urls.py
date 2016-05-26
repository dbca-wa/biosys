from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^utils/dump_lookups/?$', views.dump_lookup_view, name="dump_lookup"),
    url(r'^datasheet/schema/?$', views.datasheet_schema_view, name='datasheet_schema'),
    url(r'^descriptor/template/(?P<pk>\d+)/?$', views.DescriptorTemplateView.as_view(), name='descriptor_template'),
    url(r'dataset/upload/(?P<pk>\d+)/?$', views.UploadDataSetView.as_view(), name='dataset_upload'),
    url(r'dataset/export/(?P<pk>\d+)/?$', views.ExportDataSetView.as_view(), name='dataset_export'),
]
