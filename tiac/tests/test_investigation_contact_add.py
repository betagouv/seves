from core.tests.generic_tests.contacts import generic_test_add_contact_agent_to_an_evenement
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac


def test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, evenement)
