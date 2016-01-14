from django.conf.urls import url
from .views import SpeciesNamesJSON

urlpatterns = [
    url(r'^$', SpeciesNamesJSON.as_view(), name='species_names_json'),
]
