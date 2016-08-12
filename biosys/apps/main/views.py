import csv
import json
import tempfile
import datetime

from braces.views import FormMessagesMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, FormView
from django.utils import timezone

from envelope.views import ContactView

from main import utils as utils_model
from main.admin import readonly_user
from main.forms import FeedbackForm, UploadDataForm
from main.models import DataSet, DataSetFile, Site, MODEL_SRID
from main.utils_zip import zip_dir_to_temp_zip, export_zip
from upload.validation import DATASHEET_MODELS_MAPPING


class DashboardView(LoginRequiredMixin, TemplateView):
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


class UploadDataSetView(LoginRequiredMixin, FormView):
    # TODO: implement Observation and SpeciesObservation upload
    template_name = 'main/data_upload.html'
    form_class = UploadDataForm
    success_url = reverse_lazy('admin:main_dataset_changelist')

    def get_context_data(self, **kwargs):
        kwargs['opts'] = DataSet._meta
        return super(UploadDataSetView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        dataset = get_object_or_404(DataSet, pk=pk)

        error_url = reverse_lazy('admin:main_dataset_change', args=[pk])
        if dataset.type == DataSet.TYPE_SPECIES_OBSERVATION:
            messages.error(self.request, 'Import of data set of type ' + dataset.type + " is not yet implemented")
            return HttpResponseRedirect(reverse_lazy('admin:main_dataset_change', args=[pk]))
        src_file = DataSetFile(file=self.request.FILES['file'], dataset=dataset, uploaded_by=self.request.user)
        src_file.save()
        is_append = form.cleaned_data['append_mode']
        create_site = form.cleaned_data['create_site']
        schema = dataset.schema_model(dataset.schema)
        Record = dataset.record_model
        with open(src_file.path, 'rb') as csvfile:
            reader = csv.DictReader(csvfile)
            records = []
            row_number = 1
            warnings = []
            errors = []
            site_fk = schema.get_fk_for_model('Site')
            if site_fk is None or site_fk.model_field is None:
                warnings.append(
                    "The schema doesn't include a a related link to a Site model. The data won't be linked to a Site")
            for row in reader:
                row_number += 1
                field_errors = schema.get_error_fields(row)
                if len(field_errors) > 0:
                    for field_name, data in field_errors:
                        msg = "Row #{}, '{}': {}".format(row_number, field_name, data.get('error'))
                        errors.append(msg)
                else:
                    # data valid
                    #  find site
                    site = None
                    if site_fk:
                        model_field = site_fk.model_field
                        data = row.get(site_fk.data_field)
                        kwargs = {
                            "project": dataset.project,
                            model_field: data
                        }
                        site = Site.objects.filter(**kwargs).first()
                        if site is None:
                            if create_site:
                                try:
                                    site = Site.objects.create(**kwargs)
                                except Exception as e:
                                    errors.append("Error while creating the site '{}': {}".format(
                                        data,
                                        e.message
                                    ))
                            else:
                                msg = "Row #{}: could not find the site '{}':".format(row_number, data)
                                errors.append(msg)
                    record = Record(
                        site=site,
                        dataset=dataset,
                        data=row,
                    )
                    # specific fields
                    try:
                        if dataset.type == DataSet.TYPE_OBSERVATION or dataset.type == DataSet.TYPE_SPECIES_OBSERVATION:
                            observation_date = schema.cast_record_observation_date(row)
                            # convert to datetime with timezone awareness
                            if isinstance(observation_date, datetime.date):
                                observation_date = datetime.datetime.combine(observation_date, datetime.time.min)
                            tz = dataset.project.timezone or timezone.get_current_timezone()
                            record.datetime = timezone.make_aware(observation_date, tz)
                            # geometry
                            geometry = schema.cast_geometry(row, default_srid=MODEL_SRID)
                            record.geometry = geometry
                    except Exception as e:
                        msg = "> Row #{}: problem while extracting the Observation data: {}. [{}]".format(row_number, e,
                                                                                                          row)
                        errors.append(msg)
                    records.append(record)
            if not errors:
                if not is_append:
                    Record.objects.filter(dataset=dataset).delete()
                Record.objects.bulk_create(records)
                if warnings:
                    msg = "{} records imported but with the following warnings: \n {}".format(
                        len(records),
                        '<br>'.join(warnings)
                    )
                    messages.warning(self.request, msg)
                    return HttpResponseRedirect(error_url)
                else:
                    msg = "{} records successfully imported in dataset '{}'".format(
                        len(records), dataset
                    )
                    messages.success(self.request, msg)
            else:
                src_file.delete()
                msg = '<br>'.join(errors)
                messages.error(self.request, msg)
                return HttpResponseRedirect(error_url)

        return super(UploadDataSetView, self).form_valid(form)
