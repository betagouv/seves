import os
from typing import Literal

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE, BSV_STRUCTURE
from core.factories import ContactAgentFactory, MessageFactory, ContactStructureFactory, DocumentFactory
from core.models import Message, FinSuiviContact, Contact
from core.pages import CreateMessagePage, UpdateMessagePage


def generic_test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill, object):
    active_contact = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)).agent

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.new_message()
    message_page.pick_recipient(active_contact, choice_js_fill)
    expect(message_page.message_form_title).to_have_text("message")

    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == str(active_contact)
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Message"
    message_page.open_message()

    expect(message_page.message_title_in_sidebar).to_be_visible()
    assert "My content <br> with a line return" in message_page.message_content_in_sidebar.inner_html()
    assert object.messages.get().status == Message.Status.FINALISE


def generic_test_can_update_draft_message(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, object, mailoutbox
):
    contact, contact_cc, contact_to_add, contact_cc_to_add = ContactAgentFactory.create_batch(
        4, with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)
    )
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.MESSAGE,
        recipients=[contact],
        recipients_copy=[contact_cc],
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.pick_recipient(contact_to_add.agent, choice_js_fill)
    page.keyboard.press("Escape")
    message_page.pick_recipient_copy(contact_cc_to_add.agent, choice_js_fill)
    message_page.message_title.fill("Titre mis à jour")
    message_page.message_content.fill("Contenu mis à jour")
    message_page.save_as_draft_message()

    message.refresh_from_db()
    assert message.message_type == Message.MESSAGE
    assert message.recipients.count() == 2
    assert message.recipients_copy.count() == 2
    assert set(message.recipients.all()) == {contact, contact_to_add}
    assert set(message.recipients_copy.all()) == {contact_cc, contact_cc_to_add}
    assert message.status == Message.Status.BROUILLON
    assert message.title == "Titre mis à jour"
    assert message.content == "Contenu mis à jour"
    assert len(mailoutbox) == 0


def generic_test_cant_see_drafts_from_other_users(live_server, page: Page, object):
    contact = ContactAgentFactory(with_active_agent=True)
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        message_type=Message.MESSAGE,
        recipients=[contact],
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    expect(message_page.page.get_by_text("Pas de message pour le moment", exact=True)).to_be_visible()


def generic_test_can_update_draft_note(live_server, page: Page, mocked_authentification_user, object, mailoutbox):
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.NOTE,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.message_title.fill("Titre mis à jour")
    message_page.message_content.fill("Contenu mis à jour")
    message_page.save_as_draft_message()

    message.refresh_from_db()
    assert message.message_type == Message.NOTE
    assert message.status == Message.Status.BROUILLON
    assert message.title == "Titre mis à jour"
    assert message.content == "Contenu mis à jour"
    assert len(mailoutbox) == 0


def generic_test_can_update_draft_point_situation(
    live_server, page: Page, mocked_authentification_user, object, mailoutbox
):
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.POINT_DE_SITUATION,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.message_title.fill("Titre mis à jour")
    message_page.message_content.fill("Contenu mis à jour")
    message_page.save_as_draft_message()

    message.refresh_from_db()
    assert message.message_type == Message.POINT_DE_SITUATION
    assert message.status == Message.Status.BROUILLON
    assert message.title == "Titre mis à jour"
    assert message.content == "Contenu mis à jour"
    assert len(mailoutbox) == 0


