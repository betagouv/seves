from playwright.sync_api import Page

from ssa.factories import InvestigationCasHumainFactory
from ssa.models import EvenementInvestigationCasHumain
from ssa.tests.pages import InvestigationCasHumainFormPage

FIELD_TO_EXCLUDE_ETABLISSEMENT = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "code_insee",
    "evenement_produit_id",
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

    evenement_produit = EvenementInvestigationCasHumain.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.type_evenement == input_data.type_evenement
    assert evenement_produit.description == input_data.description
    assert evenement_produit.numero is not None
    assert evenement_produit.is_draft is True
