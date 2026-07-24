from django.urls import path

from .views import EvenementListView

app_name = "sa"
urlpatterns = [
    path(
        "evenements/",
        EvenementListView.as_view(),
        name="evenement-liste",
    ),
]
