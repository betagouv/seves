from django.urls import path

from .views.produit import EvenementProduitDetailView, EvenementProduitCreateView, EvenementProduitListView

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
]
