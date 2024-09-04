from django.urls import path
from .views import (
    FicheDetectionListView,
    FicheDetectionDetailView,
    FicheDetectionCreateView,
    FicheDetectionUpdateView,
    FreeLinkCreateView,
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
        "fiches-detection/<int:pk>/modification/",
        FicheDetectionUpdateView.as_view(),
        name="fiche-detection-modification",
    ),
    path(
        "lien/ajout/",
        FreeLinkCreateView.as_view(),
        name="free-link-add",
    ),
]
