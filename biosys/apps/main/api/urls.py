from __future__ import absolute_import, unicode_literals, print_function, division

from django.conf.urls import url
from rest_framework import routers

from main.api import views as main_views


router = routers.DefaultRouter()
router.register(r'projects?', main_views.ProjectViewSet, 'project')
router.register(r'sites?', main_views.SiteViewSet, 'site')
router.register(r'datasets?', main_views.DatasetViewSet, 'dataset')
router.register(r'generic_records?', main_views.GenericRecordViewSet, 'genericRecord')
router.register(r'observations?', main_views.ObservationViewSet, 'observation')
router.register(r'species_observations?', main_views.SpeciesObservationViewSet, 'speciesObservation')

url_patterns = [
    url(r'projects?/(?P<pk>\d+)/sites/?', main_views.ProjectSitesView.as_view(), name='project-sites'),  # bulk sites
    url(r'datasets?/(?P<pk>\d+)/data/?', main_views.DatasetDataView.as_view(), name='dataset-data')  # bulk data upload
]

urls = router.urls + url_patterns

