import csv
from unittest import mock

from django.urls import reverse
from playwright.sync_api import expect

from sv.factories import FicheDetectionFactory


def test_can_download_export_fiche_detection(live_server, page):
    FicheDetectionFactory()
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")

    with page.expect_download() as download_info:
        page.get_by_role("button", name="Extraire").click()

    download = download_info.value
    assert download.suggested_filename == "export_fiche_detection.csv"


def test_export_is_filtered(live_server, page):
    FicheDetectionFactory(evenement__numero_annee=2025)
    FicheDetectionFactory(evenement__numero_annee=2026)
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")

    page.get_by_label("Année").fill("2025")
    page.get_by_role("button", name="Rechercher").click()

    with page.expect_download() as download_info:
        page.get_by_role("button", name="Extraire").click()

    download = download_info.value
    assert download.suggested_filename == "export_fiche_detection.csv"

    path = download.path()
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        lines = list(reader)

    assert len(lines) == 2


def test_export_shows_modal_when_above_threshold(live_server, page):
    FicheDetectionFactory()
    FicheDetectionFactory()

    with mock.patch("sv.views.VOLUMINOUS_EXTRACT_THRESHOLD", 1):
        page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
        page.get_by_role("button", name="Extraire").click()
        expect(page.locator("#fr-modal-extraire-evenements")).to_be_visible()

        with page.expect_download() as download_info:
            page.get_by_test_id("submit-extract").click()

    download = download_info.value
    assert download.suggested_filename == "export_fiche_detection.csv"


def test_no_modal_when_below_threshold(live_server, page):
    FicheDetectionFactory()
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")

    expect(page.locator("#fr-modal-extraire-evenements")).to_have_count(0)
