import json
import re
from urllib.parse import quote

from django.urls import reverse
from playwright.sync_api import Page, expect, Locator

from ssa.models import CategorieDanger
from ssa.tests.pages import WithTreeSelect
from tiac.constants import TypeRepas
from tiac.models import (
    EvenementSimple,
    Etablissement,
    InvestigationTiac,
    RepasSuspect,
    AlimentSuspect,
    AnalyseAlimentaire,
)


class WithEtablissementMixin:
    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")

    @property
    def etablissement_modal(self):
        return self.page.locator(".fr-modal").locator("visible=true")

    def get_etablissement_card(self, card_index=0):
        return self.page.locator(".modal-etablissement-container").all()[card_index].locator(".etablissement-card")

    def etablissement_open_modal(self, index=0):
        return self.page.locator(".etablissement-card").nth(index).get_by_text("Voir le détail", exact=True).click()

    def open_etablissement_modal(self):
        self.page.locator(".etablissement-header").get_by_role("button", name="Ajouter").click()
        self.current_modal.wait_for(state="visible")
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

    def delete_etablissement(self, card_index):
        self.get_etablissement_card(card_index).locator(".delete-button").click()
        modal = self.page.locator(".delete-modal").locator("visible=true")
        modal.locator(".delete-confirmation").click()
        modal.wait_for(state="hidden")

    def edit_etablissement(self, index, **kwargs):
        card = self.get_etablissement_card(index)
        card.locator(".modify-button").click()

        for k, v in kwargs.items():
            self.page.locator(".modal-etablissement-container").all()[index].locator(".modal-etablissement").locator(
                "visible=true"
            ).locator(f'[id$="{k}"]').fill(v)

        self.close_etablissement_modal()


class WithAnalyseAlimentaireMixin(WithTreeSelect):
    def open_analyse_alimentaire_modal(self):
        self.page.locator(".analyses-alimentaires-fieldset").get_by_role("button", name="Ajouter").click()
        self.current_modal.wait_for(state="visible")
        return self.current_modal

    def fill_analyse_alimentaire(self, modal: Locator, analyse: AnalyseAlimentaire):
        modal.locator('[id$="reference_prelevement"]').fill(analyse.reference_prelevement)
        modal.locator('[id$="etat_prelevement"]').select_option(analyse.etat_prelevement)
        modal.locator("#categorie-danger").evaluate("el => el.scrollIntoView()")
        for categorie_danger in analyse.categorie_danger:
            self._set_treeselect_option("categorie-danger", CategorieDanger(categorie_danger).label)
        modal.locator('[id$="comments"]').fill(analyse.comments)
        modal.locator('[id$="reference_souche"]').fill(analyse.reference_souche)
        modal.locator(f"[id$='sent_to_lnr_cnr'] input[type='radio'][value='{str(analyse.sent_to_lnr_cnr)}']").check(
            force=True
        )

    def close_analyse_alimentaire_modal(self):
        self.current_modal.locator(".save-btn").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    def add_analyse_alimentaire(self, analyse: AnalyseAlimentaire):
        modal = self.open_analyse_alimentaire_modal()
        self.fill_analyse_alimentaire(modal, analyse)
        self.close_analyse_alimentaire_modal()

    @property
    def nb_analyse(self):
        return self.page.locator(".analyse-card").locator("visible=true").count()


class EvenementSimpleFormPage(WithEtablissementMixin):
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
        self.follow_up.select_option(value)

    def set_modalites_declaration(self, value):
        self.page.locator("#radio-id_modalites_declaration").locator(f"input[type='radio'][value='{value}']").check(
            force=True
        )

    def set_notify_ars(self, value):
        self.page.locator("#radio-id_notify_ars").locator(f"input[type='radio'][value='{str(value).lower()}' i]").check(
            force=True
        )

    def fill_required_fields(self, evenement: EvenementSimple):
        self.contenu.fill(evenement.contenu)
        self.set_follow_up(evenement.follow_up)

    def submit_as_draft(self):
        self.submit("Enregistrer le brouillon")

    def submit(self, btn_txt="Enregistrer"):
        self.page.get_by_role("button", name=btn_txt).click()
        redirect = reverse("tiac:evenement-simple-details", kwargs={"numero": "*"})
        self.page.wait_for_url(f"**{redirect}")

    def add_free_link(self, numero, choice_js_fill, link_label="Enregistrement simple : "):
        choice_js_fill(self.page, "#liens-libre .choices", str(numero), link_label + str(numero))

    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")

    def publish(self):
        self.page.locator("#submit_publish").click()

    def get_detail_modal_content(self, index):
        self.get_etablissement_card(index).locator(".detail-display").click()
        modal = self.page.locator(".detail-modal").locator("visible=true")
        content = [it for it in re.split(r"\s*\n\s*", modal.locator(".fr-modal__content").text_content()) if it]
        modal.locator(".fr-btn--close").click()
        modal.wait_for(state="hidden")
        return content


