from django.urls import path

from tiac.views import EvenementProduitListView

app_name = "tiac"
urlpatterns = [
    path(
        "evenement-produit/",
        EvenementProduitListView.as_view(),
        name="evenement-produit-liste",
    ),
]
