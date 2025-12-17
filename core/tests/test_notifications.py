import pytest
from django.db.models.signals import post_save

from core.factories import RegionFactory, ContactAgentFactory, ContactStructureFactory
from core.models import FinSuiviContact
from core.notifications import send_as_seves
from core.signals import fin_suivi_added


@pytest.mark.django_db
def test_notifications_are_filtered_with_fin_de_suivi(mailoutbox):
    # We just need a dummy object to test the recipients
    object = RegionFactory()
    object.get_absolute_url = lambda: "foo"

    contact = ContactAgentFactory()
    contact_in_fin_suivi = ContactAgentFactory()

    structure = ContactStructureFactory()
    structure_in_fin_suivi = ContactStructureFactory(structure=contact_in_fin_suivi.agent.structure)

    # We need to disconect the signal as Region object is not tracked with revision, so the fin_suivi_added signal
    # makes no sense and crashes.
    post_save.disconnect(fin_suivi_added, sender=FinSuiviContact)
    FinSuiviContact.objects.create(content_object=object, contact=structure_in_fin_suivi)
    post_save.connect(fin_suivi_added, sender=FinSuiviContact)

    send_as_seves(
        recipients=[contact.email, structure.email, contact_in_fin_suivi.email, structure_in_fin_suivi.email],
        subject="Test",
        message="Test",
        html_message="Test",
        object=object,
    )

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]

    assert mail.to == [contact.email, structure.email]


@pytest.mark.django_db
def test_handle_empty_emails_for_recipients(mailoutbox):
    # We just need a dummy object to test the recipients
    object = RegionFactory()
    object.get_absolute_url = lambda: "foo"

    send_as_seves(
        recipients=["foo@bar.com", ""],
        subject="Test",
        message="Test",
        html_message="Test",
        object=object,
    )

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]

    assert mail.to == ["foo@bar.com"]
