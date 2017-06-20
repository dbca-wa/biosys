from main.constants import MODEL_SRID
from main.models import Dataset


def get_record_validator_for_dataset(dataset, **kwargs):
    if dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
        return SpeciesObservationValidator(dataset, **kwargs)
    elif dataset.type == Dataset.TYPE_OBSERVATION:
        return ObservationValidator(dataset, **kwargs)
    else:
        return GenericRecordValidator(dataset, **kwargs)


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class RecordValidatorResult:
    def __init__(self):
        self.warnings = {}
        self.errors = {}

    @property
    def has_errors(self):
        return bool(self.errors)

    @property
    def is_valid(self):
        return not self.has_errors

    def add_column_warning(self, column_id, message):
        self.warnings.update([(column_id, message)])

    def add_column_error(self, column_id, message):
        self.errors.update([(column_id, message)])

    def merge(self, other):
        if isinstance(other, RecordValidatorResult):
            result = RecordValidatorResult()
            result.warnings = merge_dicts(self.warnings, other.warnings)
            result.errors = merge_dicts(self.errors, other.errors)
            return result
        else:
            raise Exception("Can merge only a RecordValidatorResult")

    def to_dict(self):
        result = {
            'warnings': self.warnings,
            'errors': self.errors
        }
        return result


class GenericRecordValidator(object):
    def __init__(self, dataset, schema_error_as_warning=True, **kwargs):
        self.schema = dataset.schema
        self.schema_error_as_warning = schema_error_as_warning
        self.default_srid = dataset.project.datum or MODEL_SRID

    def validate(self, data):
        return self.validate_schema(data)

    def validate_schema(self, data):
        """
        :param data: must be a dictionary or a list of key => value
        :return: a RecordValidatorResult. To obtain the result as dict call the to_dict method of the result.
        """
        data = dict(data)
        result = RecordValidatorResult()
        for field_name, value in data.items():
            try:
                schema_error_msg = self.schema.field_validation_error(field_name, value)
            except Exception as e:
                schema_error_msg = str(e)
            if schema_error_msg:
                if self.schema_error_as_warning:
                    result.add_column_warning(field_name, schema_error_msg)
                else:
                    result.add_column_error(field_name, schema_error_msg)
        # check for missing required fields
        for field in self.schema.required_fields:
            if field.name not in data:
                msg = "The field '{}' is missing".format(field.name)
                if self.schema_error_as_warning:
                    result.add_column_warning(field.name, msg)
                else:
                    result.add_column_error(field.name, msg)
        return result


class ObservationValidator(GenericRecordValidator):
    def __init__(self, dataset, schema_error_as_warning=True, **kwargs):
        super(ObservationValidator, self).__init__(dataset, schema_error_as_warning, **kwargs)
        self.date_col = self.schema.observation_date_field.name if self.schema.observation_date_field else None
        self.lat_col = self.schema.latitude_field.name if self.schema.latitude_field else None
        self.lon_col = self.schema.longitude_field.name if self.schema.longitude_field else None
        self.site_col = self.schema.site_code_field.name if self.schema.site_code_field else None

    def validate(self, data):
        result = super(ObservationValidator, self).validate(data)
        # Every warnings on date or lat/long becomes error
        if self.date_col and self.date_col in result.warnings:
            result.add_column_error(self.date_col, result.warnings[self.date_col])
            del result.warnings[self.date_col]
        if self.lat_col and self.lat_col in result.warnings:
            result.add_column_error(self.lat_col, result.warnings[self.lat_col])
            del result.warnings[self.lat_col]
        if self.lon_col and self.lon_col in result.warnings:
            result.add_column_error(self.lon_col, result.warnings[self.lon_col])
            del result.warnings[self.lon_col]
        if self.site_col and self.site_col in result.warnings:
            result.add_column_error(self.site_col, result.warnings[self.site_col])
            del result.warnings[self.site_col]

        # validate the date and the geometry values. To be done only if there's no schema error
        if not result.has_errors:
            result = result.merge(self.validate_date(data))
            result = result.merge(self.validate_geometry(data))
        return result

    def validate_date(self, data):
        result = RecordValidatorResult()
        date_field = self.schema.observation_date_field
        try:
            self.schema.cast_record_observation_date(data)
        except Exception as e:
            msg = str(e)
            result.add_column_error(date_field.name, msg)
        return result

    def validate_geometry(self, data):
        result = RecordValidatorResult()
        try:
            self.schema.cast_geometry(data, default_srid=self.default_srid or MODEL_SRID)
        except Exception as e:
            msg = str(e)
            # the fields involved in the geometry error depends of the schema fields.
            # It could come from a site without geometry
            lat_field = self.schema.latitude_field
            long_field = self.schema.longitude_field
            site_code_field = self.schema.site_code_field
            if lat_field and long_field:
                result.add_column_error(lat_field.name, msg)
                result.add_column_error(long_field.name, msg)
            if site_code_field:
                result.add_column_error(site_code_field.name, msg)
        return result


class SpeciesObservationValidator(ObservationValidator):
    def __init__(self, dataset, schema_error_as_warning=True, **kwargs):
        super(SpeciesObservationValidator, self).__init__(dataset, schema_error_as_warning)
        self.species_name_col = self.schema.species_name_field.name if self.schema.species_name_field else None
        self.species_name_id_col = self.schema.species_name_id_field.name if self.schema.species_name_id_field else None
        self.species_mapping = kwargs.get('species_mapping')

    def validate(self, data, schema_error_as_warning=True):
        result = super(SpeciesObservationValidator, self).validate(data)
        if self.species_name_col and self.species_name_col in result.warnings:
            result.add_column_error(self.species_name_col, result.warnings[self.species_name_col])
            del result.warnings[self.species_name_col]
        if self.species_name_id_col and self.species_name_id_col in result.warnings:
            result.add_column_error(self.species_name_id_col, result.warnings[self.species_name_id_col])
            del result.warnings[self.species_name_id_col]

        # validate the species. To be done only if there's no schema error
        if not result.has_errors:
            result = result.merge(self.validate_species(data))
        return result

    def validate_species(self, data):
        result = RecordValidatorResult()
        name_id = self.schema.cast_species_name_id(data)
        if name_id and self.species_mapping is not None:
            if name_id not in self.species_mapping.values():
                message = "Cannot find a species with nameId={}".format(name_id)
                result.add_column_error(self.species_name_id_col, message)
        return result
