from django.conf import settings


def standard(request):
    """Dictionary of context variables to pass with every request response.
    """
    context = {
        'page_title': settings.SITE_TITLE,
        'site_title': settings.SITE_TITLE,
        'application_version_no': settings.APPLICATION_VERSION_NO,
    }
    return context
