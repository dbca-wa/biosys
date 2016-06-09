from django.conf.urls import url
from apps.publish.views import data_view

urlpatterns = [
    url(r'^$', data_view.DataView.as_view(), name='data_view'),
    url(r'^data/(?P<pk>\d+)/?$', data_view.JSONDataTableView.as_view(), name='data_json'),
]
