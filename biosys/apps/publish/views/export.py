import datetime
from django.views.generic import View
from django.shortcuts import get_object_or_404

from main.models import Dataset, GenericRecord, Observation, SpeciesObservation
from main.utils_data_package import Exporter
from main.utils_http import WorkbookResponse


class ExportDataSetView(View):
    def get(self, request, *args, **kwargs):
        ds = get_object_or_404(Dataset, pk=kwargs.get('pk'))
        qs = []
        if ds.type == Dataset.TYPE_GENERIC:
            qs = GenericRecord.objects.filter(dataset=ds).order_by('id')
        elif ds.type == Dataset.TYPE_OBSERVATION:
            qs = Observation.objects.filter(dataset=ds).order_by('id')
        elif ds.type == Dataset.TYPE_SPECIES_OBSERVATION:
            qs = SpeciesObservation.objects.filter(dataset=ds).order_by('id')
        exporter = Exporter(ds, qs)
        wb = exporter.to_workbook()
        now = datetime.datetime.now()
        file_name = ds.name + '_' + now.strftime('%Y-%m-%d-%H%M%S') + '.xlsx'
        response = WorkbookResponse(wb, file_name)
        return response


class ExportTemplateView(View):
    def get(self, request, *args, **kwargs):
        ds = get_object_or_404(Dataset, pk=kwargs.get('pk'))
        exporter = Exporter(ds)
        wb = exporter.to_workbook()
        file_name = ds.name + '_template'
        response = WorkbookResponse(wb, file_name)
        return response
