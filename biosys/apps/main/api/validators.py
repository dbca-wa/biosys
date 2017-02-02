from main.models import Dataset


def get_record_validator_for_dataset(dataset):
    if dataset.type == Dataset.TYPE_SPECIES_OBSERVATION:
        return SpeciesObservationValidator(dataset)
    elif dataset.type == Dataset.TYPE_OBSERVATION:
        return ObservationValidator(dataset)
    else:
        return GenericRecordValidator(dataset)


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
    def __init__(self, dataset, schema_error_as_warning=True):
        self.schema = dataset.schema
        self.schema_error_as_warning = schema_error_as_warning

    def validate(self, data):
        return self.validate_schema(data)

    def validate_schema(self, data):
        """
        :param schema_error_as_warning: if True the schema error are reported as warnings not errors
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
    def __init__(self, dataset, schema_error_as_warning=True):
        super(ObservationValidator, self).__init__(dataset, schema_error_as_warning)
        self.date_col = self.schema.observation_date_field.name
        self.lat_col = self.schema.latitude_field.name
        self.lon_col = self.schema.longitude_field.name

    def validate(self, data):
        result = super(ObservationValidator, self).validate(data)
        # Every warnings on date or lat/long becomes error
        if self.date_col in result.warnings:
            result.add_column_error(self.date_col, result.warnings[self.date_col])
            del result.warnings[self.date_col]
        if self.lat_col in result.warnings:
            result.add_column_error(self.lat_col, result.warnings[self.lat_col])
            del result.warnings[self.lat_col]
        if self.lon_col in result.warnings:
            result.add_column_error(self.lon_col, result.warnings[self.lon_col])
            del result.warnings[self.lon_col]
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
        lat_field = self.schema.latitude_field
        long_field = self.schema.longitude_field
        try:
            self.schema.cast_geometry(data)
        except Exception as e:
            msg = str(e)
            result.add_column_error(lat_field.name, msg)
            result.add_column_error(long_field.name, msg)
        return result


class SpeciesObservationValidator(ObservationValidator):
    def __init__(self, dataset, schema_error_as_warning=True):
        super(SpeciesObservationValidator, self).__init__(dataset, schema_error_as_warning)
        self.species_name_col = self.schema.species_name_field.name

    def validate(self, data, schema_error_as_warning=True):
        result = super(SpeciesObservationValidator, self).validate(data)
        if self.species_name_col in result.warnings:
            result.add_column_error(self.species_name_col, result.warnings[self.species_name_col])
            del result.warnings[self.species_name_col]
        if not result.has_errors:
            result = result.merge(self.validate_species(data))
        return result

    def validate_species(self, data):
        # TODO: Species validation!! ??
        result = RecordValidatorResult()
        return result
