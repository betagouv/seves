from faker import Faker
from playwright.sync_api import Page

from tiac.factories import (
    InvestigationTiacFactory,
)
from .pages import InvestigationTiacEditPage
from ..constants import SuspicionConclusion, DangersSyndromiques
from ..models import InvestigationTiac, Analyses


def test_can_edit_required_fields(live_server, mocked_authentification_user, page: Page, assert_models_are_equal):
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


def test_can_edit_etiologie(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal, choose_different_values
):
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
