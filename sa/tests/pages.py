import contextlib
from functools import cached_property
import json

from django.urls import reverse
from playwright.sync_api import Locator, Page

from core.pages import WithActionsPage
from core.tests.pages import ChoiceJSPage, TreeselectPage
from sa.models import Analyse, EvenementAnimal, Veterinaire
from seves import settings


def _default_lille_commune_config():
    response_body = [
        {
            "codesPostaux": ["59000", "59160", "59260", "59777", "59800"],
            "nom": "Lille",
            "code": "59350",
            "_score": 1.8082078747980779,
            "departement": {"code": "59", "nom": "Nord"},
        }
    ]
    return {
        "search_text": "Lille",
        "option_name": f"Lille ({response_body[0]['codesPostaux'][0]})",
        "response_body": json.dumps(response_body),
    }


class WithAddressAndCommuneUtils:
    def __init__(self, page: Page, *args, **kwargs):
        self.page = page

    @cached_property
    def _address_choicejs(self):
        return ChoiceJSPage(self.page, self.page.get_by_test_id("ban-search"))

    @cached_property
    def _commune_choicejs(self):
        return ChoiceJSPage(self.page, self.page.get_by_test_id("communes-search"))

    @contextlib.contextmanager
    def mock_ban(self):
        ban_url = f"{settings.GEOCODE_URL}/search/?*"
        self.page.route(
            ban_url,
            lambda route: route.fulfill(
                status=200, content_type="application/json", body="""{"type": "FeatureCollection","features": []}"""
            ),
        )
        yield
        self.page.unroute(ban_url)

    def fill_address(self, exact_name, *, search=None):
        self._address_choicejs.try_select_option(exact_name, search=search)

    def force_address(self, address: str):
        with self.mock_ban():
            self.fill_address(f"{address} (Forcer la valeur)", search=address)

    def force_commune(self, config=None):
        config = config or _default_lille_commune_config()

        url = f"https://geo.api.gouv.fr/communes?nom={config['search_text']}&fields=departement,codesPostaux&boost=population&limit=15"

        self.page.route(
            url,
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=config["response_body"],
            ),
        )

        self._commune_choicejs.try_select_option(config["option_name"], search=config["search_text"])
        self.page.unroute(url)


class WithEtablissementDetenteurUtils:
    def __init__(self, page: Page, *args, **kwargs):
        self.page = page

    @cached_property
    def _address_etablissement_choicejs(self):
        return ChoiceJSPage(self.page, self.page.get_by_test_id("ban-search-etablissement"))

    @cached_property
    def _commune_etablissement_choicejs(self):
        return ChoiceJSPage(self.page, self.page.get_by_test_id("communes-search-etablissement"))

    @cached_property
    def _siret_choicejs(self):
        return ChoiceJSPage(self.page, self.page.get_by_test_id("siret-etablissement"))

    def force_address_etablissement(self, address: str):
        with self.mock_ban():
            self._address_etablissement_choicejs.try_select_option(f"{address} (Forcer la valeur)", search=address)

    def force_commune_etablissement(self, config=None):
        config = config or _default_lille_commune_config()

        url = f"https://geo.api.gouv.fr/communes?nom={config['search_text']}&fields=departement,codesPostaux&boost=population&limit=15"

        self.page.route(
            url,
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=config["response_body"],
            ),
        )

        self._commune_etablissement_choicejs.try_select_option(config["option_name"], search=config["search_text"])
        self.page.unroute(url)

    def fill_siret_etablissement(self, exact_siret, *, search=None):
        self._siret_choicejs.try_select_option(exact_siret, search=search)

    def force_siret_etablissement(self, siret: str):
        self.fill_siret_etablissement(f"{siret} (Forcer la valeur)", search=siret)


class WithParticulierDetenteurUtils:
    def __init__(self, page: Page, *args, **kwargs):
        self.page = page

    @cached_property
    def _address_particulier_choicejs(self):
        return ChoiceJSPage(self.page, self.page.get_by_test_id("ban-search-particulier"))

    @cached_property
    def _commune_particulier_choicejs(self):
        return ChoiceJSPage(self.page, self.page.get_by_test_id("communes-search-particulier"))

    def force_address_particulier(self, address: str):
        with self.mock_ban():
            self._address_particulier_choicejs.try_select_option(f"{address} (Forcer la valeur)", search=address)

    def force_commune_particulier(self, config=None):
        config = config or _default_lille_commune_config()

        url = f"https://geo.api.gouv.fr/communes?nom={config['search_text']}&fields=departement,codesPostaux&boost=population&limit=15"

        self.page.route(
            url,
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=config["response_body"],
            ),
        )

        self._commune_particulier_choicejs.try_select_option(config["option_name"], search=config["search_text"])
        self.page.unroute(url)


