import pytest
from playwright.sync_api import Page

from core.factories import ContactStructureFactory, MessageFactory
from core.models import Message
from core.pages import UpdateMessagePage
from core.tests.generic_tests.messages import (
    generic_test_can_add_and_see_message_without_document,
    generic_test_can_only_see_own_document_types_in_message_form,
    generic_test_only_displays_app_contacts,
    generic_test_cant_see_drafts_from_other_users,
    generic_test_structure_show_only_one_entry_in_select,
    generic_test_can_add_and_see_message_in_new_tab_without_document,
    generic_test_can_add_and_see_note_in_new_tab_without_document,
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft,
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document,
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document,
    generic_test_can_add_message_in_new_tab_with_documents,
    generic_test_can_delete_my_own_message,
    generic_test_can_reply_to_message,
    generic_test_can_update_draft_note_in_new_tab,
    generic_test_can_update_draft_point_situation_in_new_tab,
    generic_test_can_send_draft_message_in_new_tab,
    generic_test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab,
    generic_test_can_delete_my_own_draft_message,
    generic_test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi,
    generic_test_can_search_in_message_list,
)
from ssa.factories import InvestigationCasHumainFactory
from ssa.models import EvenementInvestigationCasHumain


def test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_add_and_see_message_without_document(live_server, page, choice_js_fill, evenement_produit)


def test_can_add_and_see_message_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_add_and_see_message_in_new_tab_without_document(
        live_server, page, choice_js_fill, evenement_produit, mocked_authentification_user
    )


def test_can_add_in_new_tab_without_document_in_draft(live_server, page: Page, choice_js_fill):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft(
        live_server, page, choice_js_fill, evenement_produit
    )


def test_can_add_and_see_note_in_new_tab_without_document(live_server, page: Page):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_add_and_see_note_in_new_tab_without_document(live_server, page, evenement_produit)


def test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page: Page):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page, evenement_produit)


def test_can_add_and_see_demande_intervention_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document(
        live_server, page, choice_js_fill, evenement_produit, mocked_authentification_user
    )


def test_cant_see_drafts_from_other_users(live_server, page: Page):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_cant_see_drafts_from_other_users(live_server, page, evenement_produit)


def test_can_update_draft_note_in_new_tab(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_update_draft_note_in_new_tab(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_point_situation_in_new_tab(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation_in_new_tab(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_demande_intervention_in_new_tab(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation_in_new_tab(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_send_draft_message_in_new_tab(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_send_draft_message_in_new_tab(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_send_draft_compte_rendu(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
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
    message_page = UpdateMessagePage(page)
    message_page.open_message()
    message_page.submit_message()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert len(mailoutbox) == 1


def test_can_only_see_own_document_types_in_message_form(live_server, page: Page, check_select_options_from_element):
    generic_test_can_only_see_own_document_types_in_message_form(
        live_server,
        page,
        check_select_options_from_element,
        InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS),
    )


def test_can_see_and_delete_documents_from_draft_message_in_new_tab(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    generic_test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab(
        live_server,
        page,
        InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS),
        mocked_authentification_user,
        mailoutbox,
    )


def test_only_displays_ssa_contacts(live_server, page: Page, mocked_authentification_user):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_only_displays_app_contacts(live_server, page, evenement_produit, "ssa")


def test_structure_show_only_one_entry_in_select(live_server, page: Page):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_structure_show_only_one_entry_in_select(live_server, page, evenement_produit)


def test_can_add_message_in_new_tab_with_documents(live_server, page: Page, choice_js_fill, mailoutbox):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_add_message_in_new_tab_with_documents(
        live_server, page, choice_js_fill, evenement_produit, mailoutbox
    )


def test_can_delete_my_own_message(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_delete_my_own_message(
        live_server, page, evenement_produit, mocked_authentification_user, mailoutbox
    )


def test_can_delete_my_own_draft_message(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_delete_my_own_draft_message(
        live_server, page, evenement_produit, mocked_authentification_user, mailoutbox
    )


@pytest.mark.parametrize(
    "type_message", [Message.MESSAGE, Message.POINT_DE_SITUATION, Message.DEMANDE_INTERVENTION, Message.COMPTE_RENDU]
)
def test_can_reply_to_message(live_server, page: Page, choice_js_fill, type_message):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_reply_to_message(live_server, page, choice_js_fill, evenement_produit, type_message)


def test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi(live_server, page: Page, choice_js_get_values):
    evenement_produit = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi(
        live_server, page, choice_js_get_values, evenement_produit
    )


def test_can_search_in_message_list(live_server, page: Page):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_search_in_message_list(live_server, page, evenement)
