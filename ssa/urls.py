from django.urls import path
from django.views.generic import RedirectView

from .views import (
    EvenementProduitCreateView,
    EvenementProduitDetailView,
    EvenementsListView,
    EvenementUpdateView,
    FindNumeroAgrementView,
    InvestigationCasHumainCreateView,
)
from .views.api import FindFreeLinksView
from .views.common import CsvExportView
from .views.investigation_cas_humain import (
    InvestigationCasHumainDetailView,
    InvestigationCasHumainDocumentExportView,
    InvestigationCasHumainUpdateView,
)
from .views.produit import (
    EvenementProduitDocumentExportView,
)

app_name = "ssa"
urlpatterns = [
    path(
        "evenement-produit/",
        RedirectView.as_view(pattern_name="ssa:evenements-liste", permanent=True),
        name="evenement-produit-liste",
    ),
    path(
        "evenements/",
        EvenementsListView.as_view(),
        name="evenements-liste",
    ),
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
        "export/evenements/",
        CsvExportView.as_view(),
        name="export-csv",
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
        "api/freelinks/recherche/",
        FindFreeLinksView.as_view(),
        name="find-free-link",
    ),
    path(
        "investigation-cas-humain/creation/",
        InvestigationCasHumainCreateView.as_view(),
        name="investigation-cas-humain-creation",
    ),
    path(
        "investigation-cas-humain/<int:pk>/modification/",
        InvestigationCasHumainUpdateView.as_view(),
        name="investigation-cas-humain-update",
    ),
    path(
        "investigation-cas-humain/<int:pk>/details/",
        InvestigationCasHumainDetailView.as_view(),
        name="investigation-cas-humain-details",
    ),
    path(
        "export/investigation-cas-humain/<int:pk>/document/",
        InvestigationCasHumainDocumentExportView.as_view(),
        name="export-investigation-cas-humain-document",
    ),
]
