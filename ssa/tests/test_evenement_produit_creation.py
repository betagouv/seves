import json
from unittest import mock
from unittest.mock import Mock

from django.http import JsonResponse
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE
from core.models import LienLibre, Contact, Departement
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.models import EvenementProduit, Etablissement
from ssa.models import TypeEvenement, Source
from ssa.tests.pages import EvenementProduitFormPage
from ssa.views import FindNumeroAgrementView
from tiac.factories import EvenementSimpleFactory

FIELD_TO_EXCLUDE_ETABLISSEMENT = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "code_insee",
    "evenement_produit_id",
    "departement_id",
]


def test_can_create_evenement_produit_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.type_evenement == input_data.type_evenement
    assert evenement_produit.description == input_data.description
    assert evenement_produit.numero is not None
    assert evenement_produit.is_draft is True


def test_can_create_evenement_produit_with_all_fields(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build(not_bacterie=True)
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.source.select_option(input_data.source)

    creation_page.set_categorie_produit(input_data)
    creation_page.denomination.fill(input_data.denomination)
    creation_page.marque.fill(input_data.marque)
    creation_page.lots.fill(input_data.lots)
    creation_page.description_complementaire.fill(input_data.description_complementaire)
    creation_page.set_temperature_conservation(input_data.temperature_conservation)

    creation_page.set_categorie_danger(input_data)
    creation_page.precision_danger.fill(input_data.precision_danger)
    creation_page.quantification.fill(str(input_data.quantification))
    creation_page.set_quantification_unite(input_data.quantification_unite)
    creation_page.evaluation.fill(input_data.evaluation)
    creation_page.reference_souches.fill(input_data.reference_souches)
    creation_page.reference_clusters.fill(input_data.reference_clusters)

    creation_page.actions_engagees.select_option(input_data.actions_engagees)
    for numero in input_data.numeros_rappel_conso:
        creation_page.add_rappel_conso(numero)
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()

    fields_to_exclude = [
        "_prefetched_objects_cache",
        "_state",
        "id",
        "numero_annee",
        "numero_evenement",
        "date_creation",
        "numero_rasff",
        "id",
    ]
    evenement_produit_data = {k: v for k, v in evenement_produit.__dict__.items() if k not in fields_to_exclude}
    input_data = {k: v for k, v in input_data.__dict__.items() if k not in fields_to_exclude}
    assert evenement_produit_data == input_data


def test_can_create_evenement_produit_with_pam_if_bacterie(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build(bacterie=True)
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)

    creation_page.set_categorie_danger(input_data)
    creation_page.set_pret_a_manger(input_data.produit_pret_a_manger)
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.produit_pret_a_manger == input_data.produit_pret_a_manger


def test_can_publish_evenement_produit(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.publish()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.type_evenement == input_data.type_evenement
    assert evenement_produit.description == input_data.description
    assert evenement_produit.numero is not None
    assert evenement_produit.is_draft is False


def test_ac_can_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.numero_rasff.fill("2024.2222")
    creation_page.submit_as_draft()

    evenement = EvenementProduit.objects.get()
    assert evenement.numero_rasff == "2024.2222"


def test_non_ac_cant_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    expect(creation_page.numero_rasff).not_to_be_visible()


def test_can_add_and_delete_numero_rappel_conso(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_rappel_conso("2025-01-1234")
    creation_page.add_rappel_conso("2025-02-1234")
    creation_page.add_rappel_conso("2025-03-1234")
    creation_page.delete_rappel_conso("2025-03-1234")
    creation_page.add_rappel_conso("2025-04-1234")
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.numeros_rappel_conso == ["2025-01-1234", "2025-02-1234", "2025-04-1234"]


def test_source_list_is_updated_when_type_evenement_is_changed(live_server, page: Page, check_select_options):
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.type_evenement.select_option(label=TypeEvenement.ALERTE_PRODUIT_NATIONALE.label)
    creation_page.source.click()
    excluded_values = {s.value for s in EvenementProduit.SOURCES_FOR_HUMAN_CASE}
    expected = [s.label for s in Source if s.value not in excluded_values]
    check_select_options(creation_page.page, "id_source", expected)

    creation_page.type_evenement.select_option(label=TypeEvenement.INVESTIGATION_CAS_HUMAINS.label)
    wanted_values = {s.value for s in EvenementProduit.SOURCES_FOR_HUMAN_CASE}
    expected = [s.label for s in Source if s.value in wanted_values]
    expected.append("Signalement autre")
    check_select_options(creation_page.page, "id_source", expected, with_default_value=False)


def test_can_add_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    evenement = EvenementProduitFactory()

    etablissement_1, etablissement_2, etablissement_3 = EtablissementFactory.build_batch(
        3, evenement_produit=evenement, departement=departement
    )

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)
    creation_page.add_etablissement(etablissement_3)
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    assert Etablissement.objects.count() == 3
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)
    assert_models_are_equal(etablissements[1], etablissement_2, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)
    assert_models_are_equal(etablissements[2], etablissement_3, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_edit_etablissement_multiple_times(live_server, page: Page, ensure_departements, assert_models_are_equal):
    ain, *_ = ensure_departements("Ain", "Aisne")
    evenement = EvenementProduitFactory()

    etablissement = EtablissementFactory.build(evenement_produit=evenement, departement=ain)

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement)
    creation_page.open_edit_etablissement()
    creation_page.current_modal.locator('[id$="-departement"]').select_option("01 - Ain")
    creation_page.close_etablissement_modal()

    creation_page.open_edit_etablissement()
    creation_page.current_modal.locator('[id$="-departement"]').select_option("02 - Aisne")
    creation_page.close_etablissement_modal()

    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    etablissement = Etablissement.objects.get()
    assert str(etablissement.departement) == "02 - Aisne"


def test_card_etablissement_content(live_server, page: Page, assert_etablissement_card_is_correct):
    etablissement = EtablissementFactory()

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.add_etablissement(etablissement)

    etablissement_card = creation_page.etablissement_card()
    assert_etablissement_card_is_correct(etablissement_card, etablissement)


def test_can_add_etablissement_with_required_fields_only(live_server, page: Page, assert_models_are_equal):
    evenement = EvenementProduitFactory()

    etablissement = EtablissementFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement_with_required_fields(etablissement)
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    etablissement = Etablissement.objects.get()
    assert_models_are_equal(etablissement, etablissement, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_add_and_delete_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    evenement = EvenementProduitFactory()

    etablissement_1, etablissement_2, etablissement_3 = EtablissementFactory.build_batch(
        3, evenement_produit=evenement, departement=departement
    )

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)
    creation_page.add_etablissement(etablissement_3)
    creation_page.delete_etablissement(1)
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    assert Etablissement.objects.count() == 2
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)
    assert_models_are_equal(etablissements[1], etablissement_3, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_add_free_links(live_server, page: Page, choice_js_fill):
    evenement = EvenementProduitFactory.build()
    evenement_1, evenement_2 = EvenementProduitFactory.create_batch(2, etat=EvenementProduit.Etat.EN_COURS)
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_free_link(evenement_1.numero, choice_js_fill)
    creation_page.add_free_link(evenement_2.numero, choice_js_fill)
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    evenement = EvenementProduit.objects.exclude(id__in=[evenement_1.id, evenement_2.id]).get()
    assert LienLibre.objects.count() == 2

    assert [lien.related_object_1 for lien in LienLibre.objects.all()] == [evenement, evenement]
    expected = sorted([evenement_1.numero, evenement_2.numero])
    assert sorted([lien.related_object_2.numero for lien in LienLibre.objects.all()]) == expected


def test_can_add_free_links_to_evenement_simple(live_server, page: Page, choice_js_fill):
    evenement = EvenementProduitFactory.build()
    evenement_simple = EvenementSimpleFactory(etat=EvenementProduit.Etat.EN_COURS)
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_free_link(evenement_simple.numero, choice_js_fill, link_label="Évenement simple : ")
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    evenement = EvenementProduit.objects.get()
    lien = LienLibre.objects.get()
    assert lien.related_object_1 == evenement
    assert lien.related_object_2 == evenement_simple


def test_cant_add_free_links_for_etat_brouillon(live_server, page: Page, choice_js_cant_pick):
    evenement = EvenementProduitFactory()
    evenement_1 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON)

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    numero = "Événement produit : " + str(evenement_1.numero)
    choice_js_cant_pick(creation_page.page, "#liens-libre .choices", numero, numero)


