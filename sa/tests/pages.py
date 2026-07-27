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
        "type_lieu",
        "numero_identifiant",
        "coordinates_0",  # Lat
        "coordinates_1",  # Long
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

    def fill_required_fields(self, evenement: EvenementAnimal):
        self.statut_evenement.select_option(evenement.statut_evenement)
        self.date_statut_changed.fill(evenement.date_statut_changed.strftime("%Y-%m-%d"))
        self.fill_coordinates(evenement.coordinates)
        self.type_lieu.select_option(evenement.get_type_lieu_display())

    def submit(self):
        self.page.get_by_role("button", name="Enregistrer", exact=True).click()
        redirect = reverse("sa:evenement-animal-details", kwargs={"numero": "*"})
        self.page.wait_for_url(f"**{redirect}")
