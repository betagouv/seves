import csv

from django.urls import reverse

from sv.factories import FicheDetectionFactory


def test_can_download_export_fiche_detection(live_server, page):
    FicheDetectionFactory()
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")

    with page.expect_download() as download_info:
        page.get_by_test_id("extract").click()

    download = download_info.value
    assert download.suggested_filename == "export_fiche_detection.csv"


def test_export_is_filtered(live_server, page):
    FicheDetectionFactory(evenement__numero_annee=2025)
    FicheDetectionFactory(evenement__numero_annee=2026)
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")

    page.get_by_label("Année").fill("2025")
    page.get_by_role("button", name="Rechercher").click()

    with page.expect_download() as download_info:
        page.get_by_test_id("extract").click()

    download = download_info.value
    assert download.suggested_filename == "export_fiche_detection.csv"

    path = download.path()
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        lines = list(reader)

    assert len(lines) == 2
