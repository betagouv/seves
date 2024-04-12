from django.urls import path
from .views import FicheDetectionListView, FicheDetectionDetailView

urlpatterns = [
	path("fiches-detection/", FicheDetectionListView.as_view(), name="fiche-detection-list"),
	path("fiches-detection/<int:pk>/", FicheDetectionDetailView.as_view(), name="fiche-detection-vue-detaillee"),
]