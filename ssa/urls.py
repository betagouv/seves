from django.urls import path

from .views import (
    EvenementProduitDetailView,
    EvenementProduitCreateView,
    EvenementProduitListView,
    FindNumeroAgrementView,
    EvenementUpdateView,
)
from .views.produit import EvenementProduitExportView

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
        "evenement-produit/<int:pk>/modification",
        EvenementUpdateView.as_view(),
        name="evenement-produit-update",
    ),
    path(
        "evenement-produit/",
        EvenementProduitListView.as_view(),
        name="evenement-produit-liste",
    ),
    path(
        "export/evenement-produit/",
        EvenementProduitExportView.as_view(),
        name="export-evenement-produit",
    ),
    path(
        "api/find-numero-agrement/",
        FindNumeroAgrementView.as_view(),
        name="find-numero-agrement",
    ),
]
