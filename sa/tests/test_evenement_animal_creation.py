import json

from django.urls import reverse
from playwright.sync_api import Page, expect

from sa.models import EvenementAnimal
from sa.models.evenement import StatutAnimal, TypeLieu
from sa.tests.factories import AcarapioseFactory, EspeceFactory, EvenementAnimalFactory, MaladieFactory
from sa.tests.pages import EvenementAnimalFormPage, EvenementListPage
from seves import settings
from sv.models import Evenement


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
    creation_page.submit_as_draft()

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
    creation_page.submit_as_draft()

    evenement = EvenementAnimal.objects.get()
    assert evenement.createur == mocked_authentification_user.agent.structure
    assert evenement.maladie == maladie
    assert evenement.espece == espece
    assert evenement.statut_animal == input_data.statut_animal
    assert evenement.statut_evenement == input_data.statut_evenement
    assert evenement.date_statut_changed == input_data.date_statut_changed
    assert evenement.is_draft is True


def test_can_publish_evenement_animal_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.publish()

    evenement = EvenementAnimal.objects.get()
    assert evenement.createur == mocked_authentification_user.agent.structure
    assert evenement.date_publication is not None
    assert evenement.is_draft is False
    assert evenement.etat == Evenement.Etat.EN_COURS


def test_type_lieu_options_depend_on_statut_animal(live_server, page: Page, check_select_options):
    maladie = MaladieFactory()
    espece = EspeceFactory()
    creation_page = EvenementAnimalFormPage(page, live_server.url)

    creation_page.navigate(maladie, espece, StatutAnimal.DETENU)
    check_select_options(page, "id_type_lieu", [label for _, label in TypeLieu.choices_detenu])

    creation_page.navigate(maladie, espece, StatutAnimal.SAUVAGE)
    check_select_options(page, "id_type_lieu", [label for _, label in TypeLieu.choices_sauvage])


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
    creation_page.submit_as_draft()

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
    creation_page.submit_as_draft()

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
    creation_page.submit_as_draft()

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
    creation_page.submit_as_draft()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    fields = [
        "numero_identifiant_etablissement",
        "raison_sociale_etablissement",
        "departement_etablissement",
        "adresse_lieu_dit_etablissement",
        "code_insee_etablissement",
        "siret_etablissement",
        "pays_etablissement",
    ]
    for field in fields:
        assert getattr(evenement_produit, field) == getattr(input_data, field)
    assert evenement_produit.commune_etablissement == "Lille"


