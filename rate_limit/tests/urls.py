from django.http import HttpResponse
from django.urls import include, path


def plain_view(request):
    return HttpResponse("ok")


group_patterns = ([path("a/", plain_view, name="a")], "excluded_group")

urlpatterns = [
    path("plain/", plain_view, name="plain"),
    path("named-exempt/", plain_view, name="named-exempt"),
    path("static/logo.png", plain_view, name="static-file"),
    path("group/", include(group_patterns)),
]
