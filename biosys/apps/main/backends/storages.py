from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

"""
The next two classes are just to ensure that the static and media files
are saved in a different 'folder' in a S3 bucket

"""
class S3StaticStorage(S3Boto3Storage):
    location = settings.STATICFILES_LOCATION


class S3MediaStorage(S3Boto3Storage):
    location = settings.MEDIAFILES_LOCATION
