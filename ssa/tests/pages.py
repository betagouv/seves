from django.urls import reverse
from playwright.sync_api import Page

from ssa.models import Etablissement


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

    def add_etablissement_with_required_fields(self, etablissement: Etablissement):
        self.page.locator("#add-etablissement").click()
        modal = self.page.locator(".fr-modal__body").locator("visible=true")

        modal.locator('[id$="raison_sociale"]').fill(etablissement.raison_sociale)
        modal.locator(".save-btn").click()

    def add_etablissement(self, etablissement: Etablissement):
        self.page.locator("#add-etablissement").click()
        modal = self.page.locator(".fr-modal__body").locator("visible=true")

        modal.locator('[id$="siret"]').fill(etablissement.siret)
        modal.locator('[id$="raison_sociale"]').fill(etablissement.raison_sociale)
        modal.locator('[id$="_lieu_dit"]').fill(etablissement.adresse_lieu_dit)
        modal.locator('[id$="-commune"]').fill(etablissement.commune)
        modal.locator('[id$="-departement"]').select_option(etablissement.departement)
        modal.locator('[id$="-pays"]').select_option(etablissement.pays.code)
        modal.locator('[id$="-type_exploitant"]').select_option(etablissement.type_exploitant)
        modal.locator('[id$="-position_dossier"]').select_option(etablissement.position_dossier)
        modal.locator('[id$="-quantite_en_stock"]').fill(str(etablissement.quantite_en_stock))
        modal.locator('[id$="-numero_agrement"]').fill(etablissement.numero_agrement)
        modal.locator(".save-btn").click()
        modal.wait_for(state="hidden", timeout=2_000)

    def etablissement_card(self, index=0):
        return self.page.locator(".etablissement-card").nth(index)

    def delete_etablissement(self, index):
        return self.page.locator(".etablissement-card").nth(index).locator(".etablissement-delete-btn").click()

    def add_free_link(self, numero, choice_js_fill):
        choice_js_fill(self.page, "#liens-libre .choices", str(numero), "Événement produit : " + str(numero))


class EvenementProduitDetailsPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, object):
        self.page.goto(f"{self.base_url}{object.get_absolute_url()}")

    @property
    def title(self):
        return self.page.locator(".top-row h1")

    @property
    def last_modification(self):
        return self.page.locator(".last-modification")

    @property
    def information_block(self):
        return self.page.get_by_role("heading", name="Informations").locator("..")

    @property
    def produit_block(self):
        return self.page.get_by_role("heading", name="Produit").locator("..")

    @property
    def risque_block(self):
        return self.page.get_by_role("heading", name="Risque").locator("..")

    @property
    def actions_block(self):
        return self.page.get_by_role("heading", name="Actions engagées").locator("..")

    @property
    def rappel_block(self):
        return self.page.get_by_role("heading", name="Rappel conso").locator("..")

    def etablissement_card(self, index=0):
        return self.page.locator(".etablissement-card").nth(index)

    def etablissement_open_modal(self, index=0):
        return self.page.locator(".etablissement-card").nth(index).locator(".fr-icon-eye-line").click()

    @property
    def etablissement_modal(self):
        return self.page.locator(".fr-modal").locator("visible=true")