def test_can_create_etablissement_with_ban_auto_complete(
    live_server, page: Page, ensure_departements, choice_js_fill_from_element
):
    evenement = EvenementProduitFactory.build()
    ensure_departements("Paris")
    call_count = {"count": 0}

    def handle(route):
        response = {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {
                        "label": "251 Rue de Vaugirard 75015 Paris",
                        "name": "251 Rue de Vaugirard",
                        "citycode": "75115",
                        "city": "Paris",
                        "context": "75, Paris, Île-de-France",
                    }
                },
            ],
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(response))
        call_count["count"] += 1

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.page.route(
        "https://api-adresse.data.gouv.fr/search/?q=251%20Rue%20de%20Vaugirard&limit=15",
        handle,
    )

    creation_page.open_etablissement_modal()
    creation_page.current_modal_raison_sociale_field.fill("Foo")
    choice_js_fill_from_element(
        page, creation_page.current_modal_address_field, "251 Rue de Vaugirard", "251 Rue de Vaugirard 75015 Paris"
    )
    assert call_count["count"] == 1
    creation_page.close_etablissement_modal()
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    etablissement = Etablissement.objects.get()
    assert etablissement.adresse_lieu_dit == "251 Rue de Vaugirard"
    assert etablissement.commune == "Paris"
    assert etablissement.code_insee == "75115"
    assert etablissement.pays.name == "France"
    assert etablissement.departement == Departement.objects.get(nom="Paris")


