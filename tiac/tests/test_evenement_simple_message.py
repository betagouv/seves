from playwright.sync_api import Page
from waffle.testutils import override_flag

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
    generic_test_can_add_in_new_tab_without_document_in_draft,
)
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple


def test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_and_see_message_without_document(live_server, page, choice_js_fill, evenement_produit)


@override_flag("message_v2", active=True)
def test_can_add_and_see_message_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_and_see_message_in_new_tab_without_document(
        live_server, page, choice_js_fill, evenement_produit, mocked_authentification_user
    )


@override_flag("message_v2", active=True)
def test_can_add_and_see_message_in_new_tab_without_document_in_draft(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_add_in_new_tab_without_document_in_draft(
        live_server, page, choice_js_fill, evenement_produit, mocked_authentification_user
    )


def test_cant_see_drafts_from_other_users(live_server, page: Page):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_cant_see_drafts_from_other_users(live_server, page, evenement_produit)


def test_can_update_draft_note(live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_note(live_server, page, mocked_authentification_user, evenement_produit, mailoutbox)


def test_can_update_draft_point_situation(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_demande_intervention(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_demande_intervention(
        live_server, page, choice_js_fill, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_compte_rendu_demande_intervention(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_update_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_send_draft_message(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_send_draft_message(live_server, page, mocked_authentification_user, evenement_produit, mailoutbox)


def test_can_send_draft_point_de_situation(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_send_draft_point_de_situation(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_send_draft_demande_intervention(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_send_draft_demande_intervention(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_finaliser_draft_note(live_server, page: Page, mocked_authentification_user):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_finaliser_draft_note(live_server, page, mocked_authentification_user, evenement_produit)


def test_can_send_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_can_send_draft_fin_suivi(
        live_server, page, mocked_authentification_user, evenement_produit, mailoutbox
    )


def test_can_only_see_own_document_types_in_message_form(live_server, page: Page, check_select_options_from_element):
    generic_test_can_only_see_own_document_types_in_message_form(
        live_server,
        page,
        check_select_options_from_element,
        EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS),
    )


def test_can_see_and_delete_documents_from_draft_message(
    live_server, page: Page, mocked_authentification_user, mailoutbox
):
    generic_test_can_see_and_delete_documents_from_draft_message(
        live_server,
        page,
        EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS),
        mocked_authentification_user,
        mailoutbox,
    )


def test_only_displays_ssa_contacts(live_server, page: Page, mocked_authentification_user):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_only_displays_app_contacts(live_server, page, evenement_produit, "ssa")


def test_structure_show_only_one_entry_in_select(live_server, page: Page):
    evenement_produit = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_structure_show_only_one_entry_in_select(live_server, page, evenement_produit)
