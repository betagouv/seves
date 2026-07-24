from django.urls import reverse
from playwright.sync_api import Page

from sa.models import EvenementAnimal


class WithPreCreationFormPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def open_pre_creation_form(self):
        self.page.get_by_role("button", name="Créer un évènement", exact=True).click()

    def set_statut_animal(self, value):
        self.page.locator("#radio-id_statut_animal").locator(
            f"input[type='radio'][value='{str(value).lower()}' i]"
        ).check(force=True)

    def fill_pre_creation_form(self, evenement: EvenementAnimal):
        self.page.get_by_label("Maladie").select_option(evenement.maladie.name)
        self.page.get_by_label("Espece").select_option(evenement.espece.name)
        self.set_statut_animal(evenement.statut_animal)
        self.page.get_by_role("button", name="Suivant >", exact=True).click()


class EvenementListPage(WithPreCreationFormPage):
    def __init__(self, page: Page, base_url):
        super().__init__(page, base_url)
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('sa:evenement-liste')}")


class EvenementAnimalFormPage(WithPreCreationFormPage):
    fields = [
        "statut_evenement",
        "date_statut_changed",
    ]

    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url
        for field in self.fields:
            setattr(self, field, page.locator(f"#id_{field}"))

    def navigate(self, maladie, espece, statut):
        self.page.goto(
            f"{self.base_url}{reverse('sa:evenement-animal-creation')}?maladie={maladie.pk}&espece={espece.pk}&statut_animal={statut}"
        )

    def fill_required_fields(self, evenement: EvenementAnimal):
        self.statut_evenement.select_option(evenement.statut_evenement)
        self.date_statut_changed.fill(evenement.date_statut_changed.strftime("%Y-%m-%d"))

    def submit(self):
        self.page.get_by_role("button", name="Enregistrer", exact=True).click()
        redirect = reverse("sa:evenement-animal-details", kwargs={"numero": "*"})
        self.page.wait_for_url(f"**{redirect}")
