from django.urls import path

from .api_views import search_espece_echantillon
from .views import (
    FicheDetectionListView,
    FicheDetectionDetailView,
    FicheDetectionCreateView,
    FicheDetectionUpdateView,
    FreeLinkCreateView,
    FicheDetectionExportView,
    FicheDetecionCloturerView,
    FicheDetectionVisibiliteUpdateView,
)

urlpatterns = [
    path(
        "fiches-detection/",
        FicheDetectionListView.as_view(),
        name="fiche-detection-list",
    ),
    path(
        "fiches-detection/<int:pk>/",
        FicheDetectionDetailView.as_view(),
        name="fiche-detection-vue-detaillee",
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
        "fiches-detection/<int:pk>/cloturer/",
        FicheDetecionCloturerView.as_view(),
        name="fiche-detection-cloturer",
    ),
    path(
        "fiches-detection/<int:pk>/visibilite/",
        FicheDetectionVisibiliteUpdateView.as_view(),
        name="fiche-detection-visibilite-update",
    ),
    path(
        "lien/ajout/",
        FreeLinkCreateView.as_view(),
        name="free-link-add",
    ),
    path(
        "api/espece/recherche/",
        search_espece_echantillon,
        name="api-search-espece",
    ),
]
