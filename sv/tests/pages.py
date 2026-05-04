from playwright.sync_api import Page

from core.pages import WithActionsPage


class EvenementPage(WithActionsPage):
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, object):
        return self.page.goto(f"{self.base_url}{object.get_absolute_url()}")