class WithAnalyseMixin:
    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")

    def get_analyse_card(self, index=0):
        return self.page.locator(".analyse-card").nth(index)

    @property
    def add_analyse_button(self):
        return self.page.locator(".analyses-fieldset").get_by_role("button", name="Ajouter")

    def open_analyse_modal(self):
        self.add_analyse_button.click()
        self.current_modal.wait_for(state="visible")
        return self.current_modal

    def fill_analyse(self, modal: Locator, analyse: Analyse):
        modal.locator('[id$="-maladie"]').select_option(str(analyse.maladie_id))
        modal.locator('[id$="date_prelevement"]').fill(analyse.date_prelevement.strftime("%Y-%m-%d"))
        if analyse.date_resultat:
            modal.locator('[id$="date_resultat"]').fill(analyse.date_resultat.strftime("%Y-%m-%d"))
        modal.locator('[id$="-laboratoire"]').select_option(str(analyse.laboratoire_id))
        modal.locator('[id$="-methode"]').select_option(str(analyse.methode_id))
        modal.locator('[id$="-resultat"]').select_option(analyse.resultat)
        if analyse.resultat_confirmation:
            modal.locator('[id$="resultat_confirmation"]').check(force=True)

    def close_analyse_modal(self):
        self.current_modal.locator(".save-btn").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    def add_analyse(self, analyse: Analyse):
        modal = self.open_analyse_modal()
        self.fill_analyse(modal, analyse)
        self.close_analyse_modal()

    def delete_analyse(self, index=0):
        self.get_analyse_card(index).get_by_role("button", name="Supprimer").click()
        self.current_modal.get_by_role("button", name="Supprimer").click()

    def edit_analyse(self, index=0, **kwargs):
        card = self.get_analyse_card(index)
        card.locator(".modify-button").click()

        for k, v in kwargs.items():
            self.page.locator(".analyse-modal").locator("visible=true").locator(f'[id$="{k}"]').fill(v)

        self.current_modal.get_by_role("button", name="Enregistrer").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    @property
    def nb_analyse(self):
        return self.page.locator(".analyse-card").locator("visible=true").count()


class WithVeterinaireMixin:
    @property
    def current_modal(self):
        return self.page.locator(".fr-modal__body").locator("visible=true")

    def get_veterinaire_card(self, index=0):
        return self.page.locator(".veterinaire-card").nth(index)

    @property
    def add_veterinaire_button(self):
        return self.page.locator(".veterinaires-fieldset").get_by_role("button", name="Ajouter")

    def open_veterinaire_modal(self):
        self.add_veterinaire_button.click()
        self.current_modal.wait_for(state="visible")
        return self.current_modal

    def force_address_veterinaire(self, modal: Locator, address: str):
        with self.mock_ban():
            ChoiceJSPage(self.page, modal.get_by_test_id("ban-search-veterinaire")).try_select_option(
                f"{address} (Forcer la valeur)", search=address
            )

    def force_commune_veterinaire(self, modal: Locator, config=None):
        config = config or _default_lille_commune_config()

        url = f"https://geo.api.gouv.fr/communes?nom={config['search_text']}&fields=departement,codesPostaux&boost=population&limit=15"

        self.page.route(
            url,
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=config["response_body"],
            ),
        )

        ChoiceJSPage(self.page, modal.get_by_test_id("communes-search-veterinaire")).try_select_option(
            config["option_name"], search=config["search_text"]
        )
        self.page.unroute(url)

    def fill_veterinaire(self, modal: Locator, veterinaire: Veterinaire):
        modal.locator(f'input[type="radio"][value="{veterinaire.type_veterinaire}"]').check(force=True)
        modal.locator('[id$="-nom_structure"]').fill(veterinaire.nom_structure)
        modal.locator('[id$="-numero_dpe"]').fill(veterinaire.numero_dpe)
        self.force_address_veterinaire(modal, veterinaire.adresse_lieu_dit)
        self.force_commune_veterinaire(modal)
        if veterinaire.departement_id:
            modal.locator('[id$="-departement"]').select_option(str(veterinaire.departement))
        modal.locator('[id$="-telephone_structure"]').fill(veterinaire.telephone_structure)
        modal.locator('[id$="-courriel_structure"]').fill(veterinaire.courriel_structure)
        modal.locator('[id$="-nom"]').fill(veterinaire.nom)
        modal.locator('[id$="-prenom"]').fill(veterinaire.prenom)
        modal.locator('[id$="-telephone"]').fill(veterinaire.telephone)
        modal.locator('[id$="-courriel"]').fill(veterinaire.courriel)

    def close_veterinaire_modal(self):
        self.current_modal.locator(".save-btn").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    def add_veterinaire(self, veterinaire: Veterinaire):
        modal = self.open_veterinaire_modal()
        self.fill_veterinaire(modal, veterinaire)
        self.close_veterinaire_modal()

    def delete_veterinaire(self, index=0):
        self.get_veterinaire_card(index).get_by_role("button", name="Supprimer").click()
        self.current_modal.get_by_role("button", name="Supprimer").click()

    def edit_veterinaire(self, index=0, **kwargs):
        card = self.get_veterinaire_card(index)
        card.locator(".modify-button").click()

        for k, v in kwargs.items():
            self.page.locator(".veterinaire-modal").locator("visible=true").locator(f'[id$="{k}"]').fill(v)

        self.current_modal.get_by_role("button", name="Enregistrer").click()
        self.current_modal.wait_for(state="hidden", timeout=2_000)

    @property
    def nb_veterinaire(self):
        return self.page.locator(".veterinaire-card").locator("visible=true").count()


