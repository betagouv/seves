from django.urls import reverse
from playwright.sync_api import Page


class EvenementProduitCreationPage:
    info_fields = ["numero_rasff", "type_evenement", "source", "cerfa_recu", "description", "numero_rasff"]
    produit_fields = [
        "denomination",
        "marque",
        "lots",
        "description_complementaire",
    ]
    risque_fields = [
        "quantification",
        "quantification_unite",
        "evaluation",
        "reference_souches",
        "reference_clusters",
        "produit_pret_a_manger",
    ]
    action_fields = [
        "actions_engagees",
    ]
    fields = info_fields + produit_fields + risque_fields + action_fields

    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url
        for field in self.fields:
            setattr(self, field, page.locator(f"#id_{field}"))

        self.temperature_conservation = page.get_by_label("Temperature conservation")
        self.produit_pret_a_manger = page.get_by_label("Produit pret a manger")

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('ssa:evenement-produit-creation')}")

    def fill_required_fields(self, evenement_produit):
        self.type_evenement.select_option(evenement_produit.type_evenement)
        self.description.fill(evenement_produit.description)
        self.denomination.fill(evenement_produit.denomination)

    def set_temperature_conservation(self, value):
        self.page.locator(f"input[type='radio'][value='{value}']").check(force=True)

    def set_pret_a_manger(self, value):
        self.page.locator(f"input[type='radio'][name='produit_pret_a_manger'][value='{value}']").check(force=True)

    def submit_as_draft(self):
        self.page.locator(".evenement-produit-form-header").get_by_text("Enregistrer le brouillon", exact=True).click()

    def publish(self):
        self.page.locator(".evenement-produit-form-header").get_by_text("Enregistrer", exact=True).click()