class EvenementSimpleEditFormPage(EvenementSimpleFormPage):
    def __init__(self, page: Page, base_url, event: EvenementSimple):
        super().__init__(page, base_url)
        self.event = event

    def navigate(self):
        return self.page.goto(
            f"{self.base_url}{reverse('tiac:evenement-simple-edition', kwargs={'pk': self.event.pk})}"
        )

    def delete_evenement_lie(self, index=0):
        locator = self.page.locator("#liens-libre .choices__button")
        previous = locator.count()
        locator.all()[index].click()
        expect(locator).to_have_count(previous - 1)


class EvenementListPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('tiac:evenement-liste')}")

    @property
    def numero_field(self):
        return self.page.locator("#id_numero")

    @property
    def type_evenement(self):
        return self.page.locator("#id_type_evenement")

    @property
    def with_links(self):
        return self.page.locator('label[for="id_with_free_links"]')

    @property
    def start_date_field(self):
        return self.page.locator("#id_start_date")

    @property
    def end_date_field(self):
        return self.page.locator("#id_end_date")

    @property
    def full_text_field(self):
        return self.page.locator("#id_full_text_search")

    def set_agent_filter(self, value, choice_js_fill_from_element):
        element = self.page.locator("#id_agent_contact").locator("..")
        choice_js_fill_from_element(self.page, element, value, value)

    def set_structure_filter(self, value, choice_js_fill_from_element):
        element = self.page.locator("#id_structure_contact").locator("..")
        choice_js_fill_from_element(self.page, element, value, value)

    def submit_search(self):
        return self.page.locator("#search-form").get_by_text("Rechercher", exact=True).click()

    def _cell_content(self, line_index, cell_index):
        return self.page.locator(f"tbody tr:nth-child({line_index}) td:nth-child({cell_index})")

    @property
    def nb_lines(self):
        return self.page.locator("tbody tr").count()

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

    def open_sidebar(self):
        self.page.locator(".open-sidebar").click()

    def close_sidebar(self):
        self.page.locator(".close-sidebar").click()

    def reset_more_filters(self):
        self.page.locator(".clear-btn").click()

    def reset_search(self):
        return self.page.locator("#reset-btn").click()

    def add_filters(self):
        return self.page.locator(".add-btn").click()

    @property
    def etat(self):
        return self.page.locator("#id_etat")

    @property
    def numero_sivss(self):
        return self.page.locator("#id_numero_sivss")

    @property
    def nb_sick_persons(self):
        return self.page.locator("#id_nb_sick_persons")

    @property
    def nb_dead_persons(self):
        return self.page.locator("#id_nb_dead_persons")

    @property
    def nb_participants(self):
        return self.page.locator("#id_nb_personnes_repas")

    @property
    def siret(self):
        return self.page.locator("#id_siret")

    @property
    def commune(self):
        return self.page.locator("#id_commune")

    @property
    def departement(self):
        return self.page.locator("#id_departement")

    @property
    def pays(self):
        return self.page.locator("#id_pays")

    def select_danger_syndromiques(self, dangers, choice_js_fill_from_element_with_value):
        field = self.page.locator("#id_danger_syndromiques_suspectes")
        choices = [(d, d) for d in dangers]
        choice_js_fill_from_element_with_value(self.page, field.locator(".."), choices)


class EvenementSimpleDetailsPage(WithEtablissementMixin):
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

    def etablissement_card(self, index=0):
        return self.page.locator(".etablissement-card").nth(index)

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

    def publish(self):
        self.page.get_by_role("button", name="Publier").click()


