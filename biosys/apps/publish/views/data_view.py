from __future__ import absolute_import, unicode_literals, print_function, division

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View

from main.models import Project, Dataset, GenericRecord, Observation, SpeciesObservation


class DataView(LoginRequiredMixin, TemplateView):
    template_name = 'data_view.html'

    def get_context_data(self, **kwargs):
        if 'projects' not in kwargs:
            kwargs['projects'] = Project.objects.all()
        return super(DataView, self).get_context_data(**kwargs)


class JSONDataTableView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        ds = get_object_or_404(Dataset, pk=kwargs.get('pk'))
        rows = []
        records = GenericRecord.objects.filter(dataset=ds)
        for record in records:
            rows.append(record.data_with_id)
        records = Observation.objects.filter(dataset=ds)
        for record in records:
            rows.append(record.data_with_id)
        records = SpeciesObservation.objects.filter(dataset=ds)
        for record in records:
            rows.append(record.data_with_id)
        return JsonResponse({
            'data': rows
        })
