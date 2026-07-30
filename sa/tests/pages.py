import contextlib
from functools import cached_property
import json

from django.urls import reverse
from playwright.sync_api import Page

from core.tests.pages import ChoiceJSPage
from sa.models import EvenementAnimal
from seves import settings


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
        if not config:
            response_body = [
                {
                    "codesPostaux": ["59000", "59160", "59260", "59777", "59800"],
                    "nom": "Lille",
                    "code": "59350",
                    "_score": 1.8082078747980779,
                    "departement": {"code": "59", "nom": "Nord"},
                }
            ]
            config = {
                "search_text": "Lille",
                "option_name": f"Lille ({response_body[0]['codesPostaux'][0]})",
                "response_body": json.dumps(response_body),
            }

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


class EvenementAnimalFormPage(WithPreCreationFormPage, WithAddressAndCommuneUtils):
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
        "type_lieu",
        "numero_identifiant",
        "coordinates_0",  # Lat
        "coordinates_1",  # Long
        "context_suspicion",
        "date_first_symptoms",
        "description",
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

    def fill_coordinates(self, point):
        self.coordinates_1.fill(str(point.x))
        self.coordinates_0.fill(str(point.y))

    @property
    def particulier_label(self):
        return self.page.locator("label", has_text="Particulier")

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

    def submit(self):
        self.page.get_by_role("button", name="Enregistrer", exact=True).click()
        redirect = reverse("sa:evenement-animal-details", kwargs={"numero": "*"})
        self.page.wait_for_url(f"**{redirect}")

    def fill_context_block(self, evenement):
        self.context_suspicion.select_option(evenement.context_suspicion)
        self.date_first_symptoms.fill(evenement.date_first_symptoms.strftime("%Y-%m-%d"))
        self.description.fill(evenement.description)
        self.page.locator("#context label", has_text=evenement.get_human_involved_display()).click()

    def fill_detenteur_etablissement_block(self, evenement):
        self.numero_identifiant_etablissement.fill(evenement.numero_identifiant_etablissement)
        self.raison_sociale_etablissement.fill(evenement.raison_sociale_etablissement)
        self.departement_etablissement.select_option(str(evenement.departement_etablissement))
        self.autre_identifiant_etablissement.fill(evenement.autre_identifiant_etablissement)
        self.adresse_lieu_dit_etablissement.fill(evenement.adresse_lieu_dit_etablissement)
        self.code_insee_etablissement.fill(evenement.code_insee_etablissement)
        self.siret_etablissement.fill(evenement.siret_etablissement)
        self.commune_etablissement.fill(evenement.commune_etablissement)
        self.pays_etablissement.select_option(evenement.pays_etablissement.code)

    def fill_detenteur_particulier_block(self, evenement):
        self.particulier_label.click()

        self.nom_particulier.fill(evenement.nom_particulier)
        self.prenom_particulier.fill(evenement.prenom_particulier)
        self.adresse_particulier.fill(evenement.adresse_particulier)
        self.commune_particulier.fill(evenement.commune_particulier)
        self.departement_particulier.select_option(str(evenement.departement_particulier))
        self.code_insee_particulier.fill(evenement.code_insee_particulier)
        self.email_particulier.fill(evenement.email_particulier)
        self.telephone_particulier.fill(evenement.telephone_particulier)
