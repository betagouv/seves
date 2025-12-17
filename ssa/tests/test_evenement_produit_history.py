from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from core.factories import DepartementFactory, MessageFactory
from core.models import LienLibre
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
    etablissement.numeros_resytal = "123456"
    etablissement.enseigne_usuelle = "New version"

    update_page.navigate_update_page(evenement)
    update_page.open_edit_etablissement(index=0)
    modal = update_page.current_modal
    modal.locator('[id$="raison_sociale"]').fill(etablissement.raison_sociale)
    modal.locator('[id$="enseigne_usuelle"]').fill(etablissement.enseigne_usuelle)
    modal.locator('[id$="-numeros_resytal"]').fill(etablissement.numeros_resytal)
    update_page.close_etablissement_modal()
    update_page.submit_as_draft()

    message = MessageFactory(content_object=evenement)
    message.is_deleted = True
    message.save()

    other_evenement = EvenementProduitFactory()
    lien = LienLibre.objects.create(related_object_1=other_evenement, related_object_2=evenement)
    lien.delete()

    content_type = ContentType.objects.get_for_model(EvenementProduit)
    url = reverse("revision-list", kwargs={"content_type": content_type.pk, "pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    expect(page.locator("tr")).to_have_count(
        len(
            [
                "One for table header",
                "One (fake) line for the creation of the object",
                "One line created by the change of description",
                "One line created when we add the Etablissement",
                "One line created by the addition of agent/structure contact during the update of the object",
                "One line created for each modification of the etablissement",
                "One line created for each modification of the etablissement",
                "One line created for each modification of the etablissement",
                "One for the deletion of the message",
                "One for creation of the LienLibre",
                "One for deletion of the LienLibre",
            ]
        )
    )

    expect(page.get_by_text(f"Le lien '{str(other_evenement)}' a été ajouté à la fiche", exact=True)).to_be_visible()
    expect(page.get_by_text(f"Le lien '{str(other_evenement)}' a été supprimé à la fiche", exact=True)).to_be_visible()
