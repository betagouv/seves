from django.urls import path

from .views import EvenementAnimalCreationView, EvenementAnimalDetailsView, EvenementListView
from .views.api import FindFreeLinksView
from .views.evenement import CSVExportView

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
        "api/freelinks/recherche/",
        FindFreeLinksView.as_view(),
        name="find-free-link",
    ),
    path(
        "export/csv/",
        CSVExportView.as_view(),
        name="export-csv",
    ),
]
