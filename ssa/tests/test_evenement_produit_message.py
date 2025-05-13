from playwright.sync_api import Page, expect

from core.constants import MUS_STRUCTURE
from core.factories import ContactStructureFactory
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitDetailsPage


def test_can_add_and_see_compte_rendu(live_server, page: Page, choice_js_fill):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    ContactStructureFactory(
        structure__niveau2=MUS_STRUCTURE, structure__niveau1=MUS_STRUCTURE, structure__libelle=MUS_STRUCTURE
    )

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.open_compte_rendu_di()
    expect(details_page.message_form_title).to_have_text("compte rendu sur demande d'intervention")
    details_page.add_limited_recipient_to_message(MUS_STRUCTURE, choice_js_fill)
    details_page.add_message_content_and_send()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    assert details_page.fil_de_suivi_sender == "Structure Test"
    assert details_page.fil_de_suivi_recipients == "MUS"
    assert details_page.fil_de_suivi_title == "Title of the message"
    assert details_page.fil_de_suivi_type == "Compte rendu sur demande d'intervention"
