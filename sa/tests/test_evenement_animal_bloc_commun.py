import pytest

from core.mixins import WithEtatMixin
from core.models import Message
from core.tests.generic_tests.bloc_commun import (
    generic_test_bloc_commun_nb_items,
    generic_test_can_preview_image_from_bloc_commun,
)
from core.tests.generic_tests.contacts import (
    generic_test_add_contact_agent_to_an_evenement,
    generic_test_add_contact_structure_to_an_evenement,
    generic_test_add_contact_structure_to_an_evenement_with_dedicated_email,
    generic_test_add_multiple_contacts_agents_to_an_evenement,
    generic_test_cant_add_contact_agent_if_he_cant_access_domain,
    generic_test_cant_add_contact_structure_if_any_agent_cant_access_domain,
    generic_test_remove_contact_agent_from_an_evenement,
    generic_test_remove_contact_structure_from_an_evenement,
)
from core.tests.generic_tests.documents import (
    generic_test_can_add_document_to_evenement,
    generic_test_can_download_zip_of_documents,
    generic_test_can_download_zip_of_documents_with_filter,
    generic_test_cant_download_zip_when_no_documents,
    generic_test_cant_see_document_type_from_other_app,
    generic_test_cant_see_document_type_from_other_app_when_editing_document,
    generic_test_document_modal_front_behavior,
    generic_test_document_modal_xss_mitigated,
)
from core.tests.generic_tests.messages import (
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document,
    generic_test_can_add_and_see_message_in_new_tab_without_document,
    generic_test_can_add_and_see_message_with_rich_text_editor,
    generic_test_can_add_and_see_message_without_document,
    generic_test_can_add_and_see_note_in_new_tab_with_specific_date,
    generic_test_can_add_and_see_note_in_new_tab_without_document,
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document,
    generic_test_can_add_message_in_new_tab_with_documents,
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft,
    generic_test_can_delete_my_own_draft_message,
    generic_test_can_delete_my_own_message,
    generic_test_can_download_zip_attachments_of_message,
    generic_test_can_only_see_own_document_types_in_message_form,
    generic_test_can_preview_image_from_message_details,
    generic_test_can_reply_to_message,
    generic_test_can_search_in_message_list,
    generic_test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab,
    generic_test_can_send_draft_message_in_new_tab,
    generic_test_can_send_draft_message_with_rich_text_editor,
    generic_test_can_update_draft_demande_intervention_in_new_tab,
    generic_test_can_update_draft_message_in_new_tab,
    generic_test_can_update_draft_note_in_new_tab,
    generic_test_can_update_draft_point_situation_in_new_tab,
    generic_test_cant_see_drafts_from_other_users,
    generic_test_cant_see_messages_in_internal_state,
    generic_test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi,
    generic_test_handle_document_validation_error,
    generic_test_message_ordering,
    generic_test_only_displays_app_contacts,
    generic_test_structure_show_only_one_entry_in_select,
)
from sa.tests.factories import EvenementAnimalFactory


def test_bloc_commun_nb_items(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    other_object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_bloc_commun_nb_items(live_server, page, object, other_object)


def test_can_preview_image_from_bloc_commun(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_preview_image_from_bloc_commun(live_server, page, object)


def test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, object, mailoutbox)


def test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, object, mailoutbox)


