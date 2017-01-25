class RecordValidatorResult:
    def __init__(self):
        self.warnings = []
        self.errors = []

    @staticmethod
    def _column_result(column_id, message):
        return {
            'column': column_id,
            'message': str(message) if message else ''
        }

    def add_column_warning(self, column_id, message):
        self.warnings.append(self._column_result(column_id, message))

    def add_column_error(self, column_id, message):
        self.errors.append(self._column_result(column_id, message))

    def merge(self, other):
        if isinstance(other, RecordValidatorResult):
            result = RecordValidatorResult()
            result.warnings = self.warnings + other.warnings
            result.errors = self.errors + other.errors
            return result
        else:
            raise Exception("Can merge only a RecordValidatorResult")

    def to_dict(self):
        result = {
            'warning': self.warnings,
            'errors': self.errors
        }
        return result


class GenericRecordValidator:
    def __init__(self, dataset):
        self.schema = dataset.schema

    def validate(self, data, schema_error_as_warning=True):
        return self.validate_schema(data, schema_error_as_warning=schema_error_as_warning)

    def validate_schema(self, data, schema_error_as_warning=True):
        """
        :param schema_error_as_warning: if True the schema error are reported as warnings not errors
        :param data: must be a dictionary or a list of key => value
        :return: a RecordValidatorResult. To obtain the result as dict call the to_dict method of the result.
        """
        # TODO: add constraint required validation
        data = dict(data)
        result = RecordValidatorResult()
        for field_name, value in data.items():
            try:
                schema_error_msg = self.schema.field_validation_error(field_name, value)
            except Exception as e:
                schema_error_msg = str(e)
            if schema_error_msg:
                if schema_error_as_warning:
                    result.add_column_warning(field_name, schema_error_msg)
                else:
                    result.add_column_error(field_name, schema_error_msg)
        return result


class ObservationValidator(GenericRecordValidator):
    def validate(self, data, schema_error_as_warning=True):
        result = super(ObservationValidator, self).validate(data, schema_error_as_warning=schema_error_as_warning)
        result = result.merge(self.validate_date(data))
        result = result.merge(self.validate_geometry(data))
        return result

    def validate_date(self, data, as_warning=False):
        # TODO: implement
        result = RecordValidatorResult()
        return result

    def validate_geometry(self, data):
        # TODO: implement
        result = RecordValidatorResult()
        return result


class SpeciesObservationValidator(ObservationValidator):
    def validate(self, data, schema_error_as_warning=True):
        result = super(SpeciesObservationValidator, self).validate(data,
                                                                   schema_error_as_warning=schema_error_as_warning)
        result = result.merge(self.validate_species(data))
        return result

    def validate_species(self, data):
        # TODO: implement
        result = RecordValidatorResult()
        return result
