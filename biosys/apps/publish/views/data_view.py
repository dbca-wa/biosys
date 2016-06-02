from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class DataView(LoginRequiredMixin, TemplateView):
    template_name = 'data_view.html'
