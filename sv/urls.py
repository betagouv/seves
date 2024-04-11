from django.urls import path
from .views import FicheDetectionListView

urlpatterns = [
	path("fiches-detection/", FicheDetectionListView.as_view(), name="fiche-detection-list"),
]