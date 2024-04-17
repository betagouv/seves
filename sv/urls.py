from django.urls import path
from .views import FicheDetectionListView, FicheDetectionDetailView, CreateFicheDetectionView

urlpatterns = [
	path("fiches-detection/", FicheDetectionListView.as_view(), name="fiche-detection-list"),
	path("fiches-detection/<int:pk>/", FicheDetectionDetailView.as_view(), name="fiche-detection-vue-detaillee"),
	path("fiches-detection/creation/", CreateFicheDetectionView.as_view(), name="fiche-detection-creation"),
]