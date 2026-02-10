import json
import random
from unittest import mock

from django.http import JsonResponse
from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest

from core.constants import MUS_STRUCTURE
from core.factories import DepartementFactory
from core.models import Contact, Departement, LienLibre
from ssa.constants import CategorieDanger
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from ssa.views import FindNumeroAgrementView
from tiac.factories import (
    AlimentSuspectFactory,
    AnalyseAlimentaireFactory,
    EvenementSimpleFactory,
    InvestigationTiacFactory,
    RepasSuspectFactory,
)

from ..constants import (
    DANGERS_COURANTS,
    DangersSyndromiques,
    ModaliteDeclarationEvenement,
    MotifAliment,
    SuspicionConclusion,
    TypeCollectivite,
    TypeRepas,
)
from ..models import (
    AlimentSuspect,
    AnalyseAlimentaire,
    Etablissement,
    EvenementSimple,
    InvestigationFollowUp,
    InvestigationTiac,
    RepasSuspect,
)
from .pages import InvestigationTiacFormPage

fields_to_exclude_repas = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "investigation_id",
]

fields_to_exclude_aliment = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "investigation_id",
]

pytestmark = pytest.mark.usefixtures("mus_contact")


def test_can_create_investigation_tiac_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = InvestigationTiacFactory.build()
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.createur == mocked_authentification_user.agent.structure
    assert investigation.follow_up == input_data.follow_up
    assert investigation.contenu == input_data.contenu
    assert investigation.numero is not None
    assert investigation.is_draft is True

    expect(creation_page.page.get_by_text("L’évènement a été créé avec succès.")).to_be_visible()


def test_add_contacts_on_creation(live_server, mocked_authentification_user, page: Page):
    input_data = InvestigationTiacFactory.build()
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    object = InvestigationTiac.objects.get()
    assert object.contacts.count() == 2

    user_contact_agent = Contact.objects.get(agent=mocked_authentification_user.agent)
    assert user_contact_agent in object.contacts.all()

    user_contact_structure = Contact.objects.get(structure=mocked_authentification_user.agent.structure)
    assert user_contact_structure in object.contacts.all()


def test_can_create_investigation_tiac_with_all_fields(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal
):
    input_data: InvestigationTiac = InvestigationTiacFactory.build(danger_syndromiques_suspectes=[])

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_context_block(input_data)

    for danger in input_data.agents_confirmes_ars:
        creation_page.add_agent_pathogene_confirme(CategorieDanger(danger).label)

    creation_page.fill_conlusion(input_data)

    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.last()
    assert_models_are_equal(
        input_data,
        investigation,
        to_exclude=[
            "id",
            "_state",
            "_original_state",
            "numero_annee",
            "numero_evenement",
            "date_creation",
            "analyses_sur_les_malades",
            "precisions",
        ],
        ignore_array_order=True,
    )


test_data = [
    pytest.param(
        SuspicionConclusion.CONFIRMED.value,
        random.sample(CategorieDanger.values, k=1),
        id=f"{SuspicionConclusion.CONFIRMED}-single",
    ),
    pytest.param(
        SuspicionConclusion.CONFIRMED.value,
        random.sample(CategorieDanger.values, k=2),
        id=f"{SuspicionConclusion.CONFIRMED}-multiple",
    ),
    pytest.param(
        SuspicionConclusion.CONFIRMED.value,
        random.sample(DANGERS_COURANTS, k=1),
        id=f"{SuspicionConclusion.CONFIRMED}-common-choices",
    ),
    pytest.param(
        SuspicionConclusion.SUSPECTED.value,
        random.sample(DangersSyndromiques.values, k=1),
        id=f"{SuspicionConclusion.SUSPECTED}-single",
    ),
    pytest.param(
        SuspicionConclusion.SUSPECTED.value,
        random.sample(DangersSyndromiques.values, k=2),
        id=f"{SuspicionConclusion.SUSPECTED}-multiple",
    ),
    *[(item.value, []) for item in SuspicionConclusion.no_clue],
]