def test_can_create_evenement_animal_with_detenteur_etablissement_sirene_autocomplete(
    live_server, page: Page, ensure_departements
):
    input_data = EvenementAnimalFactory.build()
    maladie = MaladieFactory()
    espece = EspeceFactory()
    ensure_departements("Paris")

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    call_count = {"count": 0}
    siret = "12007901700030"

    def handle(route):
        data = {
            "etablissements": [
                {
                    "siret": siret,
                    "uniteLegale": {
                        "denominationUniteLegale": "DIRECTION GENERALE DE L'ALIMENTATION",
                        "prenom1UniteLegale": None,
                        "nomUniteLegale": None,
                    },
                    "adresseEtablissement": {
                        "numeroVoieEtablissement": "175",
                        "typeVoieEtablissement": "RUE",
                        "libelleVoieEtablissement": "DU CHEVALERET",
                        "codePostalEtablissement": "75013",
                        "libelleCommuneEtablissement": "PARIS",
                        "codeCommuneEtablissement": "75013",
                    },
                }
            ]
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    creation_page.page.route(f"**{reverse('siret-api', kwargs={'siret': '*'})}**/", handle)
    creation_page.fill_siret_etablissement(
        "DIRECTION GENERALE DE L'ALIMENTATION DIRECTION GENERALE DE L'ALIMENTATION   12007901700030 - 175 RUE DU CHEVALERET - 75013 PARIS",
        search="120 079 017",
    )
    assert call_count["count"] == 1
    expect(creation_page.reprendre_adresse_detenteur_btn).to_be_enabled()
    creation_page.submit_as_draft()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.siret_etablissement == siret
    assert evenement_produit.raison_sociale_etablissement == "DIRECTION GENERALE DE L'ALIMENTATION"
    assert evenement_produit.adresse_lieu_dit_etablissement == "175 RUE DU CHEVALERET"
    assert evenement_produit.commune_etablissement == "PARIS"
    assert evenement_produit.code_insee_etablissement == "75013"
    assert evenement_produit.pays_etablissement == "FR"
    assert evenement_produit.departement_etablissement.numero == "75"


def test_can_create_evenement_animal_with_detenteur_particulier_block(live_server, page: Page):
    input_data = EvenementAnimalFactory(particulier=True)
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_detenteur_particulier_block(input_data)
    creation_page.submit_as_draft()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    fields = [
        "nom_particulier",
        "prenom_particulier",
        "adresse_particulier",
        "departement_particulier",
        "code_insee_particulier",
        "email_particulier",
        "telephone_particulier",
    ]
    for field in fields:
        assert getattr(evenement_produit, field) == getattr(input_data, field)
    assert evenement_produit.commune_particulier == "Lille"


PARCEL_WFS_URL = "https://data.geopf.fr/wfs/ows"
PARCEL_NUMERO = "0067"


def _set_parcelles_checkbox(creation_page, checked):
    creation_page.parcelles_checkbox.set_checked(checked, force=True)


def _parcel_response(properties=None):
    features = []
    if properties is not None:
        features = [
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [[[[2.35, 48.85], [2.351, 48.85], [2.351, 48.851], [2.35, 48.851], [2.35, 48.85]]]],
                },
            }
        ]
    return {"type": "FeatureCollection", "features": features}


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
    creation_page.force_siret_etablissement(input_data.siret_etablissement)
    creation_page.force_address_etablissement(input_data.adresse_lieu_dit_etablissement)
    creation_page.force_commune_etablissement()

    creation_page.particulier_label.click()
    creation_page.confirm_type_change()

    expect(creation_page.type_change_modal).not_to_be_visible()
    expect(creation_page.nom_particulier).to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_be_hidden()
    expect(creation_page.numero_identifiant_etablissement).to_have_value("")
    expect(creation_page.raison_sociale_etablissement).to_have_value("")
    selected_item = ".choices__list--single .choices__item"
    expect(creation_page._siret_choicejs.choice_widget.locator(selected_item)).not_to_contain_text(
        input_data.siret_etablissement
    )
    expect(creation_page._address_etablissement_choicejs.choice_widget.locator(selected_item)).not_to_contain_text(
        input_data.adresse_lieu_dit_etablissement
    )
    expect(creation_page._commune_etablissement_choicejs.choice_widget.locator(selected_item)).not_to_contain_text(
        "Lille"
    )


def test_confirmation_modal_when_switching_from_particulier_to_etablissement_with_data(live_server, page: Page):
    input_data = EvenementAnimalFactory.build(particulier=True)
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.particulier_label.click()
    creation_page.nom_particulier.fill(input_data.nom_particulier)
    creation_page.force_address_particulier(input_data.adresse_particulier)
    creation_page.force_commune_particulier()

    creation_page.etablissement_label.click()

    expect(creation_page.type_change_modal).to_be_visible()

    creation_page.confirm_type_change()

    expect(creation_page.type_change_modal).not_to_be_visible()
    expect(creation_page.numero_identifiant_etablissement).to_be_visible()
    expect(creation_page.nom_particulier).to_be_hidden()
    expect(creation_page.nom_particulier).to_have_value("")
    selected_item = ".choices__list--single .choices__item"
    expect(creation_page._address_particulier_choicejs.choice_widget.locator(selected_item)).not_to_contain_text(
        input_data.adresse_particulier
    )
    expect(creation_page._commune_particulier_choicejs.choice_widget.locator(selected_item)).not_to_contain_text(
        "Lille"
    )


def test_parcelles_checkbox_unchecked_by_default(live_server, page: Page):
    maladie = MaladieFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    expect(creation_page.parcelles_checkbox).to_be_visible()
    expect(creation_page.parcelles_checkbox).not_to_be_checked()


def test_parcelles_checkbox_displays_and_hides_parcel_layer(live_server, page: Page):
    maladie = MaladieFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()
    call_count = {"count": 0}

    def handle(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_parcel_response({"id_parcel": "1", "code_cultu": "BTH"})),
        )
        call_count["count"] += 1

    page.route(lambda url: url.startswith(PARCEL_WFS_URL), handle)

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_coordinates(input_data.coordinates)
    page.wait_for_timeout(600)

    _set_parcelles_checkbox(creation_page, True)
    page.wait_for_timeout(800)

    assert call_count["count"] == 1
    expect(creation_page.parcelles_message).to_be_hidden()

    _set_parcelles_checkbox(creation_page, False)
    page.mouse.wheel(0, -100)
    page.wait_for_timeout(800)

    assert call_count["count"] == 1


