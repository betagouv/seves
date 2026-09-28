from django.urls import path

from .views import (
    EvenementAnimalCreationView,
    EvenementAnimalDetailsView,
    EvenementAnimalDocumentExportView,
    EvenementListView,
)
from .views.api import FindFreeLinksView

app_name = "sa"
urlpatterns = [
    path(
        "evenements/",
        EvenementListView.as_view(),
        name="evenement-liste",
    ),
    path(
        "evenement-animal/creation",
        EvenementAnimalCreationView.as_view(),
        name="evenement-animal-creation",
    ),
    path(
        "evenement-animal/<int:pk>/",
        EvenementAnimalDetailsView.as_view(),
        name="evenement-animal-details",
    ),
    path(
        "evenement-animal/<int:pk>/document/",
        EvenementAnimalDocumentExportView.as_view(),
        name="evenement-animal-export-document",
    ),
    path(
        "api/freelinks/recherche/",
        FindFreeLinksView.as_view(),
        name="find-free-link",
    ),
]