def generic_test_can_update_draft_demande_intervention(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, object, mailoutbox
):
    contact, contact_cc, contact_to_add, contact_cc_to_add = ContactStructureFactory.create_batch(
        4, with_one_active_agent=True
    )
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.DEMANDE_INTERVENTION,
        recipients=[contact],
        recipients_copy=[contact_cc],
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.pick_recipient_structure_only(contact_to_add.structure, choice_js_fill)
    page.keyboard.press("Escape")
    message_page.pick_recipient_copy_structure_only(contact_cc_to_add.structure, choice_js_fill)
    message_page.message_title.fill("Titre mis à jour")
    message_page.message_content.fill("Contenu mis à jour")
    message_page.save_as_draft_message()

    message.refresh_from_db()
    assert message.message_type == Message.DEMANDE_INTERVENTION
    assert message.recipients.count() == 2
    assert message.recipients_copy.count() == 2
    assert set(message.recipients.all()) == {contact, contact_to_add}
    assert set(message.recipients_copy.all()) == {contact_cc, contact_cc_to_add}
    assert message.status == Message.Status.BROUILLON
    assert message.title == "Titre mis à jour"
    assert message.content == "Contenu mis à jour"
    assert len(mailoutbox) == 0


def generic_test_can_update_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, object, mailoutbox):
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    object.contacts.add(contact)
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.FIN_SUIVI,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.message_title.fill("Titre mis à jour")
    message_page.message_content.fill("Contenu mis à jour")
    message_page.save_as_draft_message()

    message.refresh_from_db()
    assert message.message_type == Message.FIN_SUIVI
    assert message.status == Message.Status.BROUILLON
    assert message.title == "Titre mis à jour"
    assert message.content == "Contenu mis à jour"
    assert not FinSuiviContact.objects.filter(
        content_type=ContentType.objects.get_for_model(object), object_id=object.id, contact=contact
    ).exists()
    assert len(mailoutbox) == 0


def generic_test_can_send_draft_message(live_server, page: Page, mocked_authentification_user, object, mailoutbox):
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    object.contacts.add(contact)
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.MESSAGE,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.submit_message()

    # Wait for the page to confirm message was sent
    expect(page.locator(".fr-alert.fr-alert--success").get_by_text("Le message a bien été ajouté.")).to_be_visible()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert len(mailoutbox) == 1


def generic_test_can_send_draft_demande_intervention(
    live_server, page: Page, mocked_authentification_user, object, mailoutbox
):
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    object.contacts.add(contact)
    ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE,
        structure__niveau2=MUS_STRUCTURE,
        structure__libelle=MUS_STRUCTURE,
        with_one_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP),
    )
    ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE,
        structure__niveau2=BSV_STRUCTURE,
        structure__libelle=BSV_STRUCTURE,
        with_one_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP),
    )
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.DEMANDE_INTERVENTION,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.submit_message()

    # Wait for the page to confirm message was sent
    expect(page.locator(".fr-alert.fr-alert--success").get_by_text("Le message a bien été ajouté.")).to_be_visible()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert len(mailoutbox) == 1


def generic_test_can_send_draft_point_de_situation(
    live_server, page: Page, mocked_authentification_user, object, mailoutbox
):
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    object.contacts.add(contact)
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.POINT_DE_SITUATION,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.submit_message()

    # Wait for the page to confirm message was sent
    expect(page.locator(".fr-alert.fr-alert--success").get_by_text("Le message a bien été ajouté.")).to_be_visible()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert len(mailoutbox) == 1


def generic_test_can_finaliser_draft_note(live_server, page: Page, mocked_authentification_user, object):
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.NOTE,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.submit_message()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE


def generic_test_can_send_draft_fin_suivi(live_server, page: Page, mocked_authentification_user, object, mailoutbox):
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    agent_1 = ContactAgentFactory(agent__structure__niveau2=MUS_STRUCTURE)
    agent_2 = ContactAgentFactory(agent__structure__niveau2="FOO")
    structure_1 = ContactStructureFactory()
    object.contacts.set([agent_1, agent_2, structure_1, contact])
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.FIN_SUIVI,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    message_page.submit_message()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert FinSuiviContact.objects.filter(
        content_type=ContentType.objects.get_for_model(object), object_id=object.id, contact=contact
    ).exists()
    assert len(mailoutbox) == 1


