from playwright.sync_api import Page, expect
import pytest

from core.constants import MUS_STRUCTURE
from core.models import Message
from core.tests.generic_tests.messages import (
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document,
    generic_test_can_add_and_see_message_in_new_tab_without_document,
    generic_test_can_add_and_see_message_without_document,
    generic_test_can_add_and_see_note_in_new_tab_without_document,
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document,
    generic_test_can_add_message_in_new_tab_with_documents,
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft,
    generic_test_can_delete_my_own_draft_message,
    generic_test_can_delete_my_own_message,
    generic_test_can_only_see_own_document_types_in_message_form,
    generic_test_can_reply_to_message,
    generic_test_can_search_in_message_list,
    generic_test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab,
    generic_test_can_send_draft_message_in_new_tab,
    generic_test_can_update_draft_demande_intervention_in_new_tab,
    generic_test_can_update_draft_note_in_new_tab,
    generic_test_can_update_draft_point_situation_in_new_tab,
    generic_test_cant_see_drafts_from_other_users,
    generic_test_cant_see_messages_in_internal_state,
    generic_test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi,
    generic_test_handle_document_validation_error,
    generic_test_only_displays_app_contacts,
    generic_test_structure_show_only_one_entry_in_select,
)
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple
from tiac.tests.pages import EvenementSimpleDetailsPage


def test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_and_see_message_without_document(live_server, page, choice_js_fill, evenement_produit)


def test_can_add_and_see_message_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_and_see_message_in_new_tab_without_document(
        live_server, page, choice_js_fill, evenement_produit, mocked_authentification_user
    )


def test_can_add_and_see_message_in_new_tab_without_document_in_draft(live_server, page: Page, choice_js_fill):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft(
        live_server, page, choice_js_fill, evenement_produit
    )


def test_can_add_and_see_note_in_new_tab_without_document(live_server, page: Page):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_and_see_note_in_new_tab_without_document(live_server, page, evenement_produit)


def test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page: Page):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page, evenement_produit)


def test_can_add_and_see_demande_intervention_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document(
        live_server, page, choice_js_fill, evenement_produit, mocked_authentification_user
    )


def test_can_add_and_see_compte_rendu_in_new_tab(live_server, page: Page, choice_js_fill, mus_contact):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.page.get_by_test_id("element-actions").click()
    details_page.page.get_by_role("link", name="Compte rendu sur demande d'intervention").click()
    expect((page.get_by_text("Nouveau compte rendu sur demande d'intervention"))).to_be_visible()
    details_page.add_recipient_to_message(MUS_STRUCTURE, choice_js_fill)
    details_page.add_message_content_and_send()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    assert details_page.fil_de_suivi_sender == "Structure Test"
    assert details_page.fil_de_suivi_recipients == "MUS"
    assert details_page.fil_de_suivi_title == "Title of the message"
    assert details_page.fil_de_suivi_type == "Compte rendu sur demande d'intervention"


def test_cant_see_drafts_from_other_users(live_server, page: Page):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_see_drafts_from_other_users(live_server, page, evenement_produit)


def test_can_update_draft_note_in_new_tab(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_note_in_new_tab(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_point_situation_in_new_tab(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation_in_new_tab(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_demande_intervention_in_new_tab(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_demande_intervention_in_new_tab(
        live_server, page, choice_js_fill, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_send_draft_message_in_new_tab(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_send_draft_message_in_new_tab(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_only_see_own_document_types_in_message_form(live_server, page: Page, check_select_options_from_element):
    generic_test_can_only_see_own_document_types_in_message_form(
        live_server,
        page,
        check_select_options_from_element,
        EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS),
    )


def test_can_see_and_delete_documents_from_draft_message_in_new_tab(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    generic_test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab(
        live_server,
        page,
        EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS),
        mocked_authentification_user,
        mailoutbox,
    )


def test_handle_document_validation_error(live_server, page: Page, choice_js_fill, mocked_authentification_user):
    generic_test_handle_document_validation_error(
        live_server,
        page,
        choice_js_fill,
        EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS),
    )


def test_only_displays_ssa_contacts(live_server, page: Page, mocked_authentification_user):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_only_displays_app_contacts(live_server, page, evenement_produit, "ssa")


def test_structure_show_only_one_entry_in_select(live_server, page: Page):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_structure_show_only_one_entry_in_select(live_server, page, evenement_produit)


def test_can_add_message_in_new_tab_with_documents(live_server, page: Page, choice_js_fill, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_message_in_new_tab_with_documents(
        live_server, page, choice_js_fill, evenement_produit, mailoutbox
    )


def test_can_delete_my_own_message(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_delete_my_own_message(live_server, page, evenement, mocked_authentification_user, mailoutbox)


def test_can_delete_my_own_draft_message(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_delete_my_own_draft_message(live_server, page, evenement, mocked_authentification_user, mailoutbox)


@pytest.mark.parametrize(
    "type_message", [Message.MESSAGE, Message.POINT_DE_SITUATION, Message.DEMANDE_INTERVENTION, Message.COMPTE_RENDU]
)
def test_can_reply_to_message(live_server, page: Page, choice_js_fill, type_message):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_reply_to_message(live_server, page, choice_js_fill, evenement, type_message)


def test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi(live_server, page: Page, choice_js_get_values):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi(
        live_server, page, choice_js_get_values, evenement
    )


def test_can_search_in_message_list(live_server, page: Page):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_search_in_message_list(live_server, page, evenement)


def test_cant_see_messages_in_internal_state(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_see_messages_in_internal_state(live_server, page, mocked_authentification_user, evenement)
