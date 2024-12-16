from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import Page, expect

from core.models import Structure, Contact, Visibilite, Message
from core.constants import MUS_STRUCTURE, BSV_STRUCTURE
from ..factories import FicheDetectionFactory
from ..models import FicheDetection


def test_can_notify_ac(live_server, page: Page, mailoutbox):
    fiche_detection = FicheDetectionFactory()
    Contact.objects.create(structure=Structure.objects.create(niveau2=MUS_STRUCTURE), email="foo@bar.com")
    Contact.objects.create(structure=Structure.objects.create(niveau2=BSV_STRUCTURE), email="foo@bar.com")
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Déclarer à l'AC").click()

    expect(page.get_by_text("L'administration centrale a été notifiée avec succès")).to_be_visible()

    expect(page.get_by_text("Déclaré AC")).to_be_visible()

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Notification à l'AC"
    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Notification à l'administration centrale"

    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("button", name="Déclarer à l'AC")).to_be_disabled()

    fiche_detection.refresh_from_db()
    assert fiche_detection.is_ac_notified is True

    assert len(mailoutbox) == 1

    page.goto(f"{live_server.url}{reverse('fiche-liste')}")
    cell_selector = ".fiches__list-row td:nth-child(8) a"
    assert page.text_content(cell_selector).strip() == "local"
    expect(page.locator(".fiches__list-row td:nth-child(8) a .fr-icon-notification-3-line")).to_be_visible()


def test_cant_notify_ac_if_draft_in_ui(live_server, page, mocked_authentification_user):
    fiche_detection = FicheDetectionFactory(visibilite=Visibilite.BROUILLON)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_role("button", name="Déclarer à l'AC")).not_to_be_visible()


def test_cant_notify_ac_if_draft_with_request(mocked_authentification_user, client):
    fiche_detection = FicheDetectionFactory(visibilite=Visibilite.BROUILLON)

    response = client.post(
        reverse("notify-ac"),
        {
            "next": fiche_detection.get_absolute_url(),
            "content_id": fiche_detection.id,
            "content_type_id": ContentType.objects.get_for_model(FicheDetection).id,
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_if_email_notification_fails_does_not_create_message_or_update_status(live_server, page: Page, mailoutbox):
    fiche_detection = FicheDetectionFactory()
    Contact.objects.create(structure=Structure.objects.create(niveau2=MUS_STRUCTURE))
    Contact.objects.create(structure=Structure.objects.create(niveau2=BSV_STRUCTURE), email="foo@bar.com")

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Déclarer à l'AC").click()

    assert len(mailoutbox) == 0
    expect(page.get_by_text("Une erreur s'est produite lors de la notification")).to_be_visible()
    assert not fiche_detection.messages.filter(message_type=Message.NOTIFICATION_AC).exists()
    fiche_detection.refresh_from_db()
    assert fiche_detection.is_ac_notified is False


def test_bsv_and_mus_are_added_to_contact_when_notify_ac(live_server, page: Page):
    fiche_detection = FicheDetectionFactory()
    Contact.objects.create(structure=Structure.objects.create(niveau2=MUS_STRUCTURE), email="foo@bar.com")
    Contact.objects.create(structure=Structure.objects.create(niveau2=BSV_STRUCTURE), email="foo@bar.com")

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Déclarer à l'AC").click()

    fiche_detection.refresh_from_db()
    assert fiche_detection.contacts.filter(structure__niveau2=MUS_STRUCTURE).exists()
    assert fiche_detection.contacts.filter(structure__niveau2=BSV_STRUCTURE).exists()
