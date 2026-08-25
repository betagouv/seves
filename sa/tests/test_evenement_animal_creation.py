import json

from playwright.sync_api import Page, expect

from sa.models import EvenementAnimal
from sa.tests.factories import EspeceFactory, EvenementAnimalFactory, MaladieFactory
from sa.tests.pages import EvenementAnimalFormPage, EvenementListPage
from seves import settings


def test_can_create_evenement_animal_with_required_fields_only_from_list_page(
    live_server, mocked_authentification_user, page: Page
):
    input_data = EvenementAnimalFactory()
    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.open_pre_creation_form()
    list_page.fill_pre_creation_form(input_data)

    list_page.page.wait_for_url("**/sa/evenement-animal/creation**")
    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.fill_required_fields(input_data)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.maladie == input_data.maladie
    assert evenement_produit.espece == input_data.espece
    assert evenement_produit.statut_animal == input_data.statut_animal
    assert evenement_produit.statut_evenement == input_data.statut_evenement
    assert evenement_produit.date_statut_changed == input_data.date_statut_changed
    assert evenement_produit.type_lieu == input_data.type_lieu
    assert evenement_produit.coordinates == input_data.coordinates


def test_can_create_evenement_animal_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.maladie == maladie
    assert evenement_produit.espece == espece
    assert evenement_produit.statut_animal == input_data.statut_animal
    assert evenement_produit.statut_evenement == input_data.statut_evenement
    assert evenement_produit.date_statut_changed == input_data.date_statut_changed


def test_can_create_evenement_animal_with_localisation_block(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.force_address(input_data.adresse_lieu_dit)
    creation_page.force_commune()
    creation_page.numero_identifiant.fill(input_data.numero_identifiant)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.adresse_lieu_dit == input_data.adresse_lieu_dit
    assert evenement_produit.commune == "Lille"
    assert evenement_produit.code_insee == "59350"
    assert evenement_produit.numero_identifiant == input_data.numero_identifiant
    assert evenement_produit.type_lieu == input_data.type_lieu
    assert evenement_produit.coordinates == input_data.coordinates


def test_can_create_evenement_animal_with_ban_auto_complete(
    live_server, page: Page, ensure_departements, choice_js_fill_from_element
):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    ensure_departements("Paris")
    call_count = {"count": 0}

    def handle(route):
        response = {
            "type": "FeatureCollection",
            "features": [
                {
                    "geometry": {"type": "Point", "coordinates": [2.304014, 48.840234]},
                    "properties": {
                        "label": "251 Rue de Vaugirard 75015 Paris",
                        "name": "251 Rue de Vaugirard",
                        "citycode": "75115",
                        "postcode": "75015",
                        "city": "Paris",
                        "context": "75, Paris, Île-de-France",
                    },
                },
            ],
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(response))
        call_count["count"] += 1

    creation_page.page.route(
        f"{settings.GEOCODE_URL}/search/?q=251%20Rue%20de%20Vaugirard&limit=15",
        handle,
    )
    choice_js_fill_from_element(
        page,
        creation_page.page.get_by_test_id("ban-search"),
        "251 Rue de Vaugirard",
        "251 Rue de Vaugirard 75015 Paris",
    )
    assert call_count["count"] == 1
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.adresse_lieu_dit == "251 Rue de Vaugirard"
    assert evenement_produit.commune == "Paris"
    assert evenement_produit.code_insee == "75115"


def test_can_create_evenement_animal_with_context_block(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_context_block(input_data)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.context_suspicion == input_data.context_suspicion
    assert evenement_produit.date_first_symptoms == input_data.date_first_symptoms
    assert evenement_produit.description == input_data.description
    assert evenement_produit.human_involved == input_data.human_involved


def test_can_create_evenement_animal_with_detenteur_etablissement_block(live_server, page: Page):
    input_data = EvenementAnimalFactory()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_detenteur_etablissement_block(input_data)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    fields = [
        "numero_identifiant_etablissement",
        "raison_sociale_etablissement",
        "departement_etablissement",
        "adresse_lieu_dit_etablissement",
        "code_insee_etablissement",
        "siret_etablissement",
        "commune_etablissement",
        "pays_etablissement",
    ]
    for field in fields:
        assert getattr(evenement_produit, field) == getattr(input_data, field)


def test_can_create_evenement_animal_with_detenteur_particulier_block(live_server, page: Page):
    input_data = EvenementAnimalFactory(particulier=True)
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_detenteur_particulier_block(input_data)
    creation_page.submit()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    fields = [
        "nom_particulier",
        "prenom_particulier",
        "adresse_particulier",
        "commune_particulier",
        "departement_particulier",
        "code_insee_particulier",
        "email_particulier",
        "telephone_particulier",
    ]
    for field in fields:
        assert getattr(evenement_produit, field) == getattr(input_data, field)


def test_no_confirmation_modal_when_switching_detenteur_type_without_data(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    creation_page.particulier_label.click()

    expect(creation_page.type_change_modal).not_to_be_visible()
    expect(creation_page.nom_particulier).to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_be_hidden()


def test_confirmation_modal_when_switching_from_etablissement_to_particulier_with_data(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.numero_identifiant_etablissement.fill(input_data.numero_identifiant_etablissement)
    creation_page.raison_sociale_etablissement.fill(input_data.raison_sociale_etablissement)

    creation_page.particulier_label.click()

    expect(creation_page.type_change_modal).to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_be_visible()


def test_cancelling_detenteur_type_change_keeps_current_type_and_data(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.numero_identifiant_etablissement.fill(input_data.numero_identifiant_etablissement)
    creation_page.raison_sociale_etablissement.fill(input_data.raison_sociale_etablissement)

    creation_page.particulier_label.click()
    creation_page.cancel_type_change()

    expect(creation_page.type_change_modal).not_to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_have_value(input_data.numero_identifiant_etablissement)
    expect(creation_page.raison_sociale_etablissement).to_have_value(input_data.raison_sociale_etablissement)


def test_confirming_detenteur_type_change_clears_previous_block_data(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.numero_identifiant_etablissement.fill(input_data.numero_identifiant_etablissement)
    creation_page.raison_sociale_etablissement.fill(input_data.raison_sociale_etablissement)

    creation_page.particulier_label.click()
    creation_page.confirm_type_change()

    expect(creation_page.type_change_modal).not_to_be_visible()
    expect(creation_page.nom_particulier).to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_be_hidden()
    expect(creation_page.numero_identifiant_etablissement).to_have_value("")
    expect(creation_page.raison_sociale_etablissement).to_have_value("")


def test_confirmation_modal_when_switching_from_particulier_to_etablissement_with_data(live_server, page: Page):
    input_data = EvenementAnimalFactory.build(particulier=True)
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.particulier_label.click()
    creation_page.nom_particulier.fill(input_data.nom_particulier)

    creation_page.etablissement_label.click()

    expect(creation_page.type_change_modal).to_be_visible()

    creation_page.confirm_type_change()

    expect(creation_page.type_change_modal).not_to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_be_visible()
    expect(creation_page.nom_particulier).to_be_hidden()
    expect(creation_page.nom_particulier).to_have_value("")
