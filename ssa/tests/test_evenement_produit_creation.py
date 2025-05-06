import json

from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE
from core.models import LienLibre
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.models import EvenementProduit, Etablissement, QuantificationUnite
from ssa.models import TypeEvenement, Source
from ssa.tests.pages import EvenementProduitCreationPage

FIELD_TO_EXCLUDE_ETABLISSEMENT = ["_state", "id", "code_insee", "evenement_produit_id"]


def test_can_create_evenement_produit_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.type_evenement == input_data.type_evenement
    assert evenement_produit.description == input_data.description
    assert evenement_produit.denomination == input_data.denomination
    assert evenement_produit.numero is not None
    assert evenement_produit.is_draft is True


def test_can_create_evenement_produit_with_all_fields(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.source.select_option(input_data.source)

    creation_page.marque.fill(input_data.marque)
    creation_page.lots.fill(input_data.lots)
    creation_page.description_complementaire.fill(input_data.description_complementaire)
    creation_page.set_temperature_conservation(input_data.temperature_conservation)
    creation_page.set_pret_a_manger(input_data.produit_pret_a_manger)

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


def test_can_publish_evenement_produit(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.publish()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.type_evenement == input_data.type_evenement
    assert evenement_produit.description == input_data.description
    assert evenement_produit.denomination == input_data.denomination
    assert evenement_produit.numero is not None
    assert evenement_produit.is_draft is False


def test_ac_can_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.numero_rasff.fill("2024.2222")
    creation_page.submit_as_draft()

    evenement = EvenementProduit.objects.get()
    assert evenement.numero_rasff == "2024.2222"


def test_non_ac_cant_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    expect(creation_page.numero_rasff).not_to_be_visible()


def test_can_add_and_delete_numero_rappel_conso(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
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
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.type_evenement.select_option(label=TypeEvenement.ALERTE_PRODUIT_NATIONALE.label)
    creation_page.source.click()
    excluded_values = {s.value for s in EvenementProduit.SOURCES_FOR_HUMAN_CASE}
    expected = [s.label for s in Source if s.value not in excluded_values]
    check_select_options(creation_page.page, "id_source", expected)

    creation_page.type_evenement.select_option(label=TypeEvenement.INVESTIGATION_CAS_HUMAINS.label)
    wanted_values = {s.value for s in EvenementProduit.SOURCES_FOR_HUMAN_CASE}
    expected = [s.label for s in Source if s.value in wanted_values]
    expected.append("Autre")
    check_select_options(creation_page.page, "id_source", expected, with_default_value=False)


def test_can_add_etablissements(live_server, page: Page, assert_models_are_equal):
    evenement = EvenementProduitFactory()

    etablissement_1, etablissement_2, etablissement_3 = EtablissementFactory.build_batch(3, evenement_produit=evenement)

    creation_page = EvenementProduitCreationPage(page, live_server.url)
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


def test_card_etablissement_content(live_server, page: Page):
    etablissement = EtablissementFactory()

    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.add_etablissement(etablissement)

    etablissement_card = creation_page.etablissement_card()
    expect(etablissement_card.get_by_text(etablissement.raison_sociale, exact=True)).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.pays.name, exact=True)).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.get_type_exploitant_display(), exact=True)).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.departement)).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.get_position_dossier_display(), exact=True)).to_be_visible()


def test_can_add_etablissement_with_required_fields_only(live_server, page: Page, assert_models_are_equal):
    evenement = EvenementProduitFactory()

    etablissement = EtablissementFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement_with_required_fields(etablissement)
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    etablissement = Etablissement.objects.get()
    assert_models_are_equal(etablissement, etablissement, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_can_add_and_delete_etablissements(live_server, page: Page, assert_models_are_equal):
    evenement = EvenementProduitFactory()

    etablissement_1, etablissement_2, etablissement_3 = EtablissementFactory.build_batch(3, evenement_produit=evenement)

    creation_page = EvenementProduitCreationPage(page, live_server.url)
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
    creation_page = EvenementProduitCreationPage(page, live_server.url)
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


def test_cant_add_free_links_for_etat_brouillon(live_server, page: Page, choice_js_cant_pick):
    evenement = EvenementProduitFactory()
    evenement_1 = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON)

    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    numero = "Événement produit : " + str(evenement_1.numero)
    choice_js_cant_pick(creation_page.page, "#liens-libre .choices", numero, numero)


def test_can_create_etablissement_with_ban_auto_complete(live_server, page: Page, choice_js_fill_from_element):
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

    creation_page = EvenementProduitCreationPage(page, live_server.url)
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
    assert etablissement.departement == "Paris"


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

    creation_page = EvenementProduitCreationPage(page, live_server.url)
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
    assert etablissement.departement == ""


def test_ac_can_fill_rasff_number_6_digits(live_server, mocked_authentification_user, page: Page):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.numero_rasff.fill("123456")
    creation_page.submit_as_draft()

    evenement = EvenementProduit.objects.get()
    assert evenement.numero_rasff == "123456"


def test_cant_create_evenement_produit_with_quantification_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.quantification.fill("3.14")
    creation_page.submit_as_draft()

    assert EvenementProduit.objects.count() == 0
    assert creation_page.error_messages == [
        "Quantification et unité de quantification doivent être tous les deux renseignés ou tous les deux vides."
    ]


def test_cant_create_evenement_produit_with_quantification_unit_only(
    live_server, mocked_authentification_user, page: Page
):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.set_quantification_unite(QuantificationUnite.MG_KG)
    creation_page.submit_as_draft()

    assert EvenementProduit.objects.count() == 0
    assert creation_page.error_messages == [
        "Quantification et unité de quantification doivent être tous les deux renseignés ou tous les deux vides."
    ]