def test_parcelles_insufficient_zoom_shows_message(live_server, page: Page):
    maladie = MaladieFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()
    call_count = {"count": 0}

    def handle(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(_parcel_response({"id_parcel": "1", "code_cultu": "BTH"})),
        )
        call_count["count"] += 1

    page.route(lambda url: url.startswith(PARCEL_WFS_URL), handle)

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    _set_parcelles_checkbox(creation_page, True)
    page.wait_for_timeout(800)

    expect(creation_page.parcelles_message).to_be_visible()
    expect(creation_page.parcelles_message).to_have_text("Zoomez pour afficher les parcelles")
    assert call_count["count"] == 0


def test_parcelles_api_failure_shows_message(live_server, page: Page):
    maladie = MaladieFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()
    page_errors = []
    page.on("pageerror", lambda exc: page_errors.append(exc))

    page.route(lambda url: url.startswith(PARCEL_WFS_URL), lambda route: route.fulfill(status=500, body="error"))

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_coordinates(input_data.coordinates)

    _set_parcelles_checkbox(creation_page, True)
    page.wait_for_timeout(800)

    expect(creation_page.parcelles_message).to_be_visible()
    expect(creation_page.parcelles_message).to_have_text("Les parcelles ne sont pas disponibles pour le moment")
    assert page_errors == []


def test_double_click_on_map_fills_numero_identifiant(live_server, page: Page):
    maladie = MaladieFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()

    page.route(
        lambda url: url.startswith(PARCEL_WFS_URL),
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps(_parcel_response({"numero": PARCEL_NUMERO}))
        ),
    )

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)

    expect(creation_page.map_canvas).to_be_visible()
    page.wait_for_timeout(600)
    creation_page.map_canvas.dblclick()
    page.wait_for_timeout(800)

    expect(creation_page.numero_identifiant).to_have_value(PARCEL_NUMERO)


def test_double_click_on_map_without_parcelle_leaves_numero_identifiant_unchanged(live_server, page: Page):
    maladie = MaladieFactory()
    espece = EspeceFactory()
    input_data = EvenementAnimalFactory.build()
    call_count = {"count": 0}

    def handle(route):
        route.fulfill(status=200, content_type="application/json", body=json.dumps(_parcel_response()))
        call_count["count"] += 1

    page.route(lambda url: url.startswith(PARCEL_WFS_URL), handle)

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.numero_identifiant.fill("valeur-existante")

    expect(creation_page.map_canvas).to_be_visible()
    page.wait_for_timeout(600)
    creation_page.map_canvas.dblclick()
    page.wait_for_timeout(800)

    assert call_count["count"] == 1
    expect(creation_page.numero_identifiant).to_have_value("valeur-existante")


def test_can_create_evenement_animal_when_maladie_needs_arrete(live_server, page: Page):
    input_data = EvenementAnimalFactory.build(maladie__needs_arrete=True)
    maladie = MaladieFactory(needs_arrete=True)
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.date_apms.fill(input_data.date_apms.strftime("%Y-%m-%d"))
    creation_page.date_apdi.fill(input_data.date_apdi.strftime("%Y-%m-%d"))
    creation_page.date_levee.fill(input_data.date_levee.strftime("%Y-%m-%d"))
    creation_page.submit_as_draft()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.date_apms == input_data.date_apms
    assert evenement_produit.date_apdi == input_data.date_apdi
    assert evenement_produit.date_levee == input_data.date_levee


def test_can_create_evenement_animal_when_maladie_needs_dates_desinfection(live_server, page: Page):
    input_data = EvenementAnimalFactory.build(maladie__needs_dates_desinfection=True)
    maladie = MaladieFactory(name="Needs date desinfection", needs_date_nd=False, needs_dates_desinfection=True)
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.date_d_zero.fill(input_data.date_d_zero.strftime("%Y-%m-%d"))
    creation_page.date_nd1.fill(input_data.date_nd1.strftime("%Y-%m-%d"))
    creation_page.date_nd2.fill(input_data.date_nd2.strftime("%Y-%m-%d"))
    creation_page.submit_as_draft()

    evenement_produit = EvenementAnimal.objects.get()
    assert evenement_produit.date_d_zero == input_data.date_d_zero
    assert evenement_produit.date_nd1 == input_data.date_nd1
    assert evenement_produit.date_nd2 == input_data.date_nd2


def test_evenement_animal_maladie_needs_dates_desinfection_without_correct_order(live_server, page: Page):
    input_data = EvenementAnimalFactory.build(maladie__needs_dates_desinfection=True)
    maladie = MaladieFactory(name="Needs date desinfection order", needs_date_nd=False, needs_dates_desinfection=True)
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.date_d_zero.fill("2026-01-01")
    creation_page.date_nd1.fill("2025-01-01")
    creation_page.submit_as_draft(wait_for=None)

    expect(
        creation_page.page.get_by_text("Les dates D0, ND1 et ND2 doivent respecter l'ordre D0 ≤ ND1 ≤ ND2.", exact=True)
    ).to_have_count(2)
    assert EvenementAnimal.objects.count() == 0


