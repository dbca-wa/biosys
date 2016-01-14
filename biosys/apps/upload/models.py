import logging
from django.db import models

from main.models import SiteVisitDataFile


class SiteVisitDataFileError(models.Model):
    file = models.ForeignKey(SiteVisitDataFile)
    message = models.TextField()
    # errors = models.ManyToManyField('CellSheetError')

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.message


# class CellSheetError(models.Model):
#     description = models.TextField(blank=False,
#                                    verbose_name="Description", help_text="")
#     error_label = models.CharField(max_length=30, blank=True,
#                                    verbose_name="label", help_text="")
#     error_code = models.SmallIntegerField(null=True, blank=True,
#                                           verbose_name="Code", help_text="")
#     LEVEL_CHOICES = [
#         (logging.FATAL, "Fatal"),
#         (logging.ERROR, "Error"),
#         (logging.WARNING, "Warning"),
#         (logging.INFO, "Info"),
#         (logging.DEBUG, "Debug"),
#     ]
#     error_level = models.SmallIntegerField(null=False, choices=LEVEL_CHOICES, default=LEVEL_CHOICES[0][0],
#                                            verbose_name="Level", help_text="")
#
#     # The following fields concerned the XLS cell
#     # as in openpyxl.Workbook.get_sheet_by_name()
#     sheet_name = models.CharField(max_length=100, blank=True,
#                                   verbose_name="Sheet name", help_text="")
#     # Index of row and column.
#     # Row and column index should start at 1, like in the
#     # openpyxl.Worksheet.cell(row=1, column=1)
#     # WARNING! when using openpyxl.Worksheet.rows[index] index is the store value -1
#     row_index = models.IntegerField(null=True, blank=True, default=1,
#                                     verbose_name="Row index", help_text="")
#     col_index = models.IntegerField(null=True, blank=True, default=1,
#                                     verbose_name="Column index", help_text="")
#     # coordinate, ex 'A1'. This is the openpyxl coordinate used in:
#     # cell = Worksheet[coordinate] or Worksheet.cell(coordinate=coordinate)
#     coordinate = models.CharField(max_length=10, blank=True,
#                                   verbose_name="Coordinate", help_text="")
#     column_header = models.CharField(max_length=50, blank=True,
#                                      verbose_name="Column Name", help_text="")