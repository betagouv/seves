import pytest
from django.utils import html
from model_bakery import baker

from core.constants import AC_STRUCTURE, MUS_STRUCTURE, BSV_STRUCTURE
from core.models import Structure, Agent, Contact, Message
from core.notifications import notify_message
from sv.factories import EvenementFactory


def create_message_and_notify(
    *, message_type, object, content="My message \n Thanks", recipients=None, recipients_copy=None
):
    sender = baker.make(Contact, agent=baker.make(Agent))
    message = Message.objects.create(
        title="TITLE",
        content=content,
        sender=sender,
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
    assert mail.subject == f"Sèves - {evenement.numero} - {message.message_type} - {message.title}"
    assert mail.from_email == "no-reply@beta.gouv.fr"
    assert message.sender.agent.prenom in mail.body
    assert message.sender.agent.nom in mail.body
    assert str(message.sender.agent.structure) in mail.body
    assert evenement.get_absolute_url() in mail.body
    return mail


@pytest.mark.django_db
def test_notification_message(mailoutbox):
    evenement = EvenementFactory()
    contact_1 = baker.make(Contact, agent=baker.make(Agent))
    contact_2 = baker.make(Contact, structure=baker.make(Structure))
    contact_3 = baker.make(Contact, structure=baker.make(Structure))
    contact_4 = baker.make(Contact, agent=baker.make(Agent))
    _contact_5 = baker.make(Contact, structure=baker.make(Structure))
    _contact_6 = baker.make(Contact, agent=baker.make(Agent))

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
    agent_1 = baker.make(Contact, agent=baker.make(Agent))
    agent_2 = baker.make(Contact, agent=baker.make(Agent))
    _agent_3 = baker.make(Contact, agent=baker.make(Agent))
    structure_1 = baker.make(Contact, structure=baker.make(Structure))
    structure_2 = baker.make(Contact, structure=baker.make(Structure))
    _structure_3 = baker.make(Contact, structure=baker.make(Structure))

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
    agent_1 = baker.make(Contact, agent=baker.make(Agent))
    _agent_2 = baker.make(Contact, agent=baker.make(Agent))
    structure_1 = baker.make(Contact, structure=baker.make(Structure))
    _structure_2 = baker.make(Contact, structure=baker.make(Structure))
    evenement.contacts.set([agent_1, structure_1])

    message = create_message_and_notify(
        message_type=Message.POINT_DE_SITUATION,
        object=evenement,
    )

    mail = assert_mail_common(mailoutbox, message, evenement)
    assert message.content in mail.body
    assert set(mail.to) == {agent_1.email}
    assert set(mail.cc) == set()


@pytest.mark.django_db
def test_notification_fin_de_suivi(mailoutbox):
    evenement = EvenementFactory()
    agent_1 = baker.make(Contact, agent=baker.make(Agent, structure__niveau2=MUS_STRUCTURE))
    agent_2 = baker.make(Contact, agent=baker.make(Agent, structure__niveau2="FOO"))
    structure_1 = baker.make(Contact, structure=baker.make(Structure))
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
    agent_1 = baker.make(Contact, agent=baker.make(Agent))
    structure_1 = baker.make(Contact, structure=baker.make(Structure))
    contact_mus = baker.make(Contact, structure=baker.make(Structure, niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE))
    contact_bsv = baker.make(Contact, structure=baker.make(Structure, niveau1=AC_STRUCTURE, niveau2=BSV_STRUCTURE))

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
    contact_mus = baker.make(Contact, structure=baker.make(Structure, niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE))
    contact_bsv = baker.make(Contact, structure=baker.make(Structure, niveau1=AC_STRUCTURE, niveau2=BSV_STRUCTURE))

    message = create_message_and_notify(
        message_type=Message.COMPTE_RENDU,
        object=evenement,
        recipients=[contact_mus, contact_bsv],
    )

    mail = assert_mail_common(mailoutbox, message, evenement)
    assert message.content in mail.body
    assert set(mail.to) == {contact_mus.email, contact_bsv.email}
    assert set(mail.cc) == set()
