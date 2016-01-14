from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from .views import ReportView, DownloadView

urlpatterns = [
    url(r'^$', login_required(ReportView.as_view()), name='publish_report'),
    url(r'^download/$', login_required(DownloadView.as_view()), name='publish_download'),
]
