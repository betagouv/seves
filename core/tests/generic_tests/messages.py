from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE, BSV_STRUCTURE
from core.factories import ContactAgentFactory, MessageFactory, ContactStructureFactory
from core.models import Message, FinSuiviContact
from core.pages import CreateMessagePage, UpdateMessagePage


def generic_test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill, object):
    active_contact = ContactAgentFactory(with_active_agent=True).agent

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
    contact, contact_cc, contact_to_add, contact_cc_to_add = ContactAgentFactory.create_batch(4, with_active_agent=True)
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


def generic_test_can_send_draft_element_suivi(
    live_server, page: Page, mocked_authentification_user, object, mailoutbox, message_type
):
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    object.contacts.add(contact)
    ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE, structure__libelle=MUS_STRUCTURE
    )
    ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE, structure__niveau2=BSV_STRUCTURE, structure__libelle=BSV_STRUCTURE
    )
    message = MessageFactory(
        content_object=object,
        status=Message.Status.BROUILLON,
        sender=mocked_authentification_user.agent.contact_set.get(),
        message_type=message_type,
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
