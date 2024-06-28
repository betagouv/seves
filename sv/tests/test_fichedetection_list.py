from playwright.sync_api import Page, expect


def test_url(live_server, page: Page):
    response = page.request.get(f"{live_server.url}/sv/fiches-detection/")
    expect(response).to_be_ok()


def test_no_fiches(live_server, page: Page):
    page.goto(f"{live_server.url}/sv/fiches-detection/")
    expect(page.get_by_role("heading", name="Liste des fiches")).to_be_visible()
    expect(page.locator("body")).to_contain_text("Liste des fiches")
