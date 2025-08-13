from django.urls import path

from tiac import views

app_name = "tiac"
urlpatterns = [
    path(
        "evenements/",
        views.EvenementListView.as_view(),
        name="evenement-liste",
    ),
    path(
        "evenement-simple/creation",
        views.EvenementSimpleCreationView.as_view(),
        name="evenement-simple-creation",
    ),
    path(
        "evenement-simple/<str:numero>/",
        views.EvenementSimpleDetailView.as_view(),
        name="evenement-simple-details",
    ),
]
