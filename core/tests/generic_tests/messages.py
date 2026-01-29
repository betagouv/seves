from typing import Literal

from django.conf import settings
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import ContactAgentFactory, MessageFactory, ContactStructureFactory, DocumentFactory
from core.models import Message, FinSuiviContact, Structure, Contact
from core.pages import CreateMessagePage, UpdateMessagePage


def generic_test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill, object):
    active_contact = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)).agent

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.new_message()
    message_page.pick_recipient(active_contact, choice_js_fill)
    expect(message_page.message_form_title).to_have_text("Nouveau message")

    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")
    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    assert message_page.message_recipient_in_table() == str(active_contact)
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Message"

    new_page = message_page.open_message()

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    assert "My content <br> with a line return" in new_page.content()
    assert object.messages.get().status == Message.Status.FINALISE


def generic_test_can_update_draft_message_in_new_tab(
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
    message_page = UpdateMessagePage(page, "#message-form")
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
    MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        message_type=Message.MESSAGE,
        recipients=[contact],
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page)
    expect(message_page.page.get_by_text("Pas de message pour le moment", exact=True)).to_be_visible()


def generic_test_can_update_draft_note_in_new_tab(
    live_server, page: Page, mocked_authentification_user, object, mailoutbox
):
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.NOTE,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, container_id="#message-form")
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


def generic_test_can_update_draft_point_situation_in_new_tab(
    live_server, page: Page, mocked_authentification_user, object, mailoutbox
):
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.POINT_DE_SITUATION,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, "#message-form")
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


def generic_test_can_update_draft_demande_intervention_in_new_tab(
    live_server, page: Page, choice_js_fill, mocked_authentification_user, object, mailoutbox
):
    contact, contact_cc, contact_to_add, contact_cc_to_add = ContactStructureFactory.create_batch(
        4, with_one_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)
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
    message_page = UpdateMessagePage(page, "#message-form")
    message_page.open_message()

    message_page.pick_recipient(contact_to_add.structure, choice_js_fill)
    page.keyboard.press("Escape")
    message_page.pick_recipient_copy(contact_cc_to_add.structure, choice_js_fill)
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


def generic_test_can_send_draft_message_in_new_tab(
    live_server, page: Page, mocked_authentification_user, object, mailoutbox
):
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    object.contacts.add(contact)
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.MESSAGE,
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, "#message-form")
    message_page.open_message()

    message_page.submit_message()
    expect(page.get_by_text("Le message a bien été ajouté.")).to_be_visible()

    message.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert len(mailoutbox) == 1


def generic_test_can_only_see_own_document_types_in_message_form(
    live_server, page: Page, check_select_options_from_element, object
):
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.new_message()
    message_page.open_document_modal()

    expected = [settings.SELECT_EMPTY_CHOICE, *[t.label for t in object.get_allowed_document_types()]]
    check_select_options_from_element(message_page.global_document_type_input, expected, False)

    message_page.add_basic_document(close=False)
    check_select_options_from_element(message_page.document_type_input, expected, False)


