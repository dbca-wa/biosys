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
        self.geometry_parser = self.schema.geometry_parser
        self.date_parser = self.schema.date_parser

    def validate(self, data):
        result = super(ObservationValidator, self).validate(data)
        # every schema validation warnings become errors if they concern geometry or date stuff.
        for field in self.geometry_parser.get_active_fields():
            if field.name in result.warnings:
                result.add_column_error(field.name, result.warnings[field.name])
                del result.warnings[field.name]

        for field in self.date_parser.get_active_fields():
            if field.name in result.warnings:
                result.add_column_error(field.name, result.warnings[field.name])
                del result.warnings[field.name]

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
            # the fields involved in the geometry can be many.
            # put the error on every field
            # TODO: extract the field from the error message
            for field in self.geometry_parser.get_active_fields():
                result.add_column_error(field.name, msg)
        return result


class SpeciesObservationValidator(ObservationValidator):
    def __init__(self, dataset, schema_error_as_warning=True, **kwargs):
        super(SpeciesObservationValidator, self).__init__(dataset, schema_error_as_warning)
        self.parser = self.schema.species_name_parser
        self.species_name_id_mapping = kwargs.get('species_name_id_mapping')

    def validate(self, data, schema_error_as_warning=True):
        result = super(SpeciesObservationValidator, self).validate(data)
        # every schema validation warnings become errors if they concern species stuff.
        for field in self.parser.get_active_fields():
            if field.name in result.warnings:
                result.add_column_error(field.name, result.warnings[field.name])
                del result.warnings[field.name]

        # validate the species. To be done only if there's no schema error
        if not result.has_errors:
            result = result.merge(self.validate_species(data))
        return result

    def validate_species(self, data):
        result = RecordValidatorResult()
        if self.parser.has_name_id:
            name_id = self.parser.cast_species_name_id(data)
            if name_id and self.species_name_id_mapping is not None:
                if name_id not in self.species_name_id_mapping.values():
                    message = "Cannot find a species with nameId={}".format(name_id)
                    result.add_column_error(self.parser.name_id_field.name, message)
        return result
