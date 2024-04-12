from django.urls import path
from .views import FicheDetectionListView, FicheDetectionDetailView, create_fiche_detection

urlpatterns = [
	path("fiches-detection/", FicheDetectionListView.as_view(), name="fiche-detection-list"),
	path("fiches-detection/<int:pk>/", FicheDetectionDetailView.as_view(), name="fiche-detection-vue-detaillee"),
	path("fiches-detection/creation/", create_fiche_detection, name="fiche-detection-creation"),
]