@pytest.mark.parametrize("suspicion_conclusion,selected_hazard", test_data)
def test_can_create_investigation_tiac_conlusion(
    live_server,
    mocked_authentification_user,
    page: Page,
    assert_models_are_equal,
    suspicion_conclusion,
    selected_hazard,
):
    input_data: InvestigationTiac = InvestigationTiacFactory.build(
        danger_syndromiques_suspectes=[], suspicion_conclusion=suspicion_conclusion, selected_hazard=selected_hazard
    )

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)

    creation_page.fill_conlusion(input_data)

    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.last()
    assert_models_are_equal(
        input_data,
        investigation,
        fields=[
            "suspicion_conclusion",
            "selected_hazard",
            "conclusion_comment",
            "conclusion_repas",
            "conclusion_aliment",
        ],
        ignore_array_order=True,
    )


def test_can_create_investigation_tiac_with_agents_pathogenes_shortcut(live_server, page: Page):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_agent_pathogene_confirme_via_shortcut("Shigella")
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.last()
    assert investigation.agents_confirmes_ars == ["Shigella"]


def test_can_create_investigation_tiac_etiologie(live_server, mocked_authentification_user, page: Page):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_POISSONS.label)
    assert creation_page.nb_dangers == 1

    creation_page.set_analyses("Oui")
    creation_page.precisions.fill("Mes précisions")
    creation_page.submit_as_draft()
    investigation = InvestigationTiac.objects.last()
    assert investigation.danger_syndromiques_suspectes == ["toxine des poissons"]
    assert investigation.precisions == "Mes précisions"
    assert investigation.analyses_sur_les_malades == "oui"


def test_can_add_and_delete_danger_in_investigation_tiac_etiologie(
    live_server, mocked_authentification_user, page: Page
):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_POISSONS.label)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_COQUILLAGES.label)
    creation_page.add_danger_syndromique(DangersSyndromiques.HISTAMINE.label)
    assert creation_page.nb_dangers == 3

    creation_page.delete_danger_syndromique(1)
    assert creation_page.nb_dangers == 2
    creation_page.submit_as_draft()
    investigation = InvestigationTiac.objects.last()
    assert investigation.danger_syndromiques_suspectes == ["toxine des poissons", "histamine"]


def test_cant_add_same_danger_twice_in_investigation_tiac_etiologie(
    live_server, mocked_authentification_user, page: Page
):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_POISSONS.label)
    creation_page.open_danger_modal()
    expect(creation_page.find_label_for_danger(DangersSyndromiques.TOXINE_DES_POISSONS.label)).to_be_disabled()


def test_can_create_investigation_tiac_with_repas(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal
):
    departement = DepartementFactory()
    input_data: RepasSuspect = RepasSuspectFactory.build(departement=departement)
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data.investigation)
    creation_page.add_repas(input_data)
    expect(creation_page.get_repas_card(0).get_by_text(input_data.denomination, exact=True)).to_be_visible()
    expect(creation_page.get_repas_card(0).get_by_text(input_data.get_type_repas_display())).to_be_visible()
    expect(creation_page.get_repas_card(0).get_by_text(input_data.nombre_participant, exact=True)).to_be_visible()

    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.createur == mocked_authentification_user.agent.structure
    assert investigation.repas.count() == 1
    assert_models_are_equal(
        input_data, investigation.repas.get(), to_exclude=fields_to_exclude_repas, ignore_array_order=True
    )


def test_can_create_investigation_tiac_with_repas_and_edit(live_server, mocked_authentification_user, page: Page):
    departement = DepartementFactory()
    input_data: RepasSuspect = RepasSuspectFactory.build(departement=departement)
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data.investigation)
    creation_page.add_repas(input_data)
    assert creation_page.nb_repas == 1
    creation_page.edit_repas(0, denomination="Ma nouvelle dénomination")
    assert creation_page.nb_repas == 1
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.createur == mocked_authentification_user.agent.structure
    assert investigation.repas.get().denomination == "Ma nouvelle dénomination"


