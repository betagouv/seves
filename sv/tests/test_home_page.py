from playwright.sync_api import Page, expect


def test_seves_in_title(live_server, page: Page):
    page.goto(live_server.url)
    expect(page.get_by_role("heading", name="Sèves")).to_be_visible()
    expect(page.get_by_role("heading")).to_contain_text("Sèves")
