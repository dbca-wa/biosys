from __future__ import absolute_import, unicode_literals, print_function, division

from django.urls import re_path
from rest_framework import routers
from djoser import views as djoser_views

from main.api import views as api_views

router = routers.DefaultRouter()
router.register(r'users?', api_views.UserViewSet, 'user')
router.register(r'programs?', api_views.ProgramViewSet, 'program')
router.register(r'projects?', api_views.ProjectViewSet, 'project')
router.register(r'sites?', api_views.SiteViewSet, 'site')
router.register(r'datasets?', api_views.DatasetViewSet, 'dataset')
router.register(r'forms?', api_views.FormViewSet, 'form')
router.register(r'records?', api_views.RecordViewSet, 'record')
router.register(r'media', api_views.MediaViewSet, 'media')
router.register(r'project-media', api_views.ProjectMediaViewSet, 'project-media')
router.register(r'dataset-media', api_views.DatasetMediaViewSet, 'dataset-media')


url_patterns = [
    re_path(r'auth-token/', api_views.ObtainAuthToken.as_view(), name="auth-token"),
    re_path(r'projects?/(?P<pk>\d+)/sites/?', api_views.ProjectSitesView.as_view(), name='project-sites'),  # bulk sites
    re_path(r'projects?/(?P<pk>\d+)/upload-sites/?', api_views.ProjectSitesUploadView.as_view(),
        name='upload-sites'),  # file upload for sites
    re_path(r'datasets?/(?P<pk>\d+)/records/?', api_views.DatasetRecordsView.as_view(), name='dataset-records'),
    # upload data files
    re_path(r'datasets?/(?P<pk>\d+)/upload-records/?', api_views.DatasetUploadRecordsView.as_view(),
        name='dataset-upload'),
    re_path(r'statistics/?', api_views.StatisticsView.as_view(), name="statistics"),
    re_path(r'whoami/?', api_views.WhoamiView.as_view(), name="whoami"),
    re_path(r'species/?', api_views.SpeciesView.as_view(), name="species"),
    re_path(r'logout/?', api_views.LogoutView.as_view(), name="logout"),
    # utils
    re_path(r'utils/geometry-to-data/dataset/(?P<pk>\d+)/?',
        api_views.GeoConvertView.as_view(output='data'),
        name="geometry-to-data"
        ),
    re_path(r'utils/data-to-geometry/dataset/(?P<pk>\d+)/?',
        api_views.GeoConvertView.as_view(output='geometry'),
        name="data-to-geometry"
        ),
    re_path(r'utils/infer-dataset/?', api_views.InferDatasetView.as_view(), name='infer-dataset'),
    re_path(r'^password/?$', djoser_views.UserViewSet.as_view({'post': 'set_password'}), name='set-password'),
    re_path(
        r'^password/reset/?$',
        djoser_views.UserViewSet.as_view({'post': 'reset_password'}),
        name='password-reset'
    ),
    re_path(
        r'^password/reset/confirm/?$',
        djoser_views.UserViewSet.as_view({'post': 'reset_password_confirm'}),
        name='password-reset-confirm'
    ),
]

app_name = 'api'
urls = router.urls + url_patterns
