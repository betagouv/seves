from django.urls import path

from .views import EvenementAnimalCreationView, EvenementAnimalDetailsView, EvenementListView

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
]