def generic_test_can_only_see_own_document_types_in_message_form(
    live_server, page: Page, check_select_options_from_element, object
):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.new_message()

    expected = [settings.SELECT_EMPTY_CHOICE, *[t.label for t in object.get_allowed_document_types()]]
    check_select_options_from_element(message_page.document_type_input, expected, False)


def generic_test_can_see_and_delete_documents_from_draft_message(
    live_server, page, object, mocked_authentification_user, mailoutbox
):
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.MESSAGE,
    )
    document_to_remove = DocumentFactory(content_object=message)
    document_to_keep = DocumentFactory(content_object=message)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, message.id)
    message_page.open_message()
    assert len(message_page.get_existing_documents_title) == 2
    assert os.path.basename(document_to_remove.file.name) in message_page.get_existing_documents_title
    assert os.path.basename(document_to_keep.file.name) in message_page.get_existing_documents_title

    # Add new document
    message_page.add_document()
    assert len(message_page.get_existing_documents_title) == 3

    # Remove previous document
    message_page.remove_document(index=0)
    assert len(message_page.get_existing_documents_title) == 2

    message_page.submit_message()

    # Wait for the page to confirm message was sent
    expect(page.locator(".fr-alert.fr-alert--success").get_by_text("Le message a bien été ajouté.")).to_be_visible()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert message.documents.count() == 2
    assert document_to_keep in message.documents.all()
    assert document_to_remove not in message.documents.all()
    assert len(mailoutbox) == 1


def generic_test_only_displays_app_contacts(live_server, page: Page, record, app: Literal["sv", "ssa"]):
    ContactAgentFactory(with_active_agent__with_groups=[])
    ContactStructureFactory(with_one_active_agent__with_groups=[])
    sv_contacts = (
        ContactAgentFactory(with_active_agent__with_groups=[settings.SV_GROUP]),
        ContactStructureFactory(with_one_active_agent__with_groups=[settings.SV_GROUP]),
    )
    ssa_contacts = (
        ContactStructureFactory(with_one_active_agent__with_groups=[settings.SSA_GROUP]),
        ContactAgentFactory(with_active_agent__with_groups=[settings.SSA_GROUP]),
    )

    match app:
        case "sv":
            present = sv_contacts
            absent = ssa_contacts
        case "ssa":
            present = ssa_contacts
            absent = sv_contacts

    page.goto(f"{live_server.url}{record.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.new_message()

    dropdown_items = {item.inner_text() for item in message_page.recipents_dropdown_items.all()}

    # Assert all of the expected items are there
    assert {contact.display_with_agent_unit for contact in present} <= dropdown_items
    # Assert none of the unexpected items are there
    assert dropdown_items - {contact.display_with_agent_unit for contact in absent} == dropdown_items


def generic_test_structure_show_only_one_entry_in_select(live_server, page: Page, record):
    contact_structure = ContactStructureFactory()
    ContactAgentFactory(
        agent__structure=contact_structure.structure,
        with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP),
    )
    ContactAgentFactory(
        agent__structure=contact_structure.structure,
        with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP),
    )

    page.goto(f"{live_server.url}{record.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.new_message()

    dropdown_items = [item.inner_text() for item in message_page.recipents_dropdown_items.all()]
    assert len(dropdown_items) == 3


def generic_test_can_add_and_see_message_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, object, mocked_authentification_user
):
    active_contact = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)).agent

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_message()
    message_page.add_basic_message(active_contact, choice_js_fill)
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == str(active_contact)
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Message"

    with page.context.expect_page() as new_page_info:
        message_page.open_message()
    new_page = new_page_info.value

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    expect(new_page.get_by_text("My content with a line return")).to_be_visible()
    expect(
        new_page.get_by_text(
            f"De : {mocked_authentification_user.agent.contact_set.get().display_with_agent_unit}", exact=True
        )
    ).to_be_visible()
    expect(
        new_page.get_by_text(f"À : {active_contact.contact_set.get().display_with_agent_unit}", exact=True)
    ).to_be_visible()
    expect(new_page.get_by_text("Aucun document ajouté", exact=True)).to_be_visible()


