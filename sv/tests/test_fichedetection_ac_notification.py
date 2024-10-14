from django.urls import reverse
from playwright.sync_api import Page, expect

from core.models import Structure, Contact, Visibilite
from ..models import FicheDetection


def test_can_notify_ac(live_server, page: Page, fiche_detection: FicheDetection, mailoutbox):
    fiche_detection.visibilite = Visibilite.LOCAL
    fiche_detection.save()
    Contact.objects.create(structure=Structure.objects.create(niveau2="MUS"), email="foo@bar.com")
    Contact.objects.create(structure=Structure.objects.create(niveau2="SAS/SDSPV/BSV"), email="foo@bar.com")
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


def test_cant_notify_ac_draft(live_server, page: Page, fiche_detection: FicheDetection, mailoutbox):
    fiche_detection.visibilite = Visibilite.BROUILLON
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("button", name="Déclarer à l'AC")).to_be_disabled()
