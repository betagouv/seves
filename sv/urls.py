from django.urls import path
from .views import (
    FicheDetectionListView,
    FicheDetectionDetailView,
    FicheDetectionCreateView,
    FicheDetectionUpdateView,
    FicheZoneCreateView,
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
        "fiches-zone/creation/fiche-detection/<int:pk>/",
        FicheZoneCreateView.as_view(),
        name="fiche-zone-creation",
    ),
]
