import json
import tempfile
import csv

from braces.views import FormMessagesMixin
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View, FormView
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from envelope.views import ContactView

from main import utils as utils_model
from main.admin import readonly_user
from main.forms import FeedbackForm, UploadDataForm
from main.models import DataSet, DataFile, GenericRecord
from main.utils_data_package import to_template_workbook
from main.utils_http import WorkbookResponse
from main.utils_zip import zip_dir_to_temp_zip, export_zip
from upload.validation import DATASHEET_MODELS_MAPPING


class DashboardView(TemplateView):
    template_name = 'main/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)
        context['readonly_user'] = readonly_user(self.request.user)
        return context


def dump_lookup_view(request):
    working_dir = tempfile.mkdtemp()
    utils_model.dump_lookups_json(working_dir)
    zip_file = zip_dir_to_temp_zip(working_dir, delete_after=True)
    zip_name = "biosys_lookups"
    return export_zip(zip_file, zip_name, delete_after=True)


def datasheet_schema():
    """
    expose a json schema of all the models/fields used to create a SiteVisit from a datasheet.
    This method only export the models in the datasheet (main, vegetation, animals) anf their fields
    Current implementation only export fields that are in the datasheet.
    The order in the models and fields arrays respect the order in the datasheet
    """

    def get_model_data(model_):
        return {
            'name': model_._meta.model_name,
            'module': model_.__module__,
            'class_name': model_.__name__,
            'verbose_name': model._meta.verbose_name,
            'name_plural': model._meta.verbose_name_plural.capitalize()
        }

    def get_field_data(field_):
        return {
            'name': field_.name,
            'is_datasheet_field': utils_model.is_template_field(field_),
            'datasheet_name': utils_model.get_datasheet_field_name(field_),
            'is_lookup': utils_model.is_lookup_field(field_),
            'is_mandatory': utils_model.is_mandatory(field_),
            'is_species_name': utils_model.is_species_observation_field(field_),
            'is_strict_lookup': utils_model.is_strict_lookup_field(field_),
            'is_boolean': utils_model.is_boolean_field(field_),
            'is_extra_species_attribute': utils_model.is_species_observation_extra_attribute(field),
        }

    def get_datasheet_mapping_data(mapping_):
        return {
            'sheet_name': mapping_.sheet_name,
            'top_left_column': mapping_.top_left_column,
            'top_left_row': mapping_.top_left_row,
            'transpose': mapping_.transpose,
            'mandatory': mapping_.mandatory,
            'unique': mapping_.unique
        }

    # The list of all the models are in the upload app
    datasheet_mappings = DATASHEET_MODELS_MAPPING
    result = {}
    models_data = []
    for mapping in datasheet_mappings:
        model = mapping.model
        data = {}
        data.update(**get_model_data(model))
        data.update({'datasheet_mapping': get_datasheet_mapping_data(mapping)})
        models_data.append(data)
        # we only really want the fields that are in the datasheet
        fields_data = []
        fields = utils_model.get_datasheet_fields_for_model(model)
        for field in fields:
            fields_data.append(get_field_data(field))
        data.update({'fields': fields_data})
    result.update({'models': models_data})
    return result


def datasheet_schema_view(request):
    """Returns a response containing the JSON schema.
    """
    if not request.user.is_authenticated():
        return HttpResponseForbidden('Forbidden')

    result = datasheet_schema()
    return HttpResponse(json.dumps(result), content_type='application/json')


class FeedbackView(FormMessagesMixin, ContactView):
    form_valid_message = 'Thank you for your feedback.'
    form_invalid_message = 'Oh snap, something went wrong!'
    form_class = FeedbackForm
    template_name = 'envelope/feedback.html'
    success_url = 'home'


class DataSetTemplateView(View):
    def get(self, request, *args, **kwargs):
        ds = get_object_or_404(DataSet, pk=kwargs.get('pk'))
        wb = to_template_workbook(ds)
        response = WorkbookResponse(wb, ds.name)
        return response


class UploadDataSetView(FormView):
    template_name = 'main/data_upload.html'
    form_class = UploadDataForm
    success_url = reverse_lazy('admin:main_datadescriptor_changelist')

    def get_context_data(self, **kwargs):
        kwargs['opts'] = DataSet._meta
        return super(UploadDataSetView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        descriptor = get_object_or_404(DataSet, pk=pk)
        if descriptor.type != DataSet.TYPE_GENERIC:
            messages.error(self.request, 'Import of data set of type ' + descriptor.type + " is not yet implemented")
            return HttpResponseRedirect(reverse_lazy('admin:main_datadescriptor_change', args=[pk]))
        src_file = DataFile(file=self.request.FILES['file'])
        src_file.save()
        is_append = form.cleaned_data['append_mode']
        if not is_append:
            GenericRecord.objects.filter(data_descriptor=descriptor).delete()
        with open(src_file.path, 'rb') as csvfile:
            reader = csv.DictReader(csvfile)
            records = []
            for row in reader:
                record = GenericRecord(
                    data_descriptor=descriptor,
                    data=row,
                    src_file=src_file
                )
                records.append(record)
            GenericRecord.objects.bulk_create(records)
        return super(UploadDataSetView, self).form_valid(form)


class ExportDataSetView(View):
    pass
