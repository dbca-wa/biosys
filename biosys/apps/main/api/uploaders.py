import codecs
import csv
import datetime

from django.utils import six, timezone
from openpyxl import load_workbook

from main.api.utils_geom import PointParser
from main.api.validators import get_record_validator_for_dataset
from main.constants import MODEL_SRID
from main.models import Site, Dataset
from main.utils_misc import get_value
from main.utils_species import HerbieFacade


def xlsx_to_csv(file):
    output = six.StringIO()
    writer = csv.writer(output)
    wb = load_workbook(filename=file, read_only=True)
    ws = wb.active
    for row in ws.rows:
        r = [cell.value for cell in row]
        writer.writerow(r)
    # rewind
    output.seek(0)
    return output


class SiteUploader:
    CSV_TYPES = [
        'text/csv',
        'text/comma-separated-values',
        'application/csv'
    ]
    XLSX_TYPES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'application/vnd.msexcel',
    ]
    SUPPORTED_TYPES = CSV_TYPES + XLSX_TYPES
    COLUMN_MAP = {
        'code': ['code', 'site code'],
        'name': ['name', 'site name'],
        'comments': ['comments'],
        'parent_site': ['parent site', 'parent']
    }

    def __init__(self, file, project):
        if file.content_type not in self.SUPPORTED_TYPES:
            msg = "Wrong file type {}. Should be one of: {}".format(file.content_type, self.SUPPORTED_TYPES)
            raise Exception(msg)

        self.file = file
        if file.content_type in self.XLSX_TYPES:
            self.file = xlsx_to_csv(file)
            self.reader = csv.DictReader(self.file)
        else:
            self.reader = csv.DictReader(codecs.iterdecode(self.file, 'utf-8'))
        self.project = project

    def __iter__(self):
        for row in self.reader:
            yield self._create_or_update_site(row)

    def close(self):
        self.file.close()

    def _create_or_update_site(self, row):
        # we need the code at minimum
        site, error = (None, None)
        code = get_value(self.COLUMN_MAP.get('code'), row)
        if not code:
            error = "Site Code is missing"
        else:
            kwargs = {
                'name': get_value(self.COLUMN_MAP.get('name'), row, ''),
                'comments': get_value(self.COLUMN_MAP.get('comments'), row, ''),
                'attributes': self._get_attributes(row)
            }
            # geometry
            try:
                geo_parser = PointParser(row, self.project.datum)
                kwargs['geometry'] = geo_parser.to_geom()
            except:
                # not an error (warning?)
                pass
            # parent site
            parent_site_code = get_value(self.COLUMN_MAP.get('parent_site'), row)
            if parent_site_code:
                kwargs['parent_site'] = self._get_or_create_parent_site(parent_site_code)
            try:
                site, _ = Site.objects.update_or_create(code=code, project=self.project, defaults=kwargs)
            except Exception as e:
                error = str(e)
        return site, error

    def _get_attributes(self, row):
        """
        Everything not in the COLUMN_MAP is an attribute
        :return: a dict
        """
        attributes = {}
        non_attributes_keys = [k.lower() for sublist in self.COLUMN_MAP.values() for k in sublist]
        for k, v in row.items():
            if k.lower() not in non_attributes_keys:
                attributes[k] = v
        return attributes

    @staticmethod
    def _get_or_create_parent_site(parent_code):
        site, _ = Site.objects.get_or_create(code=parent_code)
        return site


class RecordsUploader:
    CSV_TYPES = [
        'text/csv',
        'text/comma-separated-values',
        'application/csv'
    ]
    XLSX_TYPES = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'application/vnd.msexcel',
    ]
    SUPPORTED_TYPES = CSV_TYPES + XLSX_TYPES

    def __init__(self, file, dataset):
        if file.content_type not in self.SUPPORTED_TYPES:
            msg = "Wrong file type {}. Should be one of: {}".format(file.content_type, self.SUPPORTED_TYPES)
            raise Exception(msg)

        self.file = file
        if file.content_type in self.XLSX_TYPES:
            self.file = xlsx_to_csv(file)
            self.reader = csv.DictReader(self.file)
        else:
            self.reader = csv.DictReader(codecs.iterdecode(self.file, 'utf-8'))
        self.dataset = dataset
        self.schema = dataset.schema
        self.record_model = dataset.record_model
        self.validator = get_record_validator_for_dataset(dataset)
        # if species. First load species list from herbie. Should raise an exception if problem.
        self.species_id_by_name = {}
        if dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
            self.species_id_by_name = HerbieFacade().name_id_by_species_name()

    def __iter__(self):
        for row in self.reader:
            yield self._add_record(row)

    def _add_record(self, row):
        """
        :param row:
        :return: record, RecordValidatorResult
        """
        validator_result = self.validator.validate(row, schema_error_as_warning=True)
        record = None
        if not validator_result.has_errors:
            site = self._get_or_create_site(row)
            record = self.record_model(
                site=site,
                dataset=self.dataset,
                data=row,
            )
            # specific fields
            if self.dataset.type == Dataset.TYPE_OBSERVATION or self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                observation_date = self.schema.cast_record_observation_date(row)
                # convert to datetime with timezone awareness
                if isinstance(observation_date, datetime.date):
                    observation_date = datetime.datetime.combine(observation_date, datetime.time.min)
                tz = self.dataset.project.timezone or timezone.get_current_timezone()
                record.datetime = timezone.make_aware(observation_date, tz)
                # geometry
                geometry = self.schema.cast_geometry(row, default_srid=MODEL_SRID)
                record.geometry = geometry
                if self.dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
                    # species stuff. Lookup for species match in herbie
                    species_name = self.schema.cast_species_name(row)
                    name_id = int(self.species_id_by_name.get(species_name, -1))
                    record.species_name = species_name
                    record.name_id = name_id
            record.save()
        return record, validator_result

    def close(self):
        self.file.close()

    def _get_or_create_site(self, row):
        return None
