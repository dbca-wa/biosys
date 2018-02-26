from django.db.models.expressions import RawSQL


def get_value(keys, dict_, default=None):
    """
    Given a list of keys, search in a dict for the first matching keys (case insensitive) and return the value
    Note: the search is case insensitive.
    :param keys: list of possible keys
    :param dict_:
    :param default:
    :return:
    """
    keys = [k.lower() for k in keys]
    # lower the dict keys
    d_low = dict((k.lower(), v) for k, v in dict_.items())
    for key in keys:
        if key in d_low:
            return d_low.get(key)
    return default


def search_json_field(qs, json_field_name, keys, search_param):
    """
    Search does not support searching within JSONField.
    :param qs: queryset
    :param json_field_name: json field with values within to search
    :param keys: list of keys in json field to search
    :param search_param: value to search
    :return: the queryset after search filters applied
    """
    where_clauses = []
    params = []
    for key in keys:
        where_clauses.append(json_field_name + '->>%s ILIKE %s')

        params += [key, '%' + search_param + '%']

    return qs.extra(where=['OR '.join(where_clauses)], params=params)


def search_json_fields(qs, field_info, search_param):
    """
    Search does not support searching within JSONField.
    :param qs: queryset
    :param field_info: dictionary with json_field_name as the key and each json_field's respective keys as the value
    :param search_param: value to search
    :return: the queryset after search filters applied
    """
    where_clauses = []
    params = []

    for json_field_name in field_info.keys():
        for key in field_info[json_field_name]:
            where_clauses.append(json_field_name + '->>%s ILIKE %s')

            params += [key, '%' + search_param + '%']

    return qs.extra(where=['OR '.join(where_clauses)], params=params)


def order_by_json_field(qs, json_field_name, keys, ordering_param):
    """
    Order by does not support ordering within JSONField.
    :param qs: queryset
    :param json_field_name: json field with values within to potentially order by
    :param keys: list of keys in json field to potentially order by
    :param ordering_param: field to order by, prefixed with '-' for descending order
    :return: the queryset after ordering is applied if order_by param is within the json field
    """
    for key in keys:
        if ordering_param == key or ordering_param == '-' + key:
            if ordering_param.startswith('-'):
                qs = qs.order_by(RawSQL(json_field_name + '->%s', (ordering_param[1:],)).desc())
            else:
                qs = qs.order_by(RawSQL(json_field_name + '->%s', (ordering_param,)))

    return qs
