def to_bool(s):
    if isinstance(s, str):
        return s.lower() in ('y', 'yes', 'true', 'on', '1')
    else:
        return bool(s)
