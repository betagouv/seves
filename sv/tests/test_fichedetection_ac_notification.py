from playwright.sync_api import Page, expect

from core.models import Structure, Contact
from ..models import FicheDetection


def test_can_notify_ac(live_server, page: Page, fiche_detection: FicheDetection, mailoutbox):
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
