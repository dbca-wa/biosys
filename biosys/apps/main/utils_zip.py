from __future__ import unicode_literals
import logging
import os
import shutil
import tempfile

from django.http import HttpResponse


def export_zip(zip_path, name, delete_after=False):
    # Be sure that the name includes the extension .zip
    if not name.lower().endswith('.zip'):
        name += '.zip'
    response = HttpResponse(content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="{name}"'.format(name=name)
    with open(zip_path, 'rb') as zip_:
        response.write(zip_.read())
        response["Content-Length"] = response.tell()
    if delete_after:
        try:
            os.remove(zip_path)
        except Exception as e:
            logging.exception("Error when trying to delete the file {}".format(zip_path), e)
    return response


def zip_dir(dir_path, zip_out_path, delete_after=True):
    # shutil expect a path without the zip extension
    base_name, ext = os.path.splitext(zip_out_path)
    zip_file = shutil.make_archive(base_name, 'zip', dir_path)
    if delete_after:
        shutil.rmtree(dir_path)
    return zip_file


def zip_dir_to_temp_zip(dir_path, delete_after=True):
    fid, out_path = tempfile.mkstemp(suffix='.zip')
    return zip_dir(dir_path, out_path, delete_after=delete_after)