class WithEspecesConcerneesMixin:
    @property
    def especes_concernees_rows(self):
        return self.page.locator("#especes-concernees-table tbody tr")

    def get_espece_concernee_row(self, index=0):
        return self.especes_concernees_rows.nth(index)

    @property
    def add_espece_concernee_button(self):
        return self.page.locator("#especes-concernees").get_by_role("button", name="Ajouter")

    def add_espece_concernee(self):
        self.add_espece_concernee_button.click()

    def fill_espece_concernee(self, index, espece=None, **fields):
        row = self.get_espece_concernee_row(index)
        if espece is not None:
            row.locator('select[id$="-espece"]').select_option(str(espece.pk))
        for field_name, value in fields.items():
            row.locator(f'[id$="-{field_name}"]').fill(str(value))

    def delete_espece_concernee(self, index):
        self.get_espece_concernee_row(index).get_by_role("button", name="Supprimer").click()

    @property
    def nb_especes_concernees(self):
        return self.especes_concernees_rows.locator("visible=true").count()


class WithPreCreationFormPage:
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url
        self._maladie_treeselect = TreeselectPage(
            self.page, self.page.locator("#fr-treeselect-id_pre_creation_maladie")
        )

    @property
    def pre_creation_modal(self):
        return self.page.locator("#modal-pre-creation")

    def open_pre_creation_form(self):
        self.page.get_by_role("button", name="Créer un évènement", exact=True).click()

    def set_statut_animal(self, value):
        self.page.locator("#radio-id_pre_creation_statut_animal").locator(
            f"input[type='radio'][value='{str(value).lower()}' i]"
        ).check(force=True)

    def fill_maladie(self, evenement):
        group = "Les plus fréquentes" if evenement.maladie.is_highlighted else "Autre"
        self._maladie_treeselect.check_option(group, evenement.maladie.name_with_acronym)

    def fill_pre_creation_form(self, evenement: EvenementAnimal):
        self.fill_maladie(evenement)
        self.pre_creation_modal.get_by_label("Espece").select_option(evenement.espece.name)
        self.set_statut_animal(evenement.statut_animal)
        self.pre_creation_modal.get_by_role("button", name="Suivant >", exact=True).click()


class EvenementListPage(WithPreCreationFormPage):
    def __init__(self, page: Page, base_url):
        super().__init__(page, base_url)
        self.page = page
        self.base_url = base_url

    def navigate(self):
        self.page.goto(f"{self.base_url}{reverse('sa:evenement-liste')}")

    @property
    def search_form(self):
        return self.page.locator("#search-form")

    @property
    def annee_field(self):
        return self.search_form.get_by_label("Année")

    @property
    def numero_field(self):
        return self.search_form.get_by_label("N° événement")

    @property
    def maladie_field(self):
        return self.search_form.get_by_label("Maladie")

    @property
    def espece_field(self):
        return self.search_form.get_by_label("Espèce")

    @property
    def etat_field(self):
        return self.search_form.get_by_label("État de l'événement")

    def submit_search(self):
        self.page.get_by_role("button", name="Rechercher").click()

    def reset_search(self):
        self.page.get_by_role("button", name="Effacer", exact=True).click()

    def row(self, numero):
        return self.page.locator(".evenements__list-row").filter(has_text=numero)


