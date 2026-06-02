from urllib.parse import urlparse

from django.urls import resolve


def to_match_viewname(viewname):
    """
    Matcher to use with Playwright's Page.wait_for_url method. This function is designed to be easier to use than
    url globbing.
    """
    return lambda url: resolve(urlparse(url).path).view_name == viewname
