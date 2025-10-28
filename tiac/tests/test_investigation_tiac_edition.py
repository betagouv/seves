from playwright.sync_api import Page

from tiac.factories import (
    InvestigationTiacFactory,
)
from .pages import InvestigationTiacEditPage
from ..constants import SuspicionConclusion
from ..models import InvestigationTiac


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
