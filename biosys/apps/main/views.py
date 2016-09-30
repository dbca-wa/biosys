from __future__ import absolute_import, unicode_literals, print_function, division

import csv
import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView, FormView

from main.forms import UploadDatasetForm
from main.models import Dataset, DatasetFile, Site, MODEL_SRID
from main.utils_species import HerbieFacade


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'main/dashboard.html'


class UploadDataSetView(LoginRequiredMixin, FormView):
    # TODO: use API for this view
    template_name = 'main/data_upload.html'
    form_class = UploadDatasetForm
    success_url = reverse_lazy('admin:main_dataset_changelist')

    def get_context_data(self, **kwargs):
        kwargs['opts'] = Dataset._meta
        return super(UploadDataSetView, self).get_context_data(**kwargs)

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        dataset = get_object_or_404(Dataset, pk=pk)

        error_url = reverse_lazy('admin:main_dataset_change', args=[pk])
        src_file = DatasetFile(file=self.request.FILES['file'], dataset=dataset, uploaded_by=self.request.user)
        src_file.save()
        is_append = form.cleaned_data['append_mode']
        create_site = form.cleaned_data['create_site']
        schema = dataset.schema_class(dataset.schema_data)
        record_model = dataset.record_model
        # if species. First load species list from herbie. Should raise an exception if problem.
        species_id_by_name = None
        if dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
            species_id_by_name = HerbieFacade().name_id_by_species_name()

        with open(src_file.path) as csvfile:
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
                                        e
                                    ))
                            else:
                                msg = "Row #{}: could not find the site '{}':".format(row_number, data)
                                errors.append(msg)
                    record = record_model(
                        site=site,
                        dataset=dataset,
                        data=row,
                    )
                    # specific fields
                    try:
                        if dataset.type == Dataset.TYPE_OBSERVATION or dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                            observation_date = schema.cast_record_observation_date(row)
                            # convert to datetime with timezone awareness
                            if isinstance(observation_date, datetime.date):
                                observation_date = datetime.datetime.combine(observation_date, datetime.time.min)
                            tz = dataset.project.timezone or timezone.get_current_timezone()
                            record.datetime = timezone.make_aware(observation_date, tz)
                            # geometry
                            geometry = schema.cast_geometry(row, default_srid=MODEL_SRID)
                            record.geometry = geometry
                            if dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                                # species stuff. Lookup for species match in herbie
                                species_name = schema.cast_species_name(row)
                                name_id = int(species_id_by_name.get(species_name, -1))
                                record.species_name = species_name
                                record.name_id = name_id

                    except Exception as e:
                        msg = "> Row #{}: problem while extracting the Observation data: {}. [{}]".format(row_number, e,
                                                                                                          row)
                        errors.append(msg)
                    records.append(record)
            if not errors:
                if not is_append:
                    record_model.objects.filter(dataset=dataset).delete()
                record_model.objects.bulk_create(records)
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
