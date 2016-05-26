from django.http import HttpResponse


class WorkbookResponse(HttpResponse):
    def __init__(self, wb, file_name=None):
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        content_disposition = 'attachment;'

        if file_name is not None:
            if not file_name.lower().endswith('.xlsx'):
                file_name += '.xlsx'
            content_disposition += ' filename=' + file_name

        super(WorkbookResponse, self).__init__(content_type=content_type)
        self['Content-Disposition'] = content_disposition
        wb.save(self)

