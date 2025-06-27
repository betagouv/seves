import re

import pytest
from django.utils import html
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE, BSV_STRUCTURE
from core.factories import ContactAgentFactory, ContactStructureFactory, MessageFactory
from core.models import Message
from core.notifications import notify_message
from sv.factories import EvenementFactory


def create_message_and_notify(
    *, message_type, object, content="My message \n Thanks", recipients=None, recipients_copy=None
):
    message = MessageFactory(
        title="TITLE",
        content=content,
        sender=ContactAgentFactory(),
        message_type=message_type,
        content_object=object,
    )
    if recipients:
        message.recipients.set(recipients)
    if recipients_copy:
        message.recipients_copy.set(recipients_copy)
    notify_message(message)
    return message


def assert_mail_common(mails, message, evenement):
    assert len(mails) == 1
    mail = mails[0]
    message_type = message.get_email_type_display()
    assert mail.subject == f"[Sèves] {evenement.organisme_nuisible.code_oepp} {evenement.numero} - {message_type}"
    assert mail.from_email == "no-reply@beta.gouv.fr"
    assert message.sender.agent.prenom in mail.body
    assert message.sender.agent.nom in mail.body
    assert str(message.sender.agent.structure) in mail.body
    assert evenement.get_absolute_url() in mail.body
    return mail


@pytest.mark.django_db
def test_notification_message(mailoutbox):
    evenement = EvenementFactory()
    contact_1, contact_4, _contact_6 = ContactAgentFactory.create_batch(3)
    contact_2, contact_3, _contact_5 = ContactStructureFactory.create_batch(3)

    message = create_message_and_notify(
        message_type=Message.MESSAGE,
        object=evenement,
        recipients=[contact_1, contact_2],
        recipients_copy=[contact_3, contact_4],
    )

    mail = assert_mail_common(mailoutbox, message, evenement)
    assert message.content in mail.body
    assert set(mail.to) == {contact_1.email, contact_2.email}
    assert set(mail.cc) == {contact_3.email, contact_4.email}


@pytest.mark.django_db
def test_notification_demande_intervention(mailoutbox):
    evenement = EvenementFactory()
    agent_1, agent_2, _agent_3 = ContactAgentFactory.create_batch(3)
    structure_1, structure_2, _structure_3 = ContactStructureFactory.create_batch(3)

    message = create_message_and_notify(
        message_type=Message.DEMANDE_INTERVENTION,
        object=evenement,
        recipients=[agent_1, structure_1],
        recipients_copy=[agent_2, structure_2],
    )

    mail = assert_mail_common(
        mailoutbox,
        message,
        evenement,
    )
    assert message.content in mail.body
    assert set(mail.to) == {structure_1.email}
    assert set(mail.cc) == {structure_2.email}


@pytest.mark.django_db
def test_notification_point_de_situation(mailoutbox):
    evenement = EvenementFactory()
    agent_1, _agent_2 = ContactAgentFactory.create_batch(2)
    structure_1, _structure_2 = ContactStructureFactory.create_batch(2)

    message = create_message_and_notify(
        message_type=Message.POINT_DE_SITUATION, object=evenement, recipients=[agent_1, structure_1]
    )

    mail = assert_mail_common(mailoutbox, message, evenement)
    assert message.content in mail.body
    assert set(mail.to) == {agent_1.email, structure_1.email}
    assert set(mail.cc) == set()


@pytest.mark.django_db
def test_notification_fin_de_suivi(mailoutbox):
    evenement = EvenementFactory()
    agent_1 = ContactAgentFactory(agent__structure__niveau2=MUS_STRUCTURE)
    agent_2 = ContactAgentFactory(agent__structure__niveau2="FOO")
    structure_1 = ContactStructureFactory()
    evenement.contacts.set([agent_1, agent_2, structure_1])

    message = create_message_and_notify(
        message_type=Message.FIN_SUIVI,
        object=evenement,
    )

    mail = assert_mail_common(mailoutbox, message, evenement)
    assert message.content in mail.body
    assert set(mail.to) == {agent_1.email}
    assert set(mail.cc) == set()


def test_notification_notification_ac(mailoutbox):
    evenement = EvenementFactory()
    structure_1 = ContactStructureFactory()
    contact_mus = ContactStructureFactory(structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE)
    contact_bsv = ContactStructureFactory(structure__niveau1=AC_STRUCTURE, structure__niveau2=BSV_STRUCTURE)
    agent_1 = ContactAgentFactory()

    message = create_message_and_notify(
        message_type=Message.NOTIFICATION_AC,
        object=evenement,
        recipients=[agent_1, structure_1],
    )

    mail = assert_mail_common(mailoutbox, message, evenement)
    assert message.content not in mail.body
    expected_content = f"Bonjour,\nLa fiche {evenement.numero} vient d'être déclarée à l'administration centrale."
    assert html.escape(expected_content) in mail.body
    assert set(mail.to) == {contact_mus.email, contact_bsv.email}
    assert set(mail.cc) == set()


def test_notification_compte_rendu(mailoutbox):
    evenement = EvenementFactory()
    contact_mus = ContactStructureFactory(structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE)
    contact_bsv = ContactStructureFactory(structure__niveau1=AC_STRUCTURE, structure__niveau2=BSV_STRUCTURE)

    message = create_message_and_notify(
        message_type=Message.COMPTE_RENDU,
        object=evenement,
        recipients=[contact_mus, contact_bsv],
    )

    mail = assert_mail_common(mailoutbox, message, evenement)
    assert message.content in mail.body
    assert set(mail.to) == {contact_mus.email, contact_bsv.email}
    assert set(mail.cc) == set()


def test_email_contains_correct_link_to_fiche_with_message(mailoutbox):
    evenement = EvenementFactory()
    message = create_message_and_notify(
        message_type=Message.MESSAGE,
        object=evenement,
        recipients=[ContactAgentFactory()],
    )
    body = mailoutbox[0].body
    url = re.search(r'href="([^"]+)"', body).group(1)
    expected_url = f"http://testserver.com{evenement.get_absolute_url_with_message(message.id)}"
    assert url == expected_url


def test_open_message_sidebar_when_clicking_on_link(live_server, page: Page, mailoutbox):
    evenement = EvenementFactory()
    contact = ContactAgentFactory()
    message = create_message_and_notify(
        message_type=Message.MESSAGE,
        object=evenement,
        recipients=[contact],
    )
    body = mailoutbox[0].body
    url = re.search(r'href="([^"]+)"', body).group(1)
    url = url.replace("http://testserver.com", live_server.url)
    page.goto(url)
    expect(page.locator(".sidebar").get_by_text(f"De : {message.sender.display_with_agent_unit}")).to_be_visible()
    expect(page.locator(".sidebar").get_by_text(f"A : {contact.display_with_agent_unit}")).to_be_visible()
    expect(page.locator(".sidebar").get_by_text(message.title)).to_be_visible()
    expect(page.locator(".sidebar").get_by_text(message.content)).to_be_visible()
