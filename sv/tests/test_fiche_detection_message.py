from playwright.sync_api import Page, expect

from core.models import Message
from ..models import FicheDetection


def test_can_add_and_see_message_without_document(live_server, page: Page, fiche_detection: FicheDetection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{fiche_detection.add_message_url}")

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()
    message = Message.objects.get()
    page.wait_for_url(f"**{message.get_absolute_url()}")

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()


def test_can_add_and_see_message_multiple_documents(live_server, page: Page, fiche_detection: FicheDetection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{fiche_detection.add_message_url}")

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")

    page.locator("#id_document_type").select_option("Autre document")
    page.locator("#id_file").set_input_files("README.md")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("README.md", exact=True)).to_be_visible()

    page.locator("#id_document_type").select_option("Cartographie")
    page.locator("#id_file").set_input_files("requirements.in")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("requirements.in", exact=True)).to_be_visible()

    page.locator("#id_document_type").select_option("Autre document")
    page.locator("#id_file").set_input_files("requirements.txt")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("requirements.txt", exact=True)).to_be_visible()

    # Test to delete the 2nd document to see if the server can handle non-consecutive IDs of inputs
    page.locator("#document_remove_1").click()
    expect(page.get_by_text("requirements.in", exact=True)).not_to_be_visible()

    page.get_by_test_id("fildesuivi-add-submit").click()
    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()
    message = Message.objects.get()
    page.wait_for_url(f"**{message.get_absolute_url()}")

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()

    message = Message.objects.get()
    assert message.documents.count() == 2

    expect(page.get_by_text("README.md", exact=True)).to_be_visible()
    expect(page.get_by_text("requirements.txt", exact=True)).to_be_visible()
