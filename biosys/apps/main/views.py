from __future__ import absolute_import, unicode_literals, print_function, division

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'main/dashboard.html'
