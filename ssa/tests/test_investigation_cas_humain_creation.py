import json
from unittest import mock
from unittest.mock import Mock

from django.http import JsonResponse
from django.urls import reverse
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE
from core.mixins import WithEtatMixin
from core.models import Departement, LienLibre
from ssa.factories import EtablissementFactory, InvestigationCasHumainFactory
from ssa.models import Etablissement, EvenementInvestigationCasHumain
from ssa.tests.pages import InvestigationCasHumainFormPage
from ssa.views import FindNumeroAgrementView
from tiac.factories import EvenementSimpleFactory, InvestigationTiacFactory

FIELD_TO_EXCLUDE_ETABLISSEMENT = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "code_insee",
    "investigation_cas_humain_id",
    "departement_id",
]


def test_can_create_investigation_cas_humain_with_required_fields_only(
    live_server, mocked_authentification_user, page: Page
):
    input_data = InvestigationCasHumainFactory.build()
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    investigation_cas_humain = EvenementInvestigationCasHumain.objects.get()
    assert investigation_cas_humain.createur == mocked_authentification_user.agent.structure
    assert investigation_cas_humain.type_evenement == input_data.type_evenement
    assert investigation_cas_humain.description == input_data.description
    assert investigation_cas_humain.numero is not None
    assert investigation_cas_humain.is_draft is True


def test_can_create_investigation_cas_humain_with_all_fields(
    live_server, mocked_authentification_user, assert_models_are_equal, page: Page
):
    input_data = InvestigationCasHumainFactory.build()
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.date_reception.fill(input_data.date_reception.strftime("%Y-%m-%d"))
    creation_page.source.select_option(input_data.source)

    creation_page.set_categorie_danger(input_data)
    creation_page.precision_danger.fill(input_data.precision_danger)
    creation_page.evaluation.fill(input_data.evaluation)
    creation_page.reference_souches.fill(input_data.reference_souches)
    creation_page.reference_clusters.fill(input_data.reference_clusters)

    creation_page.submit_as_draft()

    investigation_cas_humain = EvenementInvestigationCasHumain.objects.get()

    assert_models_are_equal(
        investigation_cas_humain,
        input_data,
        to_exclude=[
            "_prefetched_objects_cache",
            "_state",
            "id",
            "numero_annee",
            "numero_evenement",
            "date_creation",
            "numero_rasff",
            "id",
        ],
    )


def test_can_publish_investigation_cas_humain(live_server, mocked_authentification_user, page: Page):
    input_data = InvestigationCasHumainFactory.build()
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.publish()

    investigation_cas_humain = EvenementInvestigationCasHumain.objects.get()
    assert investigation_cas_humain.createur == mocked_authentification_user.agent.structure
    assert investigation_cas_humain.type_evenement == input_data.type_evenement
    assert investigation_cas_humain.description == input_data.description
    assert investigation_cas_humain.numero is not None
    assert investigation_cas_humain.is_draft is False


def test_ac_can_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()
    input_data = InvestigationCasHumainFactory.build()
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.numero_rasff.fill("2024.2222")
    creation_page.submit_as_draft()

    evenement = EvenementInvestigationCasHumain.objects.get()
    assert evenement.numero_rasff == "2024.2222"


def test_non_ac_cant_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    expect(creation_page.numero_rasff).not_to_be_visible()