def generic_test_can_add_see_message_in_new_tab_without_document_in_draft(
    live_server, page: Page, choice_js_fill, object
):
    active_contact = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)).agent

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_message()
    message_page.add_basic_message(active_contact, choice_js_fill)
    message_page.save_as_draft_message()
    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    message = Message.objects.get()
    assert message.is_draft
    assert message_page.message_type_in_table() == "Message [BROUILLON]"


def generic_test_can_add_and_see_note_in_new_tab_without_document(live_server, page: Page, object):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_note()
    expect((message_page.page.get_by_text("Nouvelle note"))).to_be_visible()

    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == ""
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Note"

    with page.context.expect_page() as new_page_info:
        message_page.open_message()
    new_page = new_page_info.value

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    expect(new_page.get_by_text("My content with a line return")).to_be_visible()
    expect(new_page.get_by_text("Aucun document ajouté", exact=True)).to_be_visible()


def generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, object, mocked_authentification_user
):
    contact, contact_cc = ContactStructureFactory.create_batch(
        2, with_one_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)
    )
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_demande_intervention()
    message_page.pick_recipient(contact.structure, choice_js_fill)
    page.keyboard.press("Escape")
    message_page.pick_recipient_copy(contact_cc.structure, choice_js_fill)
    message_page.save_as_draft_message()

    expect((message_page.page.get_by_text("Nouvelle demande d'intervention"))).to_be_visible()

    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == str(contact.structure)
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Demande d'intervention"

    with page.context.expect_page() as new_page_info:
        message_page.open_message()
    new_page = new_page_info.value

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    expect(new_page.get_by_text("My content with a line return")).to_be_visible()
    expect(new_page.get_by_text("Aucun document ajouté", exact=True)).to_be_visible()
    expect(
        new_page.get_by_text(
            f"De : {mocked_authentification_user.agent.contact_set.get().display_with_agent_unit}", exact=True
        )
    ).to_be_visible()
    expect(new_page.get_by_text(f"À : {contact.display_with_agent_unit}", exact=True)).to_be_visible()
    expect(new_page.get_by_text(f"CC : {contact_cc.display_with_agent_unit}", exact=True)).to_be_visible()


def generic_test_can_add_and_see_point_de_situation_in_new_tab_without_document(live_server, page: Page, object):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_point_de_situation()
    expect((message_page.page.get_by_text("Nouveau point de situation"))).to_be_visible()

    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == ""
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Point de situation"

    with page.context.expect_page() as new_page_info:
        message_page.open_message()
    new_page = new_page_info.value

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    expect(new_page.get_by_text("My content with a line return")).to_be_visible()
    expect(new_page.get_by_text("Aucun document ajouté", exact=True)).to_be_visible()


def generic_test_can_add_and_see_fin_de_suivi_in_new_tab_without_document_and_alter_status(
    live_server, page: Page, object, mocked_authentification_user
):
    user_contact_agent = Contact.objects.get(agent=mocked_authentification_user.agent)
    user_contact_structure = Contact.objects.get(structure=mocked_authentification_user.agent.structure)
    object.contacts.add(user_contact_agent)
    object.contacts.add(user_contact_structure)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_fin_de_suivi()
    expect((message_page.page.get_by_text("Signaler la fin de suivi"))).to_be_visible()

    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    expect(page.get_by_role("paragraph").filter(has_text="Fin de suivi")).to_be_visible()
    page.get_by_test_id("contacts").click()
    expect(page.get_by_test_id("contacts-structures").get_by_text("Fin de suivi")).to_be_visible()
    page.get_by_test_id("fil-de-suivi").click()

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == ""
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Fin de suivi"

    with page.context.expect_page() as new_page_info:
        message_page.open_message()
    new_page = new_page_info.value

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    expect(new_page.get_by_text("My content with a line return")).to_be_visible()
    expect(new_page.get_by_text("Aucun document ajouté", exact=True)).to_be_visible()