def generic_test_can_see_delete_and_modify_documents_from_draft_message_in_new_tab(
    live_server, page, object, mocked_authentification_user, mailoutbox
):
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=Message.MESSAGE,
    )
    document_to_remove = DocumentFactory(content_object=message)
    document_to_remove_2 = DocumentFactory(content_object=message)
    document_to_keep = DocumentFactory(content_object=message)
    document_to_edit = DocumentFactory(content_object=message)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = UpdateMessagePage(page, "#message-form")
    message_page.open_message()

    assert len(message_page.get_existing_documents_title) == 4, (
        f"Expected 4 got {len(message_page.get_existing_documents_title)}"
    )
    assert document_to_remove.nom in ".".join(message_page.get_existing_documents_title)
    assert document_to_remove_2.nom in ".".join(message_page.get_existing_documents_title)
    assert document_to_keep.nom in message_page.get_existing_documents_title
    assert document_to_edit.nom in message_page.get_existing_documents_title

    # Add new document
    message_page.add_basic_document()
    assert len(message_page.get_existing_documents_title) == 5

    # Remove previous document from the document aside
    required_fields = (
        page.get_by_test_id("document-upload").filter(has_text=document_to_remove.nom).locator("[required]")
    )
    expect(required_fields).not_to_have_count(0)
    message_page.remove_document_by_name_from_aside(document_to_remove.nom)
    # Asserts that removed document won't be checked during form submission
    expect(required_fields).to_have_count(0)
    assert len(message_page.get_existing_documents_title) == 4

    # Remove previous document from the document modal
    required_fields = (
        page.get_by_test_id("document-upload").filter(has_text=document_to_remove_2.nom).locator("[required]")
    )
    expect(required_fields).not_to_have_count(0)
    message_page.remove_document_by_name_from_modal(document_to_remove_2.nom)
    # Asserts that removed document won't be checked during form submission
    expect(required_fields).to_have_count(0)
    assert len(message_page.get_existing_documents_title) == 3

    # Test that adding document without validating doesn't add document
    message_page.add_basic_document(close=False)
    message_page.close_document_modal_no_validate()
    assert len(message_page.get_existing_documents_title) == 3

    # Edit document
    with message_page.modify_document_by_name(document_to_edit.nom) as accordion:
        accordion.locator('[name$="nom"]').fill(f"New {document_to_edit.nom}")
    expect(page.get_by_test_id("document-card").filter(has_text=f"New {document_to_edit.nom}")).to_have_count(1)
    message_page.submit_message()

    # Wait for the page to confirm message was sent
    expect(page.locator(".fr-alert.fr-alert--success").get_by_text("Le message a bien été ajouté.")).to_be_visible()

    message.refresh_from_db()
    document_to_edit_nom_old = document_to_edit.nom
    document_to_edit.refresh_from_db()
    assert message.status == Message.Status.FINALISE
    assert message.documents.count() == 3, f"Expected 3 documents found {message.documents.count()}"
    assert document_to_keep in message.documents.all()
    assert document_to_remove not in message.documents.all()
    assert document_to_remove_2 not in message.documents.all()
    assert document_to_edit.nom == f"New {document_to_edit_nom_old}"
    assert len(mailoutbox) == 1


def generic_test_handle_document_validation_error(live_server, page: Page, choice_js_fill, object):
    active_contact = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)).agent

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.new_message()
    message_page.pick_recipient(active_contact, choice_js_fill)
    expect(message_page.message_form_title).to_have_text("Nouveau message")
    message_page.message_title.fill("Title of the message")
    message_page.message_content.fill("My content \n with a line return")

    message_page.add_basic_document(close=False)
    message_page.document_type_input.select_option("Choisir dans la liste")
    message_page.validate_document_modal()

    message_page.save_as_draft_message()

    expect(message_page.document_type_input).to_be_visible()
    assert (
        message_page.document_type_input.evaluate("el => el.validationMessage") == "Please select an item in the list."
    )


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
    Contact.objects.filter(email="service_account@seves.com").delete()
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
    assert len(dropdown_items) == 3, f"Got {len(dropdown_items)} items"


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

    new_page = message_page.open_message()

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

    new_page = message_page.open_message()

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    expect(new_page.get_by_text("My content with a line return")).to_be_visible()
    expect(new_page.get_by_text("Aucun document ajouté", exact=True)).to_be_visible()


def generic_test_can_add_and_see_demande_intervention_in_new_tab_without_document(
    live_server, page: Page, choice_js_fill, object, mocked_authentification_user
):
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    ContactStructureFactory(structure=structure)
    agent = mocked_authentification_user.agent
    agent.structure = structure
    agent.save()
    groups = (settings.SSA_GROUP, settings.SV_GROUP)
    contact = ContactStructureFactory(structure__libelle="Foo", with_one_active_agent__with_groups=groups)
    contact_cc = ContactStructureFactory(structure__libelle="Bar", with_one_active_agent__with_groups=groups)
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

    assert message_page.message_sender_in_table() == "MUS"
    assert message_page.message_recipient_in_table() == str(contact.structure)
    assert message_page.message_title_in_table() == "Title of the message"
    assert message_page.message_type_in_table() == "Demande d'intervention"

    new_page = message_page.open_message()

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

    new_page = message_page.open_message()

    expect(new_page.get_by_text("Title of the message", exact=True)).to_be_visible()
    expect(new_page.get_by_text("My content with a line return")).to_be_visible()
    expect(new_page.get_by_text("Aucun document ajouté", exact=True)).to_be_visible()


