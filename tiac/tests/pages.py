import json
import re
from urllib.parse import quote

from django.urls import reverse
from playwright.sync_api import Page

from tiac.models import EvenementSimple, Etablissement


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
        redirect = reverse("tiac:evenement-simple-details", kwargs={"numero": "*"})
        self.page.wait_for_url(f"**{redirect}")

    def add_free_link(self, numero, choice_js_fill, link_label="Enregistrement simple : "):
        choice_js_fill(self.page, "#liens-libre .choices", str(numero), link_label + str(numero))

    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")

    def open_etablissement_modal(self):
        self.page.get_by_role("button", name="Ajouter").click()
        return self.current_modal

    @property
    def current_modal_address_field(self):
        return self.current_modal.locator('[id$="_lieu_dit"]').locator("..")

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

    def fill_etablissement(self, modal, etablissement: Etablissement):
        modal.locator('[id$="type_etablissement"]').fill(etablissement.type_etablissement)
        modal.locator('[id$="raison_sociale"]').fill(etablissement.raison_sociale)
        modal.locator('[id$="enseigne_usuelle"]').fill(etablissement.enseigne_usuelle)
        self.force_etablissement_adresse(etablissement.adresse_lieu_dit, mock_call=True)
        modal.locator('[id$="-commune"]').fill(etablissement.commune)
        modal.locator('[id$="-departement"]').select_option(f"{etablissement.departement}")
        modal.locator('[id$="-pays"]').select_option(etablissement.pays.code)

    def close_etablissement_modal(self):
        self.current_modal.locator(".save-btn").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    def add_etablissement(self, etablissement: Etablissement):
        modal = self.open_etablissement_modal()
        self.fill_etablissement(modal, etablissement)
        self.close_etablissement_modal()

    def publish(self):
        self.page.locator("#submit_publish").click()

    def get_etablissement_card(self, card_index):
        return self.page.locator(".modal-etablissement-container").all()[card_index].locator(".etablissement-card")

    def get_detail_modal_content(self, index):
        self.get_etablissement_card(index).locator(".detail-display").click()
        modal = self.page.locator(".detail-modal").locator("visible=true")
        content = [it for it in re.split(r"\s*\n\s*", modal.locator(".fr-modal__content").text_content()) if it]
        modal.locator(".fr-btn--close").click()
        modal.wait_for(state="hidden")
        return content

    def edit_etablissement(self, index, **kwargs):
        card = self.get_etablissement_card(index)
        card.locator(".modify-button").click()

        for k, v in kwargs.items():
            self.page.locator(".modal-etablissement-container").all()[index].locator(".modal-etablissement").locator(
                "visible=true"
            ).locator(f'[id$="{k}"]').fill(v)

        self.close_etablissement_modal()


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

    def delete(self):
        self.page.get_by_role("button", name="Actions").click()
        self.page.get_by_text("Supprimer l'événement", exact=True).click()
        self.page.get_by_test_id("submit-delete-modal").click()

    def cloturer(self):
        self.page.get_by_role("button", name="Actions").click()
        self.page.get_by_role("link", name="Clôturer l'événement").click()
        self.page.get_by_role("button", name="Clôturer").click()

    def transfer(self, choice_js_fill, libelle):
        self.page.get_by_role("button", name="Actions").click()
        self.page.get_by_role("link", name="Transférer à une autre DD").click()
        choice_js_fill(self.page, "#fr-modal-transfer", libelle, libelle)
        self.page.get_by_role("button", name="Transférer").click()

    def etablissement_card(self, index=0):
        return self.page.locator(".etablissement-card").nth(index)

    def etablissement_open_modal(self, index=0):
        return self.page.locator(".etablissement-card").nth(index).get_by_text("Voir le détail", exact=True).click()

    @property
    def etablissement_modal(self):
        return self.page.locator(".fr-modal").locator("visible=true")

    def publish(self):
        self.page.get_by_role("button", name="Publier").click()
