from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def safe_redirect(url):
    if not url_has_allowed_host_and_scheme(url, allowed_hosts=settings.ALLOWED_HOSTS):
        url = reverse("index")
    return HttpResponseRedirect(url)