def test_can_add_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    evenement = InvestigationCasHumainFactory()

    etablissement_1, etablissement_2, etablissement_3 = EtablissementFactory.build_batch(
        3, investigation_cas_humain=evenement, departement=departement
    )

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)
    creation_page.add_etablissement(etablissement_3)
    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 3
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)
    assert_models_are_equal(etablissements[1], etablissement_2, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)
    assert_models_are_equal(etablissements[2], etablissement_3, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_edit_etablissement_multiple_times(live_server, page: Page, ensure_departements, assert_models_are_equal):
    ain, *_ = ensure_departements("Ain", "Aisne")
    evenement = InvestigationCasHumainFactory()

    etablissement = EtablissementFactory.build(investigation_cas_humain=evenement, departement=ain)

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
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

    etablissement = Etablissement.objects.get()
    assert str(etablissement.departement) == "02 - Aisne"


def test_card_etablissement_content(live_server, page: Page, assert_etablissement_card_is_correct):
    evenement = InvestigationCasHumainFactory()
    etablissement = EtablissementFactory(investigation_cas_humain=evenement)

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.add_etablissement(etablissement)

    etablissement_card = creation_page.etablissement_card()
    assert_etablissement_card_is_correct(etablissement_card, etablissement)


def test_can_add_etablissement_with_required_fields_only(live_server, page: Page, assert_models_are_equal):
    evenement = InvestigationCasHumainFactory()

    etablissement = EtablissementFactory.build(investigation_cas_humain=evenement)
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement_with_required_fields(etablissement)
    creation_page.submit_as_draft()

    etablissement = Etablissement.objects.get()
    assert_models_are_equal(etablissement, etablissement, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_add_and_delete_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    evenement = InvestigationCasHumainFactory()

    etablissement_1, etablissement_2, etablissement_3 = EtablissementFactory.build_batch(
        3, investigation_cas_humain=evenement, departement=departement
    )

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)
    creation_page.add_etablissement(etablissement_3)
    creation_page.delete_etablissement(1)
    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 2
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)
    assert_models_are_equal(etablissements[1], etablissement_3, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_add_etablissement_and_quit_modal(live_server, page: Page, assert_models_are_equal):
    evenement = InvestigationCasHumainFactory()

    etablissement = EtablissementFactory(investigation_cas_humain=evenement)

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
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
    evenement = InvestigationCasHumainFactory.build()
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

    page.route(f"**{reverse('siret-api', kwargs={'siret': '*'})}**/", handle_insee_siret)

    def handle_insee_commune(route):
        data = {"nom": "Paris 20e Arrondissement", "code": "75120"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(
        "https://geo.api.gouv.fr/communes/.+",
        handle_insee_commune,
    )

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)

    mocked_view = mock.Mock()
    mocked_view.side_effect = lambda request: JsonResponse({"numero_agrement": "03.223.432"})

    with mock.patch.object(FindNumeroAgrementView, "get", new=mocked_view):
        creation_page.navigate()

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
    evenement = InvestigationCasHumainFactory.build()

    mock_requests_get.return_value.text = "mocked content"
    mock_csv_reader.return_value = None
    call_count = {"count": 0}

    def handle(route):
        data = {"message": "Aucun élément trouvé"}
        route.fulfill(status=404, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(f"**{reverse('siret-api', kwargs={'siret': '*'})}**/", handle)

    handle_insee_commune = Mock(side_effect=Exception("Shound not be called"))

    page.route(
        "https://geo.api.gouv.fr/communes/.+",
        handle_insee_commune,
    )

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
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
    evenement = InvestigationCasHumainFactory.build()

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

    page.route(f"**{reverse('siret-api', kwargs={'siret': '*'})}**/", handle_insee_siret)

    def handle_insee_commune(route):
        data = {"nom": "Paris 20e Arrondissement", "code": "75120"}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))
        call_count["count"] += 1

    page.route(
        "https://geo.api.gouv.fr/communes/.+",
        handle_insee_commune,
    )

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)

    creation_page.navigate()

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


def test_can_add_free_links(live_server, page: Page, choice_js_fill):
    evenement = InvestigationCasHumainFactory.build()
    evenement_1, evenement_2 = InvestigationCasHumainFactory.create_batch(2, etat=WithEtatMixin.Etat.EN_COURS)
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_free_link(evenement_1.numero, choice_js_fill, link_label="Investigation de cas humain : ")
    creation_page.add_free_link(evenement_2.numero, choice_js_fill, link_label="Investigation de cas humain : ")
    creation_page.submit_as_draft()

    evenement = EvenementInvestigationCasHumain.objects.exclude(id__in=[evenement_1.id, evenement_2.id]).get()
    assert LienLibre.objects.count() == 2

    assert [lien.related_object_1 for lien in LienLibre.objects.all()] == [evenement, evenement]
    expected = sorted([evenement_1.numero, evenement_2.numero])
    assert sorted([lien.related_object_2.numero for lien in LienLibre.objects.all()]) == expected


def test_can_add_free_links_to_evenement_simple(live_server, page: Page, choice_js_fill):
    evenement = InvestigationCasHumainFactory.build()
    evenement_simple = EvenementSimpleFactory(etat=WithEtatMixin.Etat.EN_COURS)
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_free_link(evenement_simple.numero, choice_js_fill, link_label="Enregistrement simple : ")
    creation_page.submit_as_draft()

    evenement = EvenementInvestigationCasHumain.objects.get()
    lien = LienLibre.objects.get()
    assert lien.related_object_1 == evenement
    assert lien.related_object_2 == evenement_simple


def test_can_add_free_links_to_investigation_tiac(live_server, page: Page, choice_js_fill):
    evenement = InvestigationCasHumainFactory.build()
    investigation = InvestigationTiacFactory(etat=WithEtatMixin.Etat.EN_COURS)
    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_free_link(investigation.numero, choice_js_fill, link_label="Investigation de tiac : ")
    creation_page.submit_as_draft()

    evenement = EvenementInvestigationCasHumain.objects.get()
    lien = LienLibre.objects.get()
    assert lien.related_object_1 == evenement
    assert lien.related_object_2 == investigation


def test_cant_add_free_links_for_etat_brouillon(live_server, page: Page, choice_js_cant_pick):
    evenement = InvestigationCasHumainFactory()
    evenement_1 = InvestigationCasHumainFactory(etat=WithEtatMixin.Etat.BROUILLON)

    creation_page = InvestigationCasHumainFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    numero = "Événement produit : " + str(evenement_1.numero)
    choice_js_cant_pick(creation_page.page, "#liens-libre .choices", numero, numero)