def test_can_create_etablissement_force_ban_auto_complete(live_server, page: Page, choice_js_fill_from_element):
    evenement = EvenementProduitFactory.build()
    call_count = {"count": 0}

    def handle(route):
        response = {
            "type": "FeatureCollection",
            "features": [
                {
                    "properties": {
                        "label": "251 Rue de Vaugirard 75015 Paris",
                        "name": "251 Rue de Vaugirard",
                        "citycode": "75115",
                        "city": "Paris",
                        "context": "75, Paris, Île-de-France",
                    }
                },
            ],
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(response))
        call_count["count"] += 1

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.page.route(
        "https://api-adresse.data.gouv.fr/search/?q=Mon%20addresse%20qui%20n%27existe%20pas&limit=15",
        handle,
    )

    creation_page.open_etablissement_modal()
    creation_page.current_modal_raison_sociale_field.fill("Foo")
    creation_page.force_etablissement_adresse("Mon addresse qui n'existe pas")
    assert call_count["count"] == 1
    creation_page.close_etablissement_modal()
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    etablissement = Etablissement.objects.get()
    assert etablissement.adresse_lieu_dit == "Mon addresse qui n'existe pas"
    assert etablissement.commune == ""
    assert etablissement.code_insee == ""
    assert etablissement.pays.name == ""
    assert etablissement.departement is None


def test_ac_can_fill_rasff_number_6_digits(live_server, mocked_authentification_user, page: Page):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.numero_rasff.fill("123456")
    creation_page.submit_as_draft()

    evenement = EvenementProduit.objects.get()
    assert evenement.numero_rasff == "123456"


def test_add_contacts_on_creation(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.contacts.count() == 2

    user_contact_agent = Contact.objects.get(agent=mocked_authentification_user.agent)
    assert user_contact_agent in evenement_produit.contacts.all()

    user_contact_structure = Contact.objects.get(structure=mocked_authentification_user.agent.structure)
    assert user_contact_structure in evenement_produit.contacts.all()


def test_can_add_etablissement_and_quit_modal(live_server, page: Page, assert_models_are_equal):
    evenement = EvenementProduitFactory()

    etablissement = EtablissementFactory(evenement_produit=evenement)

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement)
    creation_page.open_edit_etablissement()
    expect(creation_page.current_modal_raison_sociale_field).to_have_value(etablissement.raison_sociale)

    page.keyboard.press("Escape")
    creation_page.open_edit_etablissement()
    expect(creation_page.current_modal_raison_sociale_field).to_have_value(etablissement.raison_sociale)


