from playwright.sync_api import Page, expect
from waffle.testutils import override_flag

from core.constants import MUS_STRUCTURE
from core.factories import ContactStructureFactory
from core.tests.generic_tests.messages import (
    generic_test_can_add_and_see_message_without_document,
    generic_test_can_update_draft_note,
    generic_test_can_update_draft_point_situation,
    generic_test_can_finaliser_draft_note,
    generic_test_can_send_draft_fin_suivi,
    generic_test_can_only_see_own_document_types_in_message_form,
    generic_test_can_see_and_delete_documents_from_draft_message,
    generic_test_only_displays_app_contacts,
    generic_test_cant_see_drafts_from_other_users,
    generic_test_structure_show_only_one_entry_in_select,
    generic_test_can_update_draft_demande_intervention,
    generic_test_can_send_draft_message,
    generic_test_can_send_draft_demande_intervention,
    generic_test_can_send_draft_point_de_situation,
    generic_test_can_add_and_see_message_in_new_tab_without_document,
    generic_test_can_add_and_see_note_in_new_tab_without_document,
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft,
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document,
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document,
    generic_test_can_add_and_see_fin_de_suivi_in_new_tab_without_document_and_alter_status,
    generic_test_can_add_message_in_new_tab_with_documents,
    generic_test_can_delete_my_own_message,
)
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac
from tiac.tests.pages import InvestigationTiacDetailsPage


def test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_and_see_message_without_document(live_server, page, choice_js_fill, evenement)


@override_flag("message_v2", active=True)
def test_can_add_and_see_message_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_and_see_message_in_new_tab_without_document(
        live_server, page, choice_js_fill, evenement, mocked_authentification_user
    )


@override_flag("message_v2", active=True)
def test_can_add_in_new_tab_without_document_in_draft(live_server, page: Page, choice_js_fill):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft(live_server, page, choice_js_fill, evenement)


@override_flag("message_v2", active=True)
def test_can_add_and_see_note_in_new_tab_without_document(
    live_server,
    page: Page,
):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_and_see_note_in_new_tab_without_document(live_server, page, evenement)


@override_flag("message_v2", active=True)
def test_can_add_and_see_point_de_situation_in_new_tab_without_document(
    live_server,
    page: Page,
):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page, evenement)


@override_flag("message_v2", active=True)
def test_can_add_and_see_demande_intervention_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document(
        live_server, page, choice_js_fill, evenement, mocked_authentification_user
    )


@override_flag("message_v2", active=True)
def test_can_add_and_see_fin_de_suivi_in_new_tab_without_document_and_alter_status(
    live_server, page: Page, mocked_authentification_user
):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_and_see_fin_de_suivi_in_new_tab_without_document_and_alter_status(
        live_server, page, evenement, mocked_authentification_user
    )


@override_flag("message_v2", active=True)
def test_can_add_and_see_compte_rendu_in_new_tab(live_server, page: Page, choice_js_fill):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    ContactStructureFactory(
        structure__niveau2=MUS_STRUCTURE, structure__niveau1=MUS_STRUCTURE, structure__libelle=MUS_STRUCTURE
    )

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
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
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_cant_see_drafts_from_other_users(live_server, page, evenement)


def test_can_update_draft_note(live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_update_draft_note(live_server, page, mocked_authentification_user, evenement, mailoutbox)


def test_can_update_draft_point_situation(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement, mailoutbox
    )


def test_can_update_draft_demande_intervention(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_update_draft_demande_intervention(
        live_server, page, choice_js_fill, mocked_authentification_user, evenement, mailoutbox
    )


def test_can_update_draft_compte_rendu_demande_intervention(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement, mailoutbox
    )


def test_can_update_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement, mailoutbox
    )


def test_can_send_draft_message(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_send_draft_message(live_server, page, mocked_authentification_user, evenement, mailoutbox)


def test_can_send_draft_point_de_situation(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_send_draft_point_de_situation(
        live_server, page, mocked_authentification_user, evenement, mailoutbox
    )


def test_can_send_draft_demande_intervention(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_send_draft_demande_intervention(
        live_server, page, mocked_authentification_user, evenement, mailoutbox
    )


def test_can_finaliser_draft_note(live_server, page: Page, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_finaliser_draft_note(live_server, page, mocked_authentification_user, evenement)


def test_can_send_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_send_draft_fin_suivi(live_server, page, mocked_authentification_user, evenement, mailoutbox)


def test_can_only_see_own_document_types_in_message_form(live_server, page: Page, check_select_options_from_element):
    generic_test_can_only_see_own_document_types_in_message_form(
        live_server,
        page,
        check_select_options_from_element,
        InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS),
    )


def test_can_see_and_delete_documents_from_draft_message(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    generic_test_can_see_and_delete_documents_from_draft_message(
        live_server,
        page,
        InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS),
        mocked_authentification_user,
        mailoutbox,
    )


def test_only_displays_ssa_contacts(live_server, page: Page, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_only_displays_app_contacts(live_server, page, evenement, "ssa")


def test_structure_show_only_one_entry_in_select(live_server, page: Page):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_structure_show_only_one_entry_in_select(live_server, page, evenement)


@override_flag("message_v2", active=True)
def test_can_add_message_in_new_tab_with_documents(live_server, page: Page, choice_js_fill):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_add_message_in_new_tab_with_documents(live_server, page, choice_js_fill, evenement)


def test_can_delete_my_own_message(live_server, page: Page, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_delete_my_own_message(live_server, page, evenement, mocked_authentification_user)