def test_add_contact_structure_to_an_evenement_with_dedicated_email(live_server, page, choice_js_fill, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_add_contact_structure_to_an_evenement_with_dedicated_email(
        live_server, page, choice_js_fill, object, mailoutbox, domain="sa"
    )


def test_remove_contact_agent_from_an_evenement(live_server, page, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_remove_contact_agent_from_an_evenement(live_server, page, object, mailoutbox)


def test_remove_contact_structure_from_an_evenement(live_server, page, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_remove_contact_structure_from_an_evenement(live_server, page, object, mailoutbox)


def test_add_multiple_contacts_agents_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_add_multiple_contacts_agents_to_an_evenement(live_server, page, object, choice_js_fill, mailoutbox)


def test_cant_add_contact_agent_if_he_cant_access_domain(live_server, page, choice_js_cant_pick):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_cant_add_contact_agent_if_he_cant_access_domain(live_server, page, choice_js_cant_pick, object)


def test_cant_add_contact_structure_if_any_agent_cant_access_domain(live_server, page, choice_js_cant_pick):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_cant_add_contact_structure_if_any_agent_cant_access_domain(
        live_server, page, choice_js_cant_pick, object
    )


def test_cant_see_document_type_from_other_app(live_server, page, check_select_options_from_element):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_cant_see_document_type_from_other_app(live_server, page, check_select_options_from_element, object)


def test_cant_see_document_type_from_other_app_when_editing_document(
    live_server,
    page,
    check_select_options_from_element,
):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_cant_see_document_type_from_other_app_when_editing_document(
        live_server, page, check_select_options_from_element, object
    )


def test_can_add_document_to_evenement(
    live_server,
    page,
    mocked_authentification_user,
):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_document_to_evenement(live_server, page, mocked_authentification_user, object)


def test_document_modal_xss_mitigated(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_document_modal_xss_mitigated(live_server, page, object)


def test_document_modal_front_behavior(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_document_modal_front_behavior(live_server, page, object)


def test_can_download_zip_of_documents(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_download_zip_of_documents(live_server, page, object)


def test_can_download_zip_of_documents_with_filter(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_download_zip_of_documents_with_filter(live_server, page, object)


def test_cant_download_zip_when_no_documents(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_cant_download_zip_when_no_documents(live_server, page, object)


def test_can_add_and_see_message_without_document(live_server, page, choice_js_fill):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_and_see_message_without_document(live_server, page, choice_js_fill, object)


def test_can_add_and_see_message_with_rich_text_editor(live_server, page, choice_js_fill):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_and_see_message_with_rich_text_editor(live_server, page, choice_js_fill, object)


def test_can_send_draft_message_with_rich_text_editor(live_server, page, mocked_authentification_user):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_send_draft_message_with_rich_text_editor(live_server, page, mocked_authentification_user, object)


def test_can_update_draft_message_in_new_tab(
    live_server, page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_update_draft_message_in_new_tab(
        live_server, page, choice_js_fill, mocked_authentification_user, object, mailoutbox
    )


def test_cant_see_drafts_from_other_users(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_cant_see_drafts_from_other_users(live_server, page, object)


def test_can_update_draft_note_in_new_tab(live_server, page, mocked_authentification_user, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_update_draft_note_in_new_tab(live_server, page, mocked_authentification_user, object, mailoutbox)


def test_can_update_draft_point_situation_in_new_tab(live_server, page, mocked_authentification_user, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_update_draft_point_situation_in_new_tab(
        live_server, page, mocked_authentification_user, object, mailoutbox
    )


def test_can_update_draft_demande_intervention_in_new_tab(
    live_server, page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_update_draft_demande_intervention_in_new_tab(
        live_server, page, choice_js_fill, mocked_authentification_user, object, mailoutbox
    )


def test_can_send_draft_message_in_new_tab(live_server, page, mocked_authentification_user, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_send_draft_message_in_new_tab(live_server, page, mocked_authentification_user, object, mailoutbox)


def test_can_only_see_own_document_types_in_message_form(live_server, page, check_select_options_from_element):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_only_see_own_document_types_in_message_form(
        live_server, page, check_select_options_from_element, object
    )


def test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab(
    live_server, page, mocked_authentification_user, mailoutbox
):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab(
        live_server, page, object, mocked_authentification_user, mailoutbox
    )


def test_handle_document_validation_error(live_server, page, choice_js_fill):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_handle_document_validation_error(live_server, page, choice_js_fill, object)


def test_only_displays_app_contacts(
    live_server,
    page,
):
    record = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_only_displays_app_contacts(live_server, page, record, app="sa")


def test_structure_show_only_one_entry_in_select(live_server, page, mocked_authentification_user):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_structure_show_only_one_entry_in_select(live_server, page, mocked_authentification_user, object)


def test_can_add_and_see_message_in_new_tab_without_document(
    live_server, page, choice_js_fill, mocked_authentification_user
):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_and_see_message_in_new_tab_without_document(
        live_server, page, choice_js_fill, object, mocked_authentification_user
    )


def test_can_add_see_message_in_new_tab_without_document_in_draft(live_server, page, choice_js_fill):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_see_message_in_new_tab_without_document_in_draft(live_server, page, choice_js_fill, object)


def test_can_add_and_see_note_in_new_tab_without_document(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_and_see_note_in_new_tab_without_document(live_server, page, object)


def test_can_add_and_see_note_in_new_tab_with_specific_date(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_and_see_note_in_new_tab_with_specific_date(live_server, page, object)


def test_can_add_and_see_demande_intervention_in_new_tab_without_document(
    live_server, page, choice_js_fill, mocked_authentification_user, mailoutbox
):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document(
        live_server, page, choice_js_fill, object, mocked_authentification_user, mailoutbox
    )


def test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page, object)


def test_can_add_message_in_new_tab_with_documents(live_server, page, choice_js_fill, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_add_message_in_new_tab_with_documents(live_server, page, choice_js_fill, object, mailoutbox)


def test_can_delete_my_own_message(live_server, page, mocked_authentification_user, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_delete_my_own_message(live_server, page, object, mocked_authentification_user, mailoutbox)


def test_can_delete_my_own_draft_message(live_server, page, mocked_authentification_user, mailoutbox):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_delete_my_own_draft_message(live_server, page, object, mocked_authentification_user, mailoutbox)


@pytest.mark.parametrize(
    "type_message", [Message.MESSAGE, Message.POINT_DE_SITUATION, Message.DEMANDE_INTERVENTION, Message.COMPTE_RENDU]
)
def test_can_reply_to_message(live_server, page, choice_js_fill, type_message):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_reply_to_message(live_server, page, choice_js_fill, object, type_message)


def test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi(live_server, page, choice_js_get_values):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi(
        live_server, page, choice_js_get_values, object
    )


def test_can_search_in_message_list(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_search_in_message_list(live_server, page, object)


def test_cant_see_messages_in_internal_state(live_server, page, mocked_authentification_user):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_cant_see_messages_in_internal_state(live_server, page, mocked_authentification_user, object)


def test_message_ordering(live_server, page, mocked_authentification_user):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_message_ordering(live_server, page, mocked_authentification_user, object)


def test_can_preview_image_from_message_details(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_preview_image_from_message_details(live_server, page, object)


def test_can_download_zip_attachments_of_message(live_server, page):
    object = EvenementAnimalFactory(etat=WithEtatMixin.Etat.EN_COURS)
    generic_test_can_download_zip_attachments_of_message(live_server, page, object)