def test_can_create_etablissement_with_sirene_autocomplete(
    live_server, page: Page, ensure_departements, choice_js_fill_from_element, settings
):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    ensure_departements("Paris")
    evenement = EvenementProduitFactory.build()
    call_count = {"count": 0}

    def handle_insee_siret(route):
        data = {
            "etablissements": [
                {
                    "siret": "12007901700030",
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
                        "codeCommuneEtablissement": "75115",
                    },
                }
            ]
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(
        "https://api.insee.fr/entreprises/sirene/siret?nombre=100&q=siren%3A120079017*%20AND%20-periode(etatAdministratifEtablissement:F)",
        handle_insee_siret,
    )

    def handle_insee_commune(route):
        data = {"nom": "Paris 20e Arrondissement", "code": "75120"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(
        "https://geo.api.gouv.fr/communes/.+",
        handle_insee_commune,
    )

    creation_page = EvenementProduitFormPage(page, live_server.url)

    mocked_view = mock.Mock()
    mocked_view.side_effect = lambda request: JsonResponse({"numero_agrement": "03.223.432"})

    with (
        mock.patch.object(FindNumeroAgrementView, "get", new=mocked_view),
        mock.patch("core.mixins.requests.post") as mock_post,
    ):
        mock_post.return_value.json.return_value = {"access_token": "FAKE_TOKEN"}

        creation_page.navigate()
        mock_post.assert_called_once()

        creation_page.fill_required_fields(evenement)

        creation_page.open_etablissement_modal()
        expected_value = "DIRECTION GENERALE DE L'ALIMENTATION DIRECTION GENERALE DE L'ALIMENTATION   12007901700030 - 175 RUE DU CHEVALERET - 75013 PARIS"
        creation_page.add_etablissement_siren("120 079 017", expected_value, choice_js_fill_from_element)
        assert call_count["count"] == 1
        creation_page.page.wait_for_timeout(1000)
        mocked_view.assert_called_once()
        assert mocked_view.call_args[0][0].get_full_path() == "/ssa/api/find-numero-agrement/?siret=12007901700030"
        creation_page.close_etablissement_modal()
        creation_page.submit_as_draft()
        creation_page.page.wait_for_timeout(600)

    etablissement = Etablissement.objects.get()
    assert etablissement.adresse_lieu_dit == "175 RUE DU CHEVALERET"
    assert etablissement.commune == "PARIS"
    assert etablissement.code_insee == "75115"
    assert etablissement.pays.name == "France"
    assert etablissement.numero_agrement == "03.223.432"
    assert etablissement.siret == "12007901700030"
    assert etablissement.departement == Departement.objects.get(nom="Paris")


@mock.patch("ssa.views.api.requests.get")
@mock.patch("ssa.views.api.csv.reader")
def test_can_create_etablissement_with_force_siret_value(
    mock_csv_reader, mock_requests_get, live_server, page: Page, choice_js_fill_from_element, settings
):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    evenement = EvenementProduitFactory.build()

    mock_requests_get.return_value.text = "mocked content"
    mock_csv_reader.return_value = None
    call_count = {"count": 0}

    def handle(route):
        data = {"message": "Aucun élément trouvé"}
        route.fulfill(status=404, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(
        "https://api.insee.fr/entreprises/sirene/siret?nombre=100&q=siren%3A123123123*%20AND%20-periode(etatAdministratifEtablissement:F)",
        handle,
    )

    handle_insee_commune = Mock(side_effect=Exception("Shound not be called"))

    page.route(
        "https://geo.api.gouv.fr/communes/.+",
        handle_insee_commune,
    )

    creation_page = EvenementProduitFormPage(page, live_server.url)

    with mock.patch("core.mixins.requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"access_token": "FAKE_TOKEN"}
        creation_page.navigate()
        mock_post.assert_called_once()

    creation_page.fill_required_fields(evenement)

    creation_page.open_etablissement_modal()
    expected_value = "12312312312312 (Forcer la valeur)"
    creation_page.add_etablissement_siren("12312312312312", expected_value, choice_js_fill_from_element)
    assert call_count["count"] == 1
    creation_page.page.wait_for_timeout(1000)
    assert mock_requests_get.call_count >= 1
    creation_page.current_modal_raison_sociale_field.fill("Foo")
    creation_page.close_etablissement_modal()
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    etablissement = Etablissement.objects.get()
    assert etablissement.siret == "12312312312312"
    handle_insee_commune.assert_not_called()


@mock.patch("ssa.views.api.requests.get")
@mock.patch("ssa.views.api.csv.reader")
def test_can_create_etablissement_with_full_siren_will_filter_results(
    mock_csv_reader,
    mock_requests_get,
    live_server,
    page: Page,
    ensure_departements,
    choice_js_cant_pick,
    choice_js_fill,
    settings,
):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    ensure_departements("Paris")
    evenement = EvenementProduitFactory.build()

    mock_requests_get.return_value.text = "mocked content"
    mock_csv_reader.return_value = None
    call_count = {"count": 0}

    def handle_insee_siret(route):
        data = {
            "etablissements": [
                {
                    "siret": "12312312311111",
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
                        "codeCommuneEtablissement": "75115",
                    },
                },
                {
                    "siret": "12312312322222",
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
                        "codeCommuneEtablissement": "75115",
                    },
                },
            ]
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(
        "https://api.insee.fr/entreprises/sirene/siret?nombre=100&q=siren%3A123123123*%20AND%20-periode(etatAdministratifEtablissement:F)",
        handle_insee_siret,
    )

    def handle_insee_commune(route):
        data = {"nom": "Paris 20e Arrondissement", "code": "75120"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(
        "https://geo.api.gouv.fr/communes/.+",
        handle_insee_commune,
    )

    creation_page = EvenementProduitFormPage(page, live_server.url)

    with mock.patch("core.mixins.requests.post") as mock_post:
        mock_post.return_value.json.return_value = {"access_token": "FAKE_TOKEN"}
        creation_page.navigate()
        mock_post.assert_called_once()

    creation_page.fill_required_fields(evenement)

    creation_page.open_etablissement_modal()
    expected_value = "DIRECTION GENERALE DE L'ALIMENTATION DIRECTION GENERALE DE L'ALIMENTATION   12312312311111 - 175 RUE DU CHEVALERET - 75013 PARIS"
    choice_js_cant_pick(
        creation_page.page, 'label[for="search-siret-input-"] ~ div.choices', "12312312322222", expected_value
    )
    creation_page.page.keyboard.press("Escape")
    expected_value = "DIRECTION GENERALE DE L'ALIMENTATION DIRECTION GENERALE DE L'ALIMENTATION   12312312322222 - 175 RUE DU CHEVALERET - 75013 PARIS"
    choice_js_fill(
        creation_page.page, 'label[for="search-siret-input-"] ~ div.choices', "12312312322222", expected_value
    )
    departement = page.locator(".fr-modal__content").locator("visible=true").locator('[id$="-departement"]')
    expect(departement).to_have_value("75")


def test_can_create_evenement_produit_using_shortcut_on_categorie_danger(
    live_server, mocked_authentification_user, page: Page
):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.set_categorie_danger_from_shortcut("Escherichia coli shigatoxinogène (STEC - EHEC)")
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.categorie_danger == "Escherichia coli shigatoxinogène (STEC - EHEC)"


def test_cant_add_etablissement_with_incorrect_numero_agrement(live_server, page: Page):
    evenement = EvenementProduitFactory()

    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.open_etablissement_modal()
    creation_page.current_modal_raison_sociale_field.fill("Foo")
    creation_page.current_modal_numero_agrement_field.fill("11111111")
    creation_page.current_modal.locator(".save-btn").click()

    assert not creation_page.current_modal_numero_agrement_field.evaluate("el => el.validity.valid")


def test_categorie_danger_dont_show(live_server, mocked_authentification_user, page: Page):
    creation_page = EvenementProduitFormPage(page, live_server.url)
    creation_page.navigate()
    dropdown = creation_page.display_and_get_categorie_danger()
    # Force open the dropdown by clicking it
    dropdown.get_by_placeholder("Choisir").click()
    expect(dropdown.locator(".categorie-danger-header")).to_be_visible()
    assert "Danger les plus courants" in dropdown.inner_text()
    page.keyboard.type("Sal")
    expect(dropdown.locator(".categorie-danger-header")).to_be_hidden()
    assert "Danger les plus courants" not in dropdown.inner_text()
