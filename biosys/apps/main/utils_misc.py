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
