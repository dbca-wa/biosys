from django.urls import re_path

from apps.publish.views import data_view, export

publish_urlpatterns = ([
    re_path(r'^$', data_view.DataView.as_view(), name='data_view'),
    re_path(r'^data/(?P<pk>\d+)/?$', data_view.JSONDataTableView.as_view(), name='data_json'),
    re_path(r'^export/(?P<pk>\d+)/?$', export.ExportDataSetView.as_view(), name='data_export'),
    re_path(r'^export-template/(?P<pk>\d+)/?$', export.ExportTemplateView.as_view(), name='data_export_template')
], 'publish')
