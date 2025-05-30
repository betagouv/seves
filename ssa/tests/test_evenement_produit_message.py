import pytest
from playwright.sync_api import Page, expect

from core.constants import MUS_STRUCTURE
from core.factories import ContactStructureFactory, MessageFactory
from core.models import Message
from core.pages import UpdateMessagePage
from core.tests.generic_tests.messages import (
    generic_test_can_add_and_see_message_without_document,
    generic_test_can_update_draft_note,
    generic_test_can_update_draft_point_situation,
    generic_test_can_send_draft_element_suivi,
    generic_test_can_finaliser_draft_note,
    generic_test_can_send_draft_fin_suivi,
)
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


def test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_add_and_see_message_without_document(live_server, page, choice_js_fill, evenement_produit)


def test_can_update_draft_note(live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_update_draft_note(live_server, page, mocked_authentification_user, evenement_produit, mailoutbox)


def test_can_update_draft_point_situation(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_demande_intervention(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_compte_rendu_demande_intervention(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


@pytest.mark.parametrize(
    "message_type",
    [
        Message.MESSAGE,
        Message.POINT_DE_SITUATION,
        Message.DEMANDE_INTERVENTION,
    ],
)
def test_can_send_draft_element_suivi(live_server, page: Page, mocked_authentification_user, mailoutbox, message_type):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_send_draft_element_suivi(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox, message_type
    )


def test_can_send_draft_compte_rendu(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    evenement_produit.contacts.add(contact)
    message = MessageFactory(
        content_object=evenement_produit,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.COMPTE_RENDU,
    )
    message.recipients.set(
        [ContactStructureFactory(structure__libelle="BAMRA"), ContactStructureFactory(structure__libelle="BEPIAS")]
    )

    page.goto(f"{live_server.url}{evenement_produit.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.submit_message()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert len(mailoutbox) == 1


def test_can_finaliser_draft_note(live_server, page: Page, mocked_authentification_user):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_finaliser_draft_note(live_server, page, mocked_authentification_user, evenement_produit)


def test_can_send_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_send_draft_fin_suivi(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )
