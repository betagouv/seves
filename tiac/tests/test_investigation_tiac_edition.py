from faker import Faker
from playwright.sync_api import Page

from tiac.factories import (
    InvestigationTiacFactory,
    EtablissementFactory,
    RepasSuspectFactory,
    AnalyseAlimentaireFactory,
    AlimentSuspectFactory,
)
from .pages import InvestigationTiacEditPage
from ..constants import SuspicionConclusion, DangersSyndromiques
from ..models import InvestigationTiac, Analyses


def test_can_edit_required_fields(live_server, page: Page, assert_models_are_equal):
    investigation = InvestigationTiacFactory(suspicion_conclusion=SuspicionConclusion.UNKNOWN)
    new_data = InvestigationTiacFactory.build(suspicion_conclusion=SuspicionConclusion.UNKNOWN)
    previous_count = InvestigationTiac.objects.count()

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()
    edit_page.fill_context_block(new_data)
    edit_page.submit()

    investigation.refresh_from_db()
    assert_models_are_equal(
        investigation,
        new_data,
        fields=[
            "date_reception",
            "evenement_origin",
            "modalites_declaration",
            "contenu",
            "notify_ars",
            "will_trigger_inquiry",
            "numero_sivss",
            "follow_up",
            "nb_sick_persons",
            "nb_sick_persons_to_hospital",
            "nb_dead_persons",
            "datetime_first_symptoms",
            "datetime_last_symptoms",
        ],
    )
    assert previous_count == InvestigationTiac.objects.count()


def test_can_edit_etiologie(live_server, page: Page, assert_models_are_equal, choose_different_values):
    investigation = InvestigationTiacFactory(
        suspicion_conclusion=SuspicionConclusion.UNKNOWN, with_danger_syndromiques_suspectes_count=3
    )

    new_danger_syndromique = choose_different_values(
        DangersSyndromiques.values, investigation.danger_syndromiques_suspectes, singleton=True
    )
    new_analyses_sur_les_malades = choose_different_values(
        list(Analyses), investigation.analyses_sur_les_malades, singleton=True
    )
    new_precision = Faker().sentence()

    previous_count = InvestigationTiac.objects.count()
    expected_danger_syndromique = [*investigation.danger_syndromiques_suspectes[:-1], new_danger_syndromique]

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    # Remove one danger syndromique and add one. One stay unchanged
    edit_page.page.locator(".etiologie-card-container").get_by_role("button", name="Supprimer").last.click()
    assert edit_page.get_dangers_syndromiques().count() == 2
    edit_page.add_danger_syndromique(DangersSyndromiques(new_danger_syndromique).label)
    assert edit_page.get_dangers_syndromiques().count() == 3
    edit_page.set_analyses(new_analyses_sur_les_malades.value)
    edit_page.precisions.fill(new_precision)

    edit_page.submit()

    investigation.refresh_from_db()
    assert_models_are_equal(
        investigation,
        {
            "danger_syndromiques_suspectes": expected_danger_syndromique,
            "analyses_sur_les_malades": new_analyses_sur_les_malades.label,
            "precisions": new_precision,
        },
        fields=[
            "danger_syndromiques_suspectes",
            "analyses_sur_les_malades",
            "precisions",
        ],
    )
    assert previous_count == InvestigationTiac.objects.count()


COMMON_FIELDS_TO_EXCLUDE = [
    "_state",
    "id",
    "departement_id",
    "investigation_id",
    "evenement_simple_id",
]


def test_can_edit_investigation_elements(
    live_server, page: Page, ensure_departements, assert_models_are_equal, choose_different_values
):
    departement, *_ = ensure_departements("Paris")

    investigation: InvestigationTiac = InvestigationTiacFactory(
        suspicion_conclusion=SuspicionConclusion.UNKNOWN,
        with_etablissements=3,
        with_etablissements__departement=departement,
        with_repas=3,
        with_repas__departement=departement,
        with_analyse_alimentaires=3,
        with_aliment_suspect=3,
    )
    new_etablissement = EtablissementFactory.build(departement=departement)
    etablissement_to_modify = EtablissementFactory.build()
    new_repas = RepasSuspectFactory.build(departement=departement)
    repas_to_modify = RepasSuspectFactory.build()
    new_aliment_suspect = AlimentSuspectFactory.build(cuisine=True)
    aliment_suspect_to_modify = AlimentSuspectFactory.build()
    new_analyse_alimentaire = AnalyseAlimentaireFactory.build()
    analyse_alimentaires_to_modify = AnalyseAlimentaireFactory.build()

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    edit_page.delete_etablissement(2)
    edit_page.edit_etablissement(1, enseigne_usuelle=etablissement_to_modify.enseigne_usuelle)
    edit_page.add_etablissement(new_etablissement)

    edit_page.delete_repas(2)
    edit_page.edit_repas(1, denomination=repas_to_modify.denomination)
    edit_page.add_repas(new_repas)

    edit_page.delete_aliment(2)
    edit_page.edit_aliment(1, denomination=aliment_suspect_to_modify.denomination)
    edit_page.add_aliment_cuisine(new_aliment_suspect)

    edit_page.delete_analyse_alimentaire(2)
    edit_page.edit_analyse_alimentaire(1, reference_prelevement=analyse_alimentaires_to_modify.reference_prelevement)
    edit_page.add_analyse_alimentaire(new_analyse_alimentaire)

    edit_page.submit()

    investigation.refresh_from_db()

    assert investigation.etablissements.count() == 3
    assert (
        investigation.etablissements.order_by("pk").all()[1].enseigne_usuelle
        == etablissement_to_modify.enseigne_usuelle
    )
    assert_models_are_equal(
        investigation.etablissements.order_by("pk").last(),
        new_etablissement,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE, "code_insee", "siret"],
    )

    assert investigation.repas.count() == 3
    assert investigation.repas.order_by("pk").all()[1].denomination == repas_to_modify.denomination
    assert_models_are_equal(
        investigation.repas.order_by("pk").last(),
        new_repas,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE],
        ignore_array_order=True,
    )

    assert investigation.aliments.count() == 3
    assert investigation.aliments.order_by("pk").all()[1].denomination == aliment_suspect_to_modify.denomination
    assert_models_are_equal(
        investigation.aliments.order_by("pk").last(),
        new_aliment_suspect,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE],
        ignore_array_order=True,
    )

    assert investigation.analyses_alimentaires.count() == 3
    assert (
        investigation.analyses_alimentaires.order_by("pk").all()[1].reference_prelevement
        == analyse_alimentaires_to_modify.reference_prelevement
    )
    assert_models_are_equal(
        investigation.analyses_alimentaires.order_by("pk").last(),
        new_analyse_alimentaire,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE],
        ignore_array_order=True,
    )
