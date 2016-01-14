import logging

from main.models import SiteVisit


logger = logging.getLogger(__name__)


def is_blank(value):
    return value is None or len(str(value).strip()) == 0


def get_sitevisit_from_datasheet(sv_file):
    """
    Parse the Meta worksheet and return the SiteVisit corresponding to the visit name/site code
    :return: The site visit for the file if it exists, or None
    """
    # don't put that at the top. It will create a circular import error
    from upload.validation import MetaData

    meta = MetaData.parse_file(sv_file)
    sites = SiteVisit.objects.filter(visit__name=meta.visit_name, site__site_code=meta.site_code)
    return sites.first()