def test_evenement_animal_creation_hide_dates_when_not_needed(live_server, page: Page):
    input_data = EvenementAnimalFactory.build()
    maladie = AcarapioseFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    expect(creation_page.date_apms).not_to_be_visible()
    expect(creation_page.date_apdi).not_to_be_visible()
    expect(creation_page.date_levee).not_to_be_visible()
    expect(creation_page.date_d_zero).not_to_be_visible()
    expect(creation_page.date_nd1).not_to_be_visible()
    expect(creation_page.date_nd2).not_to_be_visible()


def _mock_geocode_search(page, *, lat=48.840234, lon=2.304014):
    response = {
        "type": "FeatureCollection",
        "features": [
            {
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
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
    page.route(
        f"{settings.GEOCODE_URL}/search/?*",
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(response)),
    )


def test_reuse_address_button_is_disabled_when_detenteur_is_empty(live_server, page: Page):
    input_data = EvenementAnimalFactory()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)

    expect(creation_page.reprendre_adresse_detenteur_btn).to_be_disabled()

    creation_page.force_address_etablissement(input_data.adresse_lieu_dit_etablissement)
    expect(creation_page.reprendre_adresse_detenteur_btn).to_be_enabled()

    creation_page.particulier_label.click()
    creation_page.confirm_type_change()
    expect(creation_page.reprendre_adresse_detenteur_btn).to_be_disabled()

    creation_page.force_address_particulier("12 rue des Lilas")
    expect(creation_page.reprendre_adresse_detenteur_btn).to_be_enabled()


def test_can_reuse_address_from_detenteur_etablissement_block(live_server, page: Page):
    input_data = EvenementAnimalFactory()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_detenteur_etablissement_block(input_data)

    _mock_geocode_search(creation_page.page)
    creation_page.reprendre_adresse_detenteur_btn.click()

    expect(creation_page.adresse_lieu_dit).to_have_value(input_data.adresse_lieu_dit_etablissement)
    expect(creation_page.commune).to_have_value("Lille")
    expect(creation_page.code_insee).to_have_value(input_data.code_insee_etablissement)
    expect(creation_page.coordinates_0).to_have_value("48.840234")
    expect(creation_page.coordinates_1).to_have_value("2.304014")

    creation_page.submit_as_draft()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    assert evenement_produit.adresse_lieu_dit == input_data.adresse_lieu_dit_etablissement
    assert evenement_produit.commune == "Lille"
    assert evenement_produit.code_insee == input_data.code_insee_etablissement


def test_can_reuse_address_from_detenteur_particulier_block(live_server, page: Page):
    input_data = EvenementAnimalFactory(particulier=True)
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_detenteur_particulier_block(input_data)

    _mock_geocode_search(creation_page.page)
    creation_page.reprendre_adresse_detenteur_btn.click()

    expect(creation_page.adresse_lieu_dit).to_have_value(input_data.adresse_particulier)
    expect(creation_page.commune).to_have_value("Lille")
    expect(creation_page.code_insee).to_have_value(input_data.code_insee_particulier)

    creation_page.submit_as_draft()

    evenement_produit = EvenementAnimal.objects.exclude(id=input_data.pk).get()
    assert evenement_produit.adresse_lieu_dit == input_data.adresse_particulier
    assert evenement_produit.commune == "Lille"
    assert evenement_produit.code_insee == input_data.code_insee_particulier


def test_reuse_address_does_not_auto_sync_on_further_detenteur_changes(live_server, page: Page):
    input_data = EvenementAnimalFactory()
    maladie = MaladieFactory()
    espece = EspeceFactory()

    creation_page = EvenementAnimalFormPage(page, live_server.url)
    creation_page.navigate(maladie, espece, input_data.statut_animal)
    creation_page.fill_required_fields(input_data)
    creation_page.fill_detenteur_etablissement_block(input_data)

    _mock_geocode_search(creation_page.page)
    creation_page.reprendre_adresse_detenteur_btn.click()
    expect(creation_page.adresse_lieu_dit).to_have_value(input_data.adresse_lieu_dit_etablissement)

    creation_page.force_address_etablissement("Nouvelle adresse jamais reprise")

    expect(creation_page.adresse_lieu_dit).to_have_value(input_data.adresse_lieu_dit_etablissement)
