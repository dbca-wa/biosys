from django.utils import six


def to_bool(s):
    if isinstance(s, six.string_types):
        return s.lower() in ('y', 'yes', 'true', 'on', '1')
    else:
        return bool(s)