def test_can_create_investigation_tiac_with_mutliple_repas_and_delete(
    live_server, mocked_authentification_user, page: Page
):
    departement = DepartementFactory()
    input_data_1: RepasSuspect = RepasSuspectFactory.build(departement=departement, denomination="Foo")
    input_data_2: RepasSuspect = RepasSuspectFactory.build(departement=departement, denomination="Bar")
    input_data_3: RepasSuspect = RepasSuspectFactory.build(departement=departement, denomination="Buzz")

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data_1.investigation)
    creation_page.add_repas(input_data_1)
    creation_page.add_repas(input_data_2)
    creation_page.add_repas(input_data_3)

    assert creation_page.nb_repas == 3
    creation_page.delete_repas(1)
    assert creation_page.nb_repas == 2

    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.createur == mocked_authentification_user.agent.structure
    assert investigation.repas.count() == 2
    assert investigation.repas.first().denomination == "Foo"
    assert investigation.repas.last().denomination == "Buzz"


def test_can_create_investigation_tiac_with_repas_for_collectivite(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal
):
    departement = DepartementFactory()
    input_data: RepasSuspect = RepasSuspectFactory.build(
        departement=departement,
        type_repas=TypeRepas.RESTAURATION_COLLECTIVE,
        type_collectivite=TypeCollectivite.JEUNES_ENFANTS,
    )
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data.investigation)
    creation_page.add_repas(input_data)
    expect(creation_page.get_repas_card(0).get_by_text(input_data.denomination, exact=True)).to_be_visible()

    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.createur == mocked_authentification_user.agent.structure
    assert investigation.repas.count() == 1
    assert_models_are_equal(
        input_data, investigation.repas.get(), to_exclude=fields_to_exclude_repas, ignore_array_order=True
    )


def test_can_create_investigation_tiac_with_aliment_with_denomination_only(
    live_server, mocked_authentification_user, page: Page
):
    input_data: AlimentSuspect = AlimentSuspectFactory.build(simple=True)
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data.investigation)

    creation_page.page.get_by_test_id("add-aliment").click()
    creation_page.current_modal.locator("[id$=denomination]").fill(input_data.denomination)
    creation_page.current_modal.get_by_role("button", name="Enregistrer").click()

    card = creation_page.get_aliment_card(0)
    expect(card.get_by_text(input_data.denomination, exact=True)).to_be_visible()
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.aliments.count() == 1


def test_can_create_investigation_tiac_with_aliment_simple(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal
):
    input_data: AlimentSuspect = AlimentSuspectFactory.build(simple=True)
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data.investigation)

    creation_page.add_aliment_simple(input_data)
    card = creation_page.get_aliment_card(0)
    expect(card.get_by_text(input_data.denomination, exact=True)).to_be_visible()
    for motif in input_data.motif_suspicion:
        expect(card.get_by_text(MotifAliment(motif).label)).to_be_visible()
    expect(card.get_by_text("Matière première", exact=True)).to_be_visible()
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.aliments.count() == 1
    assert_models_are_equal(
        input_data, investigation.aliments.get(), to_exclude=fields_to_exclude_aliment, ignore_array_order=True
    )


def test_can_create_investigation_tiac_with_aliment_cuisine(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal
):
    input_data: AlimentSuspect = AlimentSuspectFactory.build(cuisine=True)
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data.investigation)

    creation_page.add_aliment_cuisine(input_data)
    card = creation_page.get_aliment_card(0)
    expect(card.get_by_text(input_data.denomination, exact=True)).to_be_visible()
    for motif in input_data.motif_suspicion:
        expect(card.get_by_text(MotifAliment(motif).label)).to_be_visible()
    expect(card.get_by_text("Aliment cuisiné", exact=True)).to_be_visible()
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.aliments.count() == 1
    assert_models_are_equal(
        input_data, investigation.aliments.get(), to_exclude=fields_to_exclude_aliment, ignore_array_order=True
    )


