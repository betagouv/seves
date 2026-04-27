from playwright.sync_api import Page, expect

from conftest import playwright_repeatable


class EvenementPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, object):
        return self.page.goto(f"{self.base_url}{object.get_absolute_url()}")

    @playwright_repeatable
    def download(self):
        action_dropdown = self.page.locator("#action-1")
        if not action_dropdown.is_visible():
            self.page.get_by_role("button", name="Actions").click()
            expect(action_dropdown).to_be_visible()
        with self.page.expect_download() as download_info:
            self.page.get_by_text("Télécharger le document", exact=True).click()
        return download_info