class EvenementAnimalFormPage(
    WithPreCreationFormPage,
    WithAddressAndCommuneUtils,
    WithEtablissementDetenteurUtils,
    WithParticulierDetenteurUtils,
    WithAnalyseMixin,
    WithVeterinaireMixin,
    WithEspecesConcerneesMixin,
):
    fields = [
        "statut_evenement",
        "date_statut_changed",
        # Détenteur - Etablissement
        "numero_identifiant_etablissement",
        "raison_sociale_etablissement",
        "departement_etablissement",
        "autre_identifiant_etablissement",
        "adresse_lieu_dit_etablissement",
        "code_insee_etablissement",
        "siret_etablissement",
        "commune_etablissement",
        "pays_etablissement",
        # Détenteur - Particulier
        "nom_particulier",
        "prenom_particulier",
        "adresse_particulier",
        "commune_particulier",
        "departement_particulier",
        "code_insee_particulier",
        "email_particulier",
        "telephone_particulier",
        # Localisation
        "adresse_lieu_dit",
        "commune",
        "code_insee",
        "type_lieu",
        "numero_identifiant",
        "coordinates_0",  # Lat
        "coordinates_1",  # Long
        "context_suspicion",
        "date_first_symptoms",
        "description",
        # Mesures de gestions
        "date_apms",
        "date_apdi",
        "date_levee",
        "date_d_zero",
        "date_nd1",
        "date_nd2",
        # Adis
        "numero_adis",
        "date_notification_adis",
        "date_cloture_adis",
        "effectif_retenu",
        "origine_infection",
    ]

    def __init__(self, page: Page, base_url):
        super().__init__(page, base_url)
        self.page = page
        self.base_url = base_url
        for field in self.fields:
            setattr(self, field, page.locator(f"#id_{field}"))

    def navigate(self, maladie, espece, statut):
        self.page.goto(
            f"{self.base_url}{reverse('sa:evenement-animal-creation')}?maladie={maladie.pk}&espece={espece.pk}&statut_animal={statut}"
        )

    @property
    def cancel_link(self):
        return self.page.get_by_role("link", name="Annuler", exact=True)

    def cancel(self, wait_for=None):
        self.cancel_link.click()
        if wait_for:
            self.page.wait_for_url(wait_for)

    def fill_coordinates(self, point):
        self.coordinates_1.fill(str(point.x))
        self.coordinates_0.fill(str(point.y))

    @property
    def parcelles_checkbox(self):
        return self.page.locator("#map-parcelles-checkbox")

    @property
    def parcelles_message(self):
        return self.page.locator("#map-parcelles-message")

    @property
    def map_canvas(self):
        return self.page.locator('[data-map-target="mapDisplay"] canvas')

    @property
    def particulier_label(self):
        return self.page.locator("label", has_text="Particulier")

    @property
    def etablissement_label(self):
        return self.page.locator("label", has_text="Établissement")

    @property
    def type_change_modal(self):
        return self.page.locator("#detenteur-type-change-modal")

    def confirm_type_change(self):
        self.type_change_modal.get_by_role("button", name="Continuer").click()

    def cancel_type_change(self):
        self.type_change_modal.get_by_role("button", name="Annuler").click()

    @property
    def reprendre_adresse_detenteur_btn(self):
        return self.page.get_by_test_id("reprendre-adresse-detenteur-btn")

    def fill_required_fields(self, evenement: EvenementAnimal):
        self.statut_evenement.select_option(evenement.statut_evenement)
        self.date_statut_changed.fill(evenement.date_statut_changed.strftime("%Y-%m-%d"))
        self.fill_coordinates(evenement.coordinates)
        self.type_lieu.select_option(evenement.get_type_lieu_display())

        if evenement.numero_identifiant_etablissement:
            self.numero_identifiant_etablissement.fill(evenement.numero_identifiant_etablissement)
        elif evenement.nom_particulier:
            self.particulier_label.click()
            self.nom_particulier.fill(evenement.nom_particulier)
        else:
            raise ValueError(
                "You need either a numero_identifiant_etablissement or a nom_particulier to fill required fields"
            )

    def submit_as_draft(self, wait_for="**/sa/evenement-animal/**/"):
        self.page.get_by_role("button", name="Enregistrer le brouillon", exact=True).click()
        if wait_for:
            self.page.wait_for_url(wait_for)

    def publish(self):
        self.page.get_by_role("button", name="Publier", exact=True).click()
        self.page.wait_for_url("**/sa/evenement-animal/**/")

    def fill_context_block(self, evenement):
        self.context_suspicion.select_option(evenement.context_suspicion)
        self.date_first_symptoms.fill(evenement.date_first_symptoms.strftime("%Y-%m-%d"))
        self.description.fill(evenement.description)
        self.page.locator("#context label", has_text=evenement.get_human_involved_display()).click()

    @property
    def adis_block(self):
        return self.page.locator("#adis")

    def fill_adis_block(self, evenement, choice_js_fill):
        self.adis_block.locator(f"input[type='radio'][value='{str(evenement.foyer).lower()}' i]").check(force=True)

        self.numero_adis.fill(evenement.numero_adis)
        self.date_notification_adis.fill(evenement.date_notification_adis.strftime("%Y-%m-%d"))
        self.date_cloture_adis.fill(evenement.date_cloture_adis.strftime("%Y-%m-%d"))
        self.effectif_retenu.fill(str(evenement.effectif_retenu))
        self.origine_infection.select_option(evenement.origine_infection)

        for value in evenement.mesures_controle_labels.split(", "):
            choice_js_fill(self.page, "#adis .choices__list", value, value)

    def fill_detenteur_etablissement_block(self, evenement):
        self.numero_identifiant_etablissement.fill(evenement.numero_identifiant_etablissement)
        self.raison_sociale_etablissement.fill(evenement.raison_sociale_etablissement)
        self.autre_identifiant_etablissement.fill(evenement.autre_identifiant_etablissement)

        self.force_siret_etablissement(evenement.siret_etablissement)
        self.force_address_etablissement(evenement.adresse_lieu_dit_etablissement)
        self.force_commune_etablissement()
        self.code_insee_etablissement.fill(evenement.code_insee_etablissement)
        self.departement_etablissement.select_option(str(evenement.departement_etablissement))
        self.pays_etablissement.select_option(evenement.pays_etablissement.code)

    def fill_detenteur_particulier_block(self, evenement):
        self.particulier_label.click()

        self.nom_particulier.fill(evenement.nom_particulier)
        self.prenom_particulier.fill(evenement.prenom_particulier)

        self.force_address_particulier(evenement.adresse_particulier)
        self.force_commune_particulier()
        self.departement_particulier.select_option(str(evenement.departement_particulier))
        self.code_insee_particulier.fill(evenement.code_insee_particulier)
        self.email_particulier.fill(evenement.email_particulier)
        self.telephone_particulier.fill(evenement.telephone_particulier)


