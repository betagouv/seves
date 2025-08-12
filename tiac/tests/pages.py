from django.urls import reverse
from playwright.sync_api import Page

from tiac.models import EvenementSimple


class EvenementSimpleFormPage:
    fields = [
        "date_reception",
        "evenement_origin",
        "modalites_declaration",
        "contenu",
        "notify_ars",
        "nb_sick_persons",
        "follow_up",
    ]

    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url
        for field in self.fields:
            setattr(self, field, page.locator(f"#id_{field}"))

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('tiac:evenement-simple-creation')}")

    def set_follow_up(self, value):
        self.page.locator(f"input[type='radio'][value='{value}']").check(force=True)

    def set_modalites_declaration(self, value):
        self.page.locator("#radio-id_modalites_declaration").locator(f"input[type='radio'][value='{value}']").check(
            force=True
        )

    def set_notify_ars(self, value):
        self.page.locator("#radio-id_notify_ars").locator(f"input[type='radio'][value='{str(value).lower()}']").check(
            force=True
        )

    def fill_required_fields(self, evenement: EvenementSimple):
        self.contenu.fill(evenement.contenu)
        self.set_follow_up(evenement.follow_up)

    def submit_as_draft(self):
        self.page.get_by_role("button", name="Enregistrer le brouillon").click()
