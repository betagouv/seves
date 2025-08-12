from django.urls import path
from django.views.generic import RedirectView

from tiac import views

app_name = "tiac"
urlpatterns = [
    path(
        "evenements/",
        RedirectView.as_view(pattern_name="tiac:evenement-simple-creation", permanent=False),
        name="evenement-liste",
    ),
    path(
        "evenement-simple/",
        views.EvenementSimpleCreationView.as_view(),
        name="evenement-simple-creation",
    ),
    path(
        "evenement-simple/<str:numero>/",
        views.EvenementSimpleDetailView.as_view(),
        name="evenement-simple-details",
    ),
]
