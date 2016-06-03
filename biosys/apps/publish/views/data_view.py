from django.views.generic import TemplateView, View
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy

from main.models import Project, DataSet


class DataView(LoginRequiredMixin, TemplateView):
    template_name = 'data_view.html'

    def get_context_data(self, **kwargs):
        if 'projects' not in kwargs:
            kwargs['projects'] = Project.objects.all()
        return super(DataView, self).get_context_data(**kwargs)


