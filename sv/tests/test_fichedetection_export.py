from django.urls import reverse
from playwright.sync_api import expect


def test_can_download_export_fiche_detection(live_server, page, fiche_detection):
    page.goto(f"{live_server.url}{reverse('fiche-detection-list')}")

    page.get_by_test_id("extract-open").click()
    expect(page.get_by_test_id("extract-submit")).to_be_visible()

    with page.expect_download() as download_info:
        page.get_by_test_id("extract-submit").click()

    download = download_info.value
    assert download.suggested_filename == "export_fiche_detection.csv"
