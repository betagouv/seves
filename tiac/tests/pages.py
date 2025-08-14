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

    def add_free_link(self, numero, choice_js_fill, link_label="Évenement simple : "):
        choice_js_fill(self.page, "#liens-libre .choices", str(numero), link_label + str(numero))


class EvenementListPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('tiac:evenement-liste')}")

    def _cell_content(self, line_index, cell_index):
        return self.page.locator(f"tbody tr:nth-child({line_index}) td:nth-child({cell_index})")

    def numero_cell(self, line_index=1):
        return self._cell_content(line_index, 1)

    def createur_cell(self, line_index=1):
        return self._cell_content(line_index, 2)

    def date_reception_cell(self, line_index=1):
        return self._cell_content(line_index, 3)

    def etablissement_cell(self, line_index=1):
        return self._cell_content(line_index, 4)

    def malades_cell(self, line_index=1):
        return self._cell_content(line_index, 5)

    def type_cell(self, line_index=1):
        return self._cell_content(line_index, 6)

    def conclusion_cell(self, line_index=1):
        return self._cell_content(line_index, 7)

    def danger_cell(self, line_index=1):
        return self._cell_content(line_index, 8)

    def etat_cell(self, line_index=1):
        return self._cell_content(line_index, 9)


class EvenementSimpleDetailsPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, object):
        return self.page.goto(f"{self.base_url}{object.get_absolute_url()}")

    @property
    def title(self):
        return self.page.locator(".details-top-row h1").nth(0)

    @property
    def last_modification(self):
        return self.page.locator(".last-modification")

    @property
    def context_block(self):
        return self.page.get_by_role("heading", name="Le contexte").locator("..")

    @property
    def modalite(self):
        return self.page.get_by_test_id("modalite")

    @property
    def origin(self):
        return self.page.get_by_test_id("origin")

    @property
    def links_block(self):
        return self.page.get_by_role("heading", name="Événements liés").locator("..")
