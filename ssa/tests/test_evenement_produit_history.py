from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from core.factories import DepartementFactory
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitFormPage


def test_can_view_evenement_produit_history(live_server, page):
    evenement = EvenementProduitFactory()
    evenement.description = "I changed"
    evenement.save()

    departement = DepartementFactory()
    etablissement = EtablissementFactory.build(departement=departement)

    update_page = EvenementProduitFormPage(page, live_server.url)
    update_page.navigate_update_page(evenement)
    update_page.add_etablissement_with_required_fields(etablissement)
    update_page.submit_as_draft()

    etablissement.raison_sociale = "New"
    update_page.navigate_update_page(evenement)
    update_page.edit_etablissement_with_new_values(index=0, wanted_values=etablissement)
    update_page.submit_as_draft()

    content_type = ContentType.objects.get_for_model(EvenementProduit)
    url = reverse("revision-list", kwargs={"content_type": content_type.pk, "pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")
    expect(page.locator("tr")).to_have_count(
        len(
            [
                "One for table header",
                "One line created by the post_generation hook for source field in the factory",
                "One line created by the change of description",
                "One line created when we add the Etablissement",
                "One line created by the addition of agent/structure contact during the update of the object",
                "One line created by the modification of the etablissement",
            ]
        )
    )
