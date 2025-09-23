from django.urls import path

from tiac import views

app_name = "tiac"
urlpatterns = [
    path(
        "evenements/",
        views.TiacListView.as_view(),
        name="evenement-liste",
    ),
    path(
        "evenement-simple/creation",
        views.EvenementSimpleCreationView.as_view(),
        name="evenement-simple-creation",
    ),
    path(
        "investigation-tiac/creation",
        views.InvestigationTiacCreationView.as_view(),
        name="investigation-tiac-creation",
    ),
    path(
        "evenement-simple/<str:numero>/",
        views.EvenementSimpleDetailView.as_view(),
        name="evenement-simple-details",
    ),
    path(
        "investigation-tiac/<str:numero>/",
        views.InvestigationTiacDetailView.as_view(),
        name="investigation-tiac-details",
    ),
    path(
        "evenement-simple/<int:pk>/transfer",
        views.EvenementSimpleTransferView.as_view(),
        name="evenement-simple-transfer",
    ),
]
