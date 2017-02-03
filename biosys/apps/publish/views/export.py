from __future__ import absolute_import, unicode_literals, print_function, division

import datetime

from django.shortcuts import get_object_or_404
from django.views.generic import View

from main.models import Dataset, Record
from main.utils_data_package import Exporter
from main.utils_http import WorkbookResponse


class ExportDataSetView(View):
    def get(self, request, *args, **kwargs):
        ds = get_object_or_404(Dataset, pk=kwargs.get('pk'))
        qs = Record.objects.filter(dataset=ds).order_by('id')
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
