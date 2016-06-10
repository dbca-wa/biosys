from django.conf.urls import url
from apps.publish.views import data_view, export

urlpatterns = [
    url(r'^$', data_view.DataView.as_view(), name='data_view'),
    url(r'^data/(?P<pk>\d+)/?$', data_view.JSONDataTableView.as_view(), name='data_json'),
    url(r'^export/(?P<pk>\d+)/?$', export.ExportDataSetView.as_view(), name='data_export')
]
