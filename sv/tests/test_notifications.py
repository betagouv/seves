import pytest
from model_bakery import baker

from core.models import Structure, Agent, Contact, Message
from core.notifications import notify_message


@pytest.mark.django_db
def test_notification_message(mailoutbox, fiche_detection):
    sender = baker.make(Contact, agent=baker.make(Agent))
    contact_1 = baker.make(Contact, agent=baker.make(Agent))
    contact_2 = baker.make(Contact, structure=baker.make(Structure))
    contact_3 = baker.make(Contact, structure=baker.make(Structure))
    contact_4 = baker.make(Contact, agent=baker.make(Agent))
    _contact_5 = baker.make(Contact, structure=baker.make(Structure))
    _contact_6 = baker.make(Contact, agent=baker.make(Agent))

    message = Message.objects.create(
        title="TITLE",
        content="My message \n Thanks",
        sender=sender,
        message_type=Message.MESSAGE,
        content_object=fiche_detection,
    )
    message.recipients.set([contact_1, contact_2])
    message.recipients_copy.set([contact_3, contact_4])

    notify_message(message)

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "SEVES - TITLE"
    assert (
        message.body
        == f"Bonjour,\n Vous avez reçu un message sur SEVES dont voici le contenu : \n My message \n Thanks\n\n Pour voir la fiche concernée par cette notification, consultez SEVES : http://testserver.com/sv/fiches-detection/{fiche_detection.pk}/"
    )
    assert message.from_email == "no-reply@beta.gouv.fr"
    assert set(message.to) == {contact_1.email, contact_2.email}
    assert set(message.cc) == {contact_3.email, contact_4.email}


@pytest.mark.django_db
def test_notification_demande_intervention(mailoutbox, fiche_detection):
    sender = baker.make(Contact, agent=baker.make(Agent))
    agent_1 = baker.make(Contact, agent=baker.make(Agent))
    agent_2 = baker.make(Contact, agent=baker.make(Agent))
    _agent_3 = baker.make(Contact, agent=baker.make(Agent))
    structure_1 = baker.make(Contact, structure=baker.make(Structure))
    structure_2 = baker.make(Contact, structure=baker.make(Structure))
    _structure_3 = baker.make(Contact, structure=baker.make(Structure))

    message = Message.objects.create(
        title="TITLE",
        content="My message \n Thanks",
        sender=sender,
        message_type=Message.DEMANDE_INTERVENTION,
        content_object=fiche_detection,
    )
    message.recipients.set([agent_1, structure_1])
    message.recipients_copy.set([agent_2, structure_2])

    notify_message(message)

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "SEVES - TITLE"
    assert (
        message.body
        == f"Bonjour,\n Vous avez reçu un message sur SEVES.\n\n Pour voir la fiche concernée par cette notification, consultez SEVES : http://testserver.com/sv/fiches-detection/{fiche_detection.pk}/"
    )
    assert message.from_email == "no-reply@beta.gouv.fr"
    assert set(message.to) == {structure_1.email}
    assert set(message.cc) == {structure_2.email}


@pytest.mark.django_db
def test_notification_point_de_situation(mailoutbox, fiche_detection):
    sender = baker.make(Contact, agent=baker.make(Agent))
    agent_1 = baker.make(Contact, agent=baker.make(Agent))
    _agent_2 = baker.make(Contact, agent=baker.make(Agent))
    structure_1 = baker.make(Contact, structure=baker.make(Structure))
    _structure_2 = baker.make(Contact, structure=baker.make(Structure))

    message = Message.objects.create(
        title="TITLE",
        content="My message \n Thanks",
        sender=sender,
        message_type=Message.POINT_DE_SITUATION,
        content_object=fiche_detection,
    )
    fiche_detection.contacts.set([agent_1, structure_1])

    notify_message(message)

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "SEVES - TITLE"
    assert (
        message.body
        == f"Bonjour,\n Vous avez reçu un nouveau point de suivi sur SEVES.\n\n Pour voir la fiche concernée par cette notification, consultez SEVES : http://testserver.com/sv/fiches-detection/{fiche_detection.pk}/"
    )
    assert message.from_email == "no-reply@beta.gouv.fr"
    assert set(message.to) == {agent_1.email}
    assert set(message.cc) == set()


@pytest.mark.django_db
def test_notification_fin_de_suivi(mailoutbox, fiche_detection):
    sender = baker.make(Contact, agent=baker.make(Agent))
    agent_1 = baker.make(Contact, agent=baker.make(Agent, structure__niveau2="MUS"))
    agent_2 = baker.make(Contact, agent=baker.make(Agent, structure__niveau2="FOO"))
    structure_1 = baker.make(Contact, structure=baker.make(Structure))

    message = Message.objects.create(
        title="TITLE",
        content="My message \n Thanks",
        sender=sender,
        message_type=Message.FIN_SUIVI,
        content_object=fiche_detection,
    )
    fiche_detection.contacts.set([agent_1, agent_2, structure_1])

    notify_message(message)

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "SEVES - TITLE"
    assert (
        message.body
        == f"Bonjour,\n Vous avez reçu un nouveau point de suivi sur SEVES.\n\n Pour voir la fiche concernée par cette notification, consultez SEVES : http://testserver.com/sv/fiches-detection/{fiche_detection.pk}/"
    )
    assert message.from_email == "no-reply@beta.gouv.fr"
    assert set(message.to) == {agent_1.email}
    assert set(message.cc) == set()
