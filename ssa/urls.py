from django.urls import path

from .views import (
    EvenementProduitDetailView,
    EvenementProduitCreateView,
    EvenementProduitListView,
    FindNumeroAgrementView,
)

app_name = "ssa"
urlpatterns = [
    path(
        "evenement-produit/creation",
        EvenementProduitCreateView.as_view(),
        name="evenement-produit-creation",
    ),
    path(
        "evenement-produit/<str:numero>/",
        EvenementProduitDetailView.as_view(),
        name="evenement-produit-details",
    ),
    path(
        "evenement-produit/",
        EvenementProduitListView.as_view(),
        name="evenement-produit-liste",
    ),
    path(
        "api/find-numero-agrement/",
        FindNumeroAgrementView.as_view(),
        name="find-numero-agrement",
    ),
]
