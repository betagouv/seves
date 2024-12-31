from django.urls import path

from .api_views import search_espece_echantillon
from .views import (
    FicheListView,
    FicheDetectionCreateView,
    FicheDetectionUpdateView,
    FicheDetectionExportView,
    FicheCloturerView,
    EvenementVisibiliteUpdateView,
    FicheZoneDelimiteeCreateView,
    FicheZoneDelimiteeUpdateView,
    EvenementDetailView,
)

urlpatterns = [
    path(
        "fiches/",
        FicheListView.as_view(),
        name="fiche-liste",
    ),
    path(
        "evenement/<int:pk>/",
        EvenementDetailView.as_view(),
        name="evenement-details",
    ),
    path(
        "fiches-detection/creation/",
        FicheDetectionCreateView.as_view(),
        name="fiche-detection-creation",
    ),
    path(
        "fiches-detection/export/",
        FicheDetectionExportView.as_view(),
        name="fiche-detection-export",
    ),
    path(
        "fiches-detection/<int:pk>/modification/",
        FicheDetectionUpdateView.as_view(),
        name="fiche-detection-modification",
    ),
    path(
        "fiches/<int:pk>/cloturer/",
        FicheCloturerView.as_view(),
        name="fiche-cloturer",
    ),
    path(
        "evenement/<int:pk>/visibilite/",
        EvenementVisibiliteUpdateView.as_view(),
        name="evenement-visibilite-update",
    ),
    path(
        "api/espece/recherche/",
        search_espece_echantillon,
        name="api-search-espece",
    ),
    path(
        "fiche-zone-delimitee/creation/",
        FicheZoneDelimiteeCreateView.as_view(),
        name="fiche-zone-delimitee-creation",
    ),
    path(
        "fiche-zone-delimitee/<int:pk>/modification/",
        FicheZoneDelimiteeUpdateView.as_view(),
        name="fiche-zone-delimitee-update",
    ),
]
