from core.tests.generic_tests.contacts import (
    generic_test_add_contact_agent_to_an_evenement,
    generic_test_add_contact_structure_to_an_evenement,
    generic_test_remove_contact_agent_from_an_evenement,
    generic_test_remove_contact_structure_from_an_evenement,
    generic_test_add_multiple_contacts_agents_to_an_evenement,
)
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac


def test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, evenement, mailoutbox)


def test_add_contact_structure_to_an_investigation_tiac(live_server, page, choice_js_fill, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, evenement, mailoutbox)


def test_remove_contact_agent_from_an_evenement(live_server, page, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_remove_contact_agent_from_an_evenement(live_server, page, evenement, mailoutbox)


def test_remove_contact_structure_from_an_evenement(live_server, page, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_remove_contact_structure_from_an_evenement(live_server, page, evenement, mailoutbox)


def test_add_multiple_contacts_agents_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_add_multiple_contacts_agents_to_an_evenement(live_server, page, evenement, choice_js_fill, mailoutbox)
