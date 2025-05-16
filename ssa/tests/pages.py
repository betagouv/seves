import json
from urllib.parse import quote

from django.urls import reverse
from playwright.sync_api import Page

from ssa.models import Etablissement


class EvenementProduitCreationPage:
    info_fields = ["numero_rasff", "type_evenement", "source", "description", "numero_rasff"]
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

    def set_categorie_produit(self, evenement_produit):
        label = evenement_produit.get_categorie_produit_display()
        self.page.locator("#categorie-produit .treeselect-input__edit").click()
        for part in label.split(">"):
            if part == label.split(">")[-1]:
                self.page.get_by_title(part.strip(), exact=True).click()
            else:
                self.page.get_by_title(part.strip(), exact=True).locator(".treeselect-list__item-icon").click()

    def set_temperature_conservation(self, value):
        self.page.locator(f"input[type='radio'][value='{value}']").check(force=True)

    def set_pret_a_manger(self, value):
        self.page.locator(f"input[type='radio'][name='produit_pret_a_manger'][value='{value}']").check(force=True)

    def set_quantification_unite(self, value):
        self.page.query_selector(".risk-column .choices").click()
        self.page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        self.page.locator("*:focus").fill(value)
        self.page.locator(".choices__list--dropdown .choices__list").get_by_role(
            "treeitem", name=value, exact=True
        ).nth(0).click()

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
        tag = self.page.locator(".fr-tag", has_text=numero)
        box = tag.bounding_box()
        self.page.mouse.click(box["x"] + box["width"] - 15, box["y"] - 5 + box["height"] / 2)

    def add_etablissement_with_required_fields(self, etablissement: Etablissement):
        modal = self.open_etablissement_modal()
        modal.locator('[id$="raison_sociale"]').fill(etablissement.raison_sociale)
        self.close_etablissement_modal()

    def open_etablissement_modal(self):
        self.page.locator("#add-etablissement").click()
        return self.current_modal

    def add_etablissement_siren(self, value, full_value, choice_js_fill):
        self.current_modal.locator("#sirene-btn").click()
        choice_js_fill(self.page, "#header-search .choices", value, full_value)

    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")

    @property
    def current_modal_address_field(self):
        return self.current_modal.locator('[id$="_lieu_dit"]').locator("..")

    @property
    def current_modal_raison_sociale_field(self):
        return self.current_modal.locator('[id$="raison_sociale"]')

    def close_etablissement_modal(self):
        self.current_modal.locator(".save-btn").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    def force_etablissement_adresse(self, adresse, mock_call=False):
        if mock_call:

            def handle(route):
                route.fulfill(status=200, content_type="application/json", body=json.dumps({"features": []}))

            self.page.route(
                f"https://api-adresse.data.gouv.fr/search/?q={quote(adresse)}&limit=15",
                handle,
            )

        self.current_modal_address_field.click()
        self.page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        self.page.locator("*:focus").fill(adresse)
        self.page.get_by_role("option", name=f"{adresse} (Forcer la valeur)", exact=True).click()

    def add_etablissement(self, etablissement: Etablissement):
        modal = self.open_etablissement_modal()

        modal.locator('[id$="siret"]').fill(etablissement.siret)
        modal.locator('[id$="-numero_agrement"]').fill(etablissement.numero_agrement)
        modal.locator('[id$="raison_sociale"]').fill(etablissement.raison_sociale)
        self.force_etablissement_adresse(etablissement.adresse_lieu_dit, mock_call=True)
        modal.locator('[id$="-commune"]').fill(etablissement.commune)
        modal.locator('[id$="-departement"]').select_option(etablissement.departement)
        modal.locator('[id$="-pays"]').select_option(etablissement.pays.code)
        modal.locator('[id$="-type_exploitant"]').select_option(etablissement.type_exploitant)
        modal.locator('[id$="-position_dossier"]').select_option(etablissement.position_dossier)

        self.close_etablissement_modal()

    def open_edit_etablissement(self):
        self.page.locator(".etablissement-edit-btn").click()

    def etablissement_card(self, index=0):
        return self.page.locator(".etablissement-card").nth(index)

    def delete_etablissement(self, index):
        return self.page.locator(".etablissement-card").nth(index).locator(".etablissement-delete-btn").click()

    def add_free_link(self, numero, choice_js_fill):
        choice_js_fill(self.page, "#liens-libre .choices", str(numero), "Événement produit : " + str(numero))

    @property
    def error_messages(self):
        return self.page.locator(".fr-alert__title").all_text_contents()