def test_can_create_investigation_tiac_with_aliment_and_edit(live_server, mocked_authentification_user, page: Page):
    input_data: AlimentSuspect = AlimentSuspectFactory.build(cuisine=True)
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data.investigation)
    creation_page.add_aliment_cuisine(input_data)
    assert creation_page.nb_aliments == 1
    creation_page.edit_aliment(0, denomination="Ma nouvelle dénomination")
    assert creation_page.nb_aliments == 1
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.createur == mocked_authentification_user.agent.structure
    assert investigation.aliments.get().denomination == "Ma nouvelle dénomination"


def test_can_add_and_cancel_aliment(live_server, page: Page, assert_models_are_equal):
    investigation: InvestigationTiac = InvestigationTiacFactory.build()
    input_data: AlimentSuspect = AlimentSuspectFactory.build(cuisine=True)

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(investigation)

    # Open modal, fill and delete
    creation_page.add_aliment_cuisine(input_data)
    creation_page.page.locator(".aliment-card").all()[0].get_by_role("button", name="Supprimer").click()
    creation_page.current_modal.get_by_role("button", name="Supprimer").click()

    # Open modal and cancel
    creation_page.page.get_by_test_id("add-aliment").click()
    creation_page.current_modal.wait_for(state="visible")
    creation_page.current_modal.get_by_role("button", name="Annuler").click()
    creation_page.current_modal.wait_for(state="hidden", timeout=2_000)

    creation_page.submit_as_draft()
    assert InvestigationTiac.objects.get().repas.count() == 0


def test_can_create_investigation_tiac_with_mutliple_aliments_and_delete(
    live_server, mocked_authentification_user, page: Page
):
    input_data_1: RepasSuspect = AlimentSuspectFactory.build(cuisine=True, denomination="Foo")
    input_data_2: RepasSuspect = AlimentSuspectFactory.build(cuisine=True, denomination="Bar")
    input_data_3: RepasSuspect = AlimentSuspectFactory.build(cuisine=True, denomination="Buzz")

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data_1.investigation)
    creation_page.add_aliment_cuisine(input_data_1)
    creation_page.add_aliment_cuisine(input_data_2)
    creation_page.add_aliment_cuisine(input_data_3)

    assert creation_page.nb_aliments == 3
    creation_page.delete_aliment(1)
    assert creation_page.nb_aliments == 2

    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.aliments.count() == 2
    assert investigation.aliments.first().denomination == "Foo"
    assert investigation.aliments.last().denomination == "Buzz"


def test_can_add_free_links(live_server, page: Page, choice_js_fill):
    evenement = InvestigationTiacFactory.build()
    other_event_1 = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    other_event_2 = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    other_event_3 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_free_link(other_event_1.numero, choice_js_fill)
    creation_page.add_free_link(other_event_2.numero, choice_js_fill, link_label="Enregistrement simple : ")
    creation_page.add_free_link(other_event_3.numero, choice_js_fill, link_label="Événement produit : ")
    creation_page.submit_as_draft()
    creation_page.page.wait_for_timeout(600)

    evenement = InvestigationTiac.objects.exclude(id=other_event_1.id).get()
    assert LienLibre.objects.count() == 3

    assert [lien.related_object_1 for lien in LienLibre.objects.all()] == [evenement, evenement, evenement]
    expected = sorted([other_event_1.numero, other_event_2.numero, other_event_3.numero])
    assert sorted([lien.related_object_2.numero for lien in LienLibre.objects.all()]) == expected


FIELD_TO_EXCLUDE_ANALYSE_ALIMENTAIRE = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "investigation_id",
    "suspicion_conclusion",
    "selected_hazard",
    "conclusion_comment",
]