def generic_test_can_add_message_in_new_tab_with_documents(live_server, page: Page, choice_js_fill, object, mailoutbox):
    active_contact = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)).agent

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_message()
    message_page.add_basic_message(active_contact, choice_js_fill)
    message_page.add_basic_document()
    assert len(message_page.get_existing_documents_title) == 1

    message_page.add_basic_document(suffix=" numero 2")
    message_page.add_basic_document(suffix=" numero 3")
    assert len(message_page.get_existing_documents_title) == 3

    message_page.remove_document_by_name_from_aside("Mon document numero 2")
    assert len(message_page.get_existing_documents_title) == 2

    message_page.submit_message()

    page.wait_for_url(f"**{object.get_absolute_url()}#tabpanel-messages-panel")

    assert message_page.message_sender_in_table() == "Structure Test"
    message = Message.objects.get()
    assert message.documents.count() == 2
    assert {d.nom for d in message.documents.all()} == {"Mon document", "Mon document numero 3"}

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "Documents déposés sur Sèves en pièce jointe de ce message" in mail.body
    assert "Mon document numero 3 (Autre document)" in mail.body
    assert "Mon document (Autre document)" in mail.body


def generic_test_can_delete_my_own_message(live_server, page: Page, object, mocked_authentification_user, mailoutbox):
    assert Message.objects.count() == 0
    assert Message._base_manager.count() == 0

    message = MessageFactory(
        content_object=object, title="Mon titre", sender=mocked_authentification_user.agent.contact_set.get()
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)

    assert message_page.message_title_in_table() == message.title

    message_page.delete_message()
    assert Message.objects.count() == 0
    assert Message._base_manager.count() == 1

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "Suppression d’un élément du fil de suivi" in mail.subject
    assert "a été supprimé." in mail.body


def generic_test_can_delete_my_own_draft_message(
    live_server, page: Page, object, mocked_authentification_user, mailoutbox
):
    assert Message.objects.count() == 0
    assert Message._base_manager.count() == 0

    message = MessageFactory(
        content_object=object,
        sender=mocked_authentification_user.agent.contact_set.get(),
        status=Message.Status.BROUILLON,
        title="Short title",
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)

    assert message_page.message_title_in_table() == f"[BROUILLON] {message.title}"

    message_page.delete_message()
    assert Message.objects.count() == 0
    assert Message._base_manager.count() == 1

    assert len(mailoutbox) == 0


def generic_test_can_reply_to_message(live_server, page: Page, choice_js_fill, object, type_message):
    contact = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP))
    sender = ContactAgentFactory(with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP))
    message = MessageFactory(content_object=object, message_type=type_message, sender=sender)
    contact_sender_structure = ContactStructureFactory(structure=message.sender_structure)

    page.goto(f"{live_server.url}{message.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.page.get_by_text("Répondre", exact=True).click()

    assert message_page.message_title.input_value() == f"{settings.REPLY_PREFIX} {message.title}"
    assert message_page.message_content.input_value() == message.get_reply_intro_text()

    message_page.message_content.fill("Ma réponse")
    message_page.pick_recipient_copy(contact.agent, choice_js_fill)
    message_page.submit_message()

    assert Message.objects.count() == 2
    reply = Message.objects.first()

    expected_title = f"{settings.REPLY_PREFIX} {message.title}"
    expected_content = "Ma réponse"
    expected_recipients = [contact_sender_structure]
    expected_copies = [contact]

    assert reply.title == expected_title, f"{reply.title=!r} != {expected_title=!r}"
    assert reply.content == expected_content, f"{reply.content=!r} != {expected_content=!r}"
    assert list(reply.recipients.all()) == expected_recipients, (
        f"{list(reply.recipients.all())=!r} != {expected_recipients=!r}"
    )
    assert list(reply.recipients_copy.all()) == expected_copies, (
        f"{list(reply.recipients_copy.all())=!r} != {expected_copies=!r}"
    )


def generic_test_contact_shorcut_excludes_agent_and_structures_in_fin_suivi(
    live_server, page: Page, choice_js_get_values, object
):
    contact_structure = ContactStructureFactory()
    contact_agent = ContactAgentFactory(
        agent__structure=contact_structure.structure,
        with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP),
    )
    other_contact_structure = ContactStructureFactory()
    other_contact_agent = ContactAgentFactory(
        agent__structure=other_contact_structure.structure,
        with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP),
    )
    object.contacts.add(contact_structure, contact_agent, other_contact_structure, other_contact_agent)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page, container_id="#message-form")
    message_page.new_message()
    message_page.page.wait_for_url("**/message-add/**")

    message_page.page.locator(".destinataires-contacts-shortcut").click()
    expected = {
        contact_agent.display_with_agent_unit,
        contact_structure.display_with_agent_unit,
        other_contact_structure.display_with_agent_unit,
        other_contact_agent.display_with_agent_unit,
    }
    locator = "#id_recipients"
    assert set(choice_js_get_values(page, locator, delete_remove_link=True)) == expected, (
        f"Got {set(choice_js_get_values(page, locator, delete_remove_link=True))}"
    )

    FinSuiviContact.objects.create(
        content_object=object,
        contact=contact_structure,
    )

    message_page.page.reload()
    message_page.page.locator(".destinataires-contacts-shortcut").click()
    expected = {
        other_contact_structure.display_with_agent_unit,
        other_contact_agent.display_with_agent_unit,
    }
    assert set(choice_js_get_values(page, locator, delete_remove_link=True)) == expected, (
        f"Got {set(choice_js_get_values(page, locator, delete_remove_link=True))}"
    )


