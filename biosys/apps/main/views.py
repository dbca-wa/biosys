from __future__ import absolute_import, unicode_literals, print_function, division

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.cell import WriteOnlyCell
from django.http import HttpResponseBadRequest

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from main.utils_http import WorkbookResponse


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'main/dashboard.html'


class SiteTemplateView(View):

    MODEL_LAT_LONG = "lat_long"
    MODEL_EASTING_NORTHING = "easting_northing"
    model = MODEL_LAT_LONG

    COMMON_HEADERS = ['Name', 'Code', 'Description']
    LAT_LONG_HEADERS = ['Latitude', 'Longitude', 'Datum']
    EASTING_NORTHING_HEADERS = ['Easting', 'Northing', 'Datum', 'Zone']

    HEADER_FONT = Font(bold=True)

    def get(self, request, **kwargs):
        if self.model == self.MODEL_LAT_LONG:
            headers = self.COMMON_HEADERS + self.LAT_LONG_HEADERS
        elif self.model == self.MODEL_EASTING_NORTHING:
            headers = self.COMMON_HEADERS + self.EASTING_NORTHING_HEADERS
        else:
            return HttpResponseBadRequest("Unknown site template model {}. Must be one of {}.".format(
                self.model,
                [self.MODEL_LAT_LONG, self.MODEL_EASTING_NORTHING]
            ))
        wb = Workbook(write_only=True)
        ws = wb.create_sheet()
        ws.title = 'Sites'
        cells = []
        for header in headers:
            cell = WriteOnlyCell(ws, value=header)
            cell.font = self.HEADER_FONT
            cells.append(cell)
        ws.append(cells)
        file_name = 'Sites_template_' + self.model
        return WorkbookResponse(wb, file_name=file_name)