def test_can_add_analyses_alimentaires(live_server, page: Page, assert_models_are_equal):
    investigation: InvestigationTiac = InvestigationTiacFactory.build()
    analyse: AnalyseAlimentaire = AnalyseAlimentaireFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(investigation)
    creation_page.add_analyse_alimentaire(analyse)

    assert creation_page.nb_analyse == 1

    creation_page.submit_as_draft()
    analyses = InvestigationTiac.objects.get().analyses_alimentaires.all()
    assert len(analyses) == 1
    assert_models_are_equal(
        analyse, analyses[0], to_exclude=FIELD_TO_EXCLUDE_ANALYSE_ALIMENTAIRE, ignore_array_order=True
    )


def test_can_add_and_cancel_analyses_alimentaires(live_server, page: Page, assert_models_are_equal):
    investigation: InvestigationTiac = InvestigationTiacFactory.build()
    analyse: AnalyseAlimentaire = AnalyseAlimentaireFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(investigation)

    # Open modal, fill and delete
    creation_page.add_analyse_alimentaire(analyse)
    creation_page.page.locator(".analyse-card").all()[0].get_by_role("button", name="Supprimer").click()
    creation_page.current_modal.get_by_role("button", name="Supprimer").click()

    # Open modal and cancel
    creation_page.page.locator(".analyses-alimentaires-fieldset").get_by_role("button", name="Ajouter").click()
    creation_page.current_modal.wait_for(state="visible")
    creation_page.current_modal.get_by_role("button", name="Annuler").click()
    creation_page.current_modal.wait_for(state="hidden", timeout=2_000)

    creation_page.submit_as_draft()
    assert InvestigationTiac.objects.get().analyses_alimentaires.count() == 0


def test_create_investigation_tiac_with_investigation_coordonnee_notification(live_server, page: Page, mailoutbox):
    input_data = InvestigationTiacFactory.build()
    contact_structure_mus = Contact.objects.get(structure__libelle=MUS_STRUCTURE)
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.set_follow_up(InvestigationFollowUp.INVESTIGATION_COORDONNEE)
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.follow_up == InvestigationFollowUp.INVESTIGATION_COORDONNEE
    expect(creation_page.page.get_by_text("L’évènement a été créé avec succès.")).to_be_visible()

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert set(mail.to) == {"text@example.com", contact_structure_mus.email}
    assert "Investigation coordonnée" in mail.subject


def test_can_create_etablissement_with_sirene_autocomplete(
    live_server, page: Page, ensure_departements, choice_js_fill_from_element, settings
):
    settings.SIRENE_CONSUMER_KEY = "FOO"
    settings.SIRENE_CONSUMER_SECRET = "BAR"
    ensure_departements("Paris")
    evenement = InvestigationTiacFactory.build()
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

    page.route("https://geo.api.gouv.fr/communes/.+", handle_insee_commune)

    creation_page = InvestigationTiacFormPage(page, live_server.url)

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


def test_ars_notified_is_checked_when_origin_is_ars(live_server, mocked_authentification_user, page: Page):
    input_data = InvestigationTiacFactory.build()
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    expect(creation_page.page.locator("#radio-id_notify_ars :checked")).to_have_value("False")
    expect(creation_page.page.locator("#radio-id_modalites_declaration :checked")).to_have_count(0)
    creation_page.evenement_origin.select_option("ARS")
    expect(creation_page.page.locator("#radio-id_notify_ars :checked")).to_have_value("True")
    expect(creation_page.page.locator("#radio-id_modalites_declaration :checked")).to_have_value("autre")

    creation_page.fill_required_fields(input_data)
    creation_page.submit()

    investigation = InvestigationTiac.objects.get()
    assert investigation.notify_ars is True
    assert investigation.modalites_declaration == ModaliteDeclarationEvenement.OTHER
