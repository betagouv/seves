from django.urls import path

from .views import (
    EvenementProduitDetailView,
    EvenementProduitCreateView,
    EvenementProduitListView,
    FindNumeroAgrementView,
    EvenementUpdateView,
)
from .views.produit import (
    EvenementProduitExportView,
    EvenementProduitDocumentExportView,
    InvestigationCasHumainCreateView,
    InvestigationCasHumainUpdateView,
)

app_name = "ssa"
urlpatterns = [
    path(
        "evenement-produit/creation",
        EvenementProduitCreateView.as_view(),
        name="evenement-produit-creation",
    ),
    path(
        "evenement-produit/<int:pk>/",
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
        "export/evenement-produit/<int:pk>/document/",
        EvenementProduitDocumentExportView.as_view(),
        name="export-evenement-produit-document",
    ),
    path(
        "api/find-numero-agrement/",
        FindNumeroAgrementView.as_view(),
        name="find-numero-agrement",
    ),
    path(
        "investigation-cas-humain/creation",
        InvestigationCasHumainCreateView.as_view(),
        name="investigation-cas-humain-creation",
    ),
    path(
        "investigation-cas-humain/<int:pk>/modification",
        InvestigationCasHumainUpdateView.as_view(),
        name="investigation-cas-humain-update",
    ),
]
