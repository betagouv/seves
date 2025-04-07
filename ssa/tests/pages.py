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
        self.numero_rappel_part_1 = page.locator("#rappel-1")
        self.numero_rappel_part_2 = page.locator("#rappel-2")
        self.numero_rappel_part_3 = page.locator("#rappel-3")
        self.numero_rappel_submit = page.locator("#rappel-submit")

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
        self.page.locator("#submit_draft").click()

    def publish(self):
        self.page.locator("#submit_publish").click()

    def add_rappel_conso(self, numero):
        p1, p2, p3 = numero.split("-")
        self.numero_rappel_part_1.fill(p1)
        self.numero_rappel_part_2.fill(p2)
        self.numero_rappel_part_3.fill(p3)
        self.numero_rappel_submit.click()

    def delete_rappel_conso(self, numero):
        self.page.locator(".fr-tag", has_text=numero).click()
