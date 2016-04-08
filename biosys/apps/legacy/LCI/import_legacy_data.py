from __future__ import unicode_literals, print_function
import os
from os import path
from openpyxl import load_workbook
import logging

logger = logging.getLogger('import_lci')

from main.models import *
from vegetation.models import *
from animals.models import *
from species.models import Species
from upload.utils_openpyxl import TableData

DATA_FILE = 'LCI_NC_MonSiteData_15Jan2016.xlsx'


def parse_sites(ws):
    table_reader = TableData(ws)
    rows = table_reader.by_rows()
    print('rows', rows)


def import_data(file_path=None):
    if not file_path:
        file_path = path.join(path.dirname(__file__), 'data', DATA_FILE)
    wb = load_workbook(file_path)
    # Sites datasheet
    parse_sites(wb.get_sheet_by_name('Sites'))
