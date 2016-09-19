

def set_site(record_data, dataset, site):
    """
    Update the 'Site' column value with the given site code
    :param record_data:
    :param dataset:
    :param site:
    :return:
    """
    schema = dataset.schema
    site_column = schema.get_fk_for_model('Site').data_field
    record_data[site_column] = site.code
    return record_data