class EvenementProduitDetailsPage:
    def submit_form(self):
        self.page.locator(".fiche-produit-form-header .fr-btn").click()

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

    def delete(self):
        self.page.get_by_role("button", name="Actions").click()
        self.page.get_by_text("Supprimer l'événement", exact=True).click()
        self.page.get_by_test_id("submit-delete-modal").click()

    def cloturer(self):
        self.page.get_by_role("button", name="Actions").click()
        self.page.get_by_role("link", name="Clôturer l'événement").click()
        self.page.get_by_role("button", name="Clôturer").click()

    def open_compte_rendu_di(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_test_id("fildesuivi-actions-compte-rendu").click()

    @property
    def message_form_title(self):
        return self.page.locator("#message-type-title")

    def add_limited_recipient_to_message(self, contact: str, choice_js_fill):
        choice_js_fill(
            self.page,
            ".choices:has(#id_recipients_limited_recipients)",
            contact,
            contact,
            use_locator_as_parent_element=True,
        )

    def add_message_content_and_send(self):
        self.page.locator("#id_title").fill("Title of the message")
        self.page.locator("#id_content").fill("My content \n with a line return")
        self.page.get_by_test_id("fildesuivi-add-submit").click()

    @property
    def fil_de_suivi_sender(self, line_number=1):
        return self.page.text_content(f"#table-sm-row-key-{line_number} td:nth-child(2) a")

    @property
    def fil_de_suivi_recipients(self, line_number=1):
        return self.page.text_content(f"#table-sm-row-key-{line_number} td:nth-child(3) a")

    @property
    def fil_de_suivi_title(self, line_number=1):
        return self.page.text_content(f"#table-sm-row-key-{line_number} td:nth-child(4) a")

    @property
    def fil_de_suivi_type(self, line_number=1):
        return self.page.text_content(f"#table-sm-row-key-{line_number} td:nth-child(6) a")


class EvenementProduitListPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('ssa:evenement-produit-liste')}")

    def _cell_content(self, line_index, cell_index):
        return self.page.locator(f"tbody tr:nth-child({line_index}) td:nth-child({cell_index})")

    def numero_cell(self, line_index=1):
        return self._cell_content(line_index, 1)

    def date_creation_cell(self, line_index=1):
        return self._cell_content(line_index, 2)

    def description_cell(self, line_index=1):
        return self._cell_content(line_index, 3)

    def createur_cell(self, line_index=1):
        return self._cell_content(line_index, 6)

    def etat_cell(self, line_index=1):
        return self._cell_content(line_index, 7)

    def liens_cell(self, line_index=1):
        return self._cell_content(line_index, 8)

    @property
    def numero_field(self):
        return self.page.locator("#id_numero")

    @property
    def numero_rasff_field(self):
        return self.page.locator("#id_numero_rasff")

    @property
    def type_evenement_select(self):
        return self.page.locator("#id_type_evenement")

    @property
    def start_date_field(self):
        return self.page.locator("#id_start_date")

    @property
    def end_date_field(self):
        return self.page.locator("#id_end_date")

    @property
    def full_text_field(self):
        return self.page.locator("#id_full_text_search")

    def submit_search(self):
        return self.page.locator("#search-form").get_by_text("Rechercher", exact=True).click()

    def reset_search(self):
        return self.page.locator("#search-form").get_by_text("Effacer", exact=True).click()