class EvenementAnimalDetailsPage(WithActionsPage):
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, evenement: EvenementAnimal):
        self.page.goto(f"{self.base_url}{evenement.get_absolute_url()}")

    @property
    def title(self):
        return self.page.locator(".details-top-row h1").nth(0)

    @property
    def etat_badge(self):
        return self.page.get_by_test_id("evenement-header").locator(".fr-badge").nth(0)

    @property
    def statut_evenement_badge(self):
        return self.page.get_by_test_id("evenement-header").locator(".fr-badge").nth(1)

    def block(self, title):
        return self.page.get_by_role("heading", name=title, exact=True).locator("..")

    def publish(self):
        self.page.get_by_role("button", name="Publier", exact=True).click()
        self.page.wait_for_url("**/sa/evenement-animal/**/")

    def get_analyse_card(self, index=0):
        return self.page.locator(".analyse-card").nth(index)

    @property
    def nb_analyse(self):
        return self.page.locator(".analyse-card").count()

    def open_analyse_detail(self, index=0):
        self.get_analyse_card(index).get_by_role("button", name="Voir le détail").click()
        modal = self.page.locator(".fr-modal__body").locator("visible=true")
        modal.wait_for(state="visible")
        return modal

    def get_veterinaire_card(self, index=0):
        return self.page.locator(".veterinaire-card").nth(index)

    @property
    def nb_veterinaire(self):
        return self.page.locator(".veterinaire-card").count()

    def open_veterinaire_detail(self, index=0):
        self.get_veterinaire_card(index).get_by_role("button", name="Voir le détail").click()
        modal = self.page.locator(".fr-modal__body").locator("visible=true")
        modal.wait_for(state="visible")
        return modal

    def get_especes_concernees_values(self):
        block = self.block("Espèces concernées et exposées")
        texts = []
        for row in block.locator("tbody tr").all():
            texts.append([t.strip() for t in row.locator("td").all_text_contents()])

        return texts