def generic_test_can_search_in_message_list(live_server, page: Page, object):
    params = {"content_object": object, "message_type": Message.MESSAGE}

    agent_prenom = ContactAgentFactory(agent__prenom="Ma phrase")
    agent_nom = ContactAgentFactory(agent__prenom="Ma phrase")
    structure = ContactStructureFactory(structure__libelle="Ma phrase")

    expected_messages = [
        MessageFactory(title="Ma phrase", **params),
        MessageFactory(content="Ma phrase", **params),
        MessageFactory(sender__agent__prenom="Ma phrase", **params),
        MessageFactory(sender__agent__nom="Ma phrase", **params),
        MessageFactory(sender__agent__structure__libelle="Ma phrase", **params),
        MessageFactory(recipients=[agent_prenom], **params),
        MessageFactory(recipients=[agent_nom], **params),
        MessageFactory(recipients=[structure], **params),
        MessageFactory(recipients_copy=[agent_prenom], **params),
        MessageFactory(recipients_copy=[agent_nom], **params),
        MessageFactory(recipients_copy=[structure], **params),
    ]

    not_expected_1 = MessageFactory(**params)
    not_expected_2 = MessageFactory(**params)
    not_expected_3 = MessageFactory(**params)

    message = MessageFactory(**params)
    DocumentFactory(nom="Ma phrase", description="", content_object=message, is_infected=False)
    expected_messages.append(message)

    message = MessageFactory(**params)
    DocumentFactory(description="Ma phrase", content_object=message, is_infected=False)
    expected_messages.append(message)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    message_page = CreateMessagePage(page)
    message_page.search_in_message_list("Ma phrase")

    expect(message_page.page.locator("#tabpanel-messages-panel").get_by_text("13 messages trouvés")).to_be_visible()

    for message in expected_messages:
        expect(
            message_page.page.locator("#tabpanel-messages-panel .fr-cell--multiline").get_by_text(message.title[:25])
        ).to_be_visible()

    expect(
        message_page.page.locator("#tabpanel-messages-panel .fr-cell--multiline").get_by_text(not_expected_1.title[:25])
    ).not_to_be_visible()
    expect(
        message_page.page.locator("#tabpanel-messages-panel .fr-cell--multiline").get_by_text(not_expected_2.title[:25])
    ).not_to_be_visible()
    expect(
        message_page.page.locator("#tabpanel-messages-panel .fr-cell--multiline").get_by_text(not_expected_3.title[:25])
    ).not_to_be_visible()

    message_page.page.locator("#tabpanel-messages-panel").get_by_text("Effacer la recherche").click()
    expect(
        message_page.page.locator("#tabpanel-messages-panel .cell-link").get_by_text("Message", exact=True)
    ).to_have_count(16)