class InvestigationTiacFormPage(WithAnalyseAlimentaireMixin, WithEtablissementMixin, WithTreeSelect):
    fields = [
        "date_reception",
        "evenement_origin",
        "modalites_declaration",
        "contenu",
        "will_trigger_inquiry",
        "numero_sivss",
        "type_evenement",
        "notify_ars",
        "nb_sick_persons",
        "nb_sick_persons_to_hospital",
        "nb_dead_persons",
        "datetime_first_symptoms",
        "datetime_last_symptoms",
        "analyses_sur_les_malades",
        "precisions",
        "suspicion_conclusion",
        "selected_hazard",
        "conclusion_comment",
    ]

    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url
        for field in self.fields:
            setattr(self, field, page.locator(f"#id_{field}"))

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('tiac:investigation-tiac-creation')}")

    def set_modalites_declaration(self, value):
        self.page.locator("#radio-id_modalites_declaration").locator(f"input[type='radio'][value='{value}']").check(
            force=True
        )

    def set_will_trigger_inquiry(self, value):
        self.page.locator("#radio-id_will_trigger_inquiry").locator(
            f"input[type='radio'][value='{str(value).lower()}']"
        ).check(force=True)

    def set_notify_ars(self, value):
        self.page.locator("#radio-id_notify_ars").locator(f"input[type='radio'][value='{str(value).lower()}']").check(
            force=True
        )

    def set_type_evenement(self, value):
        self.page.locator("#radio-id_type_evenement").locator(
            f"input[type='radio'][value='{str(value).lower()}']"
        ).check(force=True)

    def set_analyses(self, value):
        self.page.locator("#radio-id_analyses_sur_les_malades").locator(
            f"input[type='radio'][value='{str(value).lower()}']"
        ).check(force=True)

    def fill_required_fields(self, object: InvestigationTiac):
        self.contenu.fill(object.contenu)
        self.set_type_evenement(object.type_evenement)

    def add_agent_pathogene_confirme(self, label):
        self.page.locator("#agents-pathogene").evaluate("el => el.scrollIntoView()")
        self._set_treeselect_option("agents-pathogene", label)

    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")

    def find_label_for_danger(self, text):
        return self.current_modal.get_by_text(text[:25])

    def open_danger_modal(self):
        self.page.get_by_test_id("add-etiologie").click()

    def add_danger_syndromique(self, text):
        self.open_danger_modal()
        self.find_label_for_danger(text).click()
        self.current_modal.get_by_role("button", name="Vérifier").click()
        self.current_modal.get_by_role("button", name="Confirmer").click()

    def add_repas(self, repas: RepasSuspect):
        self.page.get_by_test_id("add-repas").click()

        for field in ["denomination", "menu", "nombre_participant"]:
            self.current_modal.locator(f'[id$="{field}"]').fill(str(getattr(repas, field)))

        for motif in repas.motif_suspicion:
            self.current_modal.locator(f'input[type="checkbox"][value="{motif}"]').check(force=True)

        self.current_modal.locator('[id$="-datetime_repas"]').fill(repas.datetime_repas.strftime("%Y-%m-%dT%H:%M"))
        self.current_modal.locator('[id$="-departement"]').select_option(f"{repas.departement}")
        self.current_modal.locator('[id$="type_repas"]').select_option(f"{repas.type_repas}")
        if repas.type_repas == TypeRepas.RESTAURATION_COLLECTIVE:
            self.current_modal.locator('[id$="type_collectivite"]').select_option(f"{repas.type_collectivite}")

        self.current_modal.get_by_role("button", name="Enregistrer").click()

    def add_aliment_simple(self, aliment: AlimentSuspect):
        self.page.get_by_test_id("add-aliment").click()

        self.page.locator("#categorie-produit").evaluate("el => el.scrollIntoView()")
        self._set_treeselect_option("categorie-produit", aliment.get_categorie_produit_display())
        self.current_modal.get_by_label("Aliment simple/ingrédient").click(force=True)

        for field in ["denomination", "description_produit"]:
            self.current_modal.locator(f'[id$="{field}"]').fill(str(getattr(aliment, field)))

        for motif in aliment.motif_suspicion:
            checkbox = self.current_modal.locator(f'input[type="checkbox"][value="{motif}"]')
            self.current_modal.locator(f'label[for="{checkbox.get_attribute("id")}"]').click()

        self.current_modal.get_by_role("button", name="Enregistrer").click()

    def add_aliment_cuisine(self, aliment: AlimentSuspect):
        self.page.get_by_test_id("add-aliment").click()

        self.current_modal.get_by_label("Aliment cuisiné").click(force=True)

        for field in ["denomination", "description_composition"]:
            self.current_modal.locator(f'[id$="{field}"]').fill(str(getattr(aliment, field)))

        for motif in aliment.motif_suspicion:
            checkbox = self.current_modal.locator(f'input[type="checkbox"][value="{motif}"]')
            self.current_modal.locator(f'label[for="{checkbox.get_attribute("id")}"]').click()

        self.current_modal.get_by_role("button", name="Enregistrer").click()

    def get_repas_card(self, card_index):
        return self.page.locator(".modal-repas-container").all()[card_index].locator(".repas-card")

    def get_aliment_card(self, card_index):
        return self.page.locator(".modal-aliment-container").all()[card_index].locator(".aliment-card")

    def edit_repas(self, index, **kwargs):
        card = self.get_repas_card(index)
        card.locator(".modify-button").click()

        for k, v in kwargs.items():
            self.page.locator(".repas-modal").locator("visible=true").locator(f'[id$="{k}"]').fill(v)

        self.current_modal.get_by_role("button", name="Enregistrer").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    def edit_aliment(self, index, **kwargs):
        card = self.get_aliment_card(index)
        card.locator(".modify-button").click()

        for k, v in kwargs.items():
            self.page.locator(".aliment-modal").locator("visible=true").locator(f'[id$="{k}"]').fill(v)

        self.current_modal.get_by_role("button", name="Enregistrer").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    def delete_danger_syndromique(self, index):
        self.page.locator(".etiologie-card-container").locator("visible=true").nth(index).get_by_role(
            "button", name="Supprimer"
        ).click()

    def delete_repas(self, index):
        self.page.locator(".repas-card").nth(index).get_by_role("button", name="Supprimer").click()
        self.current_modal.get_by_role("button", name="Supprimer").click()

    def delete_aliment(self, index):
        self.page.locator(".aliment-card").nth(index).get_by_role("button", name="Supprimer").click()
        self.current_modal.get_by_role("button", name="Supprimer").click()

    @property
    def nb_dangers(self):
        return self.page.locator(".etiologie-card-container").locator("visible=true").count()

    @property
    def nb_repas(self):
        return self.page.locator(".repas-card").locator("visible=true").count()

    @property
    def nb_aliments(self):
        return self.page.locator(".aliment-card").locator("visible=true").count()

    def submit_as_draft(self):
        self.page.get_by_role("button", name="Enregistrer le brouillon").click()

    def add_free_link(self, numero, choice_js_fill, link_label="Investigation de tiac : "):
        choice_js_fill(self.page, "#liens-libre .choices", str(numero), link_label + str(numero))


class InvestigationTiacDetailsPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

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
    def origin(self):
        return self.page.get_by_test_id("origin")

    @property
    def modalite(self):
        return self.page.get_by_test_id("modalite")

    @property
    def cas_block(self):
        return self.page.get_by_role("heading", name="Cas").locator("..")

    @property
    def etiologie_block(self):
        return self.page.get_by_role("heading", name="Étiologie").locator("..")

    def navigate(self, object):
        return self.page.goto(f"{self.base_url}{object.get_absolute_url()}")

    def delete(self):
        self.page.get_by_role("button", name="Actions").click()
        self.page.get_by_test_id("delete-nav").click()
        self.page.get_by_test_id("submit-delete-modal").click()

    def cloturer(self):
        self.page.get_by_role("button", name="Actions").click()
        self.page.get_by_role("link", name="Clôturer l'investigation").click()
        self.page.get_by_role("button", name="Clôturer").click()

    def etablissement_card(self, index=0):
        return self.page.locator(".etablissement-card").nth(index)

    def aliment_card(self, index=0):
        return self.page.locator(".aliment-card").nth(index)

    def repas_card(self, index=0):
        return self.page.locator(".repas-card").nth(index)

    def analyse_card(self, index=0):
        return self.page.locator(".analyse-card").nth(index)

    def etablissement_open_modal(self, index=0):
        return self.etablissement_card(index).get_by_text("Voir le détail", exact=True).click()

    def aliment_open_modal(self, index=0):
        return self.aliment_card(index).get_by_text("Voir le détail", exact=True).click()

    def repas_open_modal(self, index=0):
        return self.repas_card(index).get_by_text("Voir le détail", exact=True).click()

    def analyse_open_modal(self, index=0):
        return self.analyse_card(index).get_by_text("Voir le détail", exact=True).click()

    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")
