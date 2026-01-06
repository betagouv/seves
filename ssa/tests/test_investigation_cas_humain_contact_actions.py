from core.tests.generic_tests.contacts import (
    generic_test_add_contact_agent_to_an_evenement,
    generic_test_add_contact_structure_to_an_evenement,
    generic_test_remove_contact_agent_from_an_evenement,
    generic_test_remove_contact_structure_from_an_evenement,
    generic_test_add_multiple_contacts_agents_to_an_evenement,
    generic_test_add_contact_structure_to_an_evenement_with_dedicated_email,
    generic_test_cant_add_contact_agent_if_he_cant_access_domain,
    generic_test_cant_add_contact_structure_if_any_agent_cant_access_domain,
)
from ssa.factories import InvestigationCasHumainFactory
from ssa.models import EvenementInvestigationCasHumain


def test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, evenement, mailoutbox)


def test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, evenement, mailoutbox)


def test_add_contact_structure_to_an_evenement_with_dedicated_email(live_server, page, choice_js_fill, mailoutbox):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_add_contact_structure_to_an_evenement_with_dedicated_email(
        live_server, page, choice_js_fill, evenement, mailoutbox, domain="ssa"
    )


def test_remove_contact_agent_from_an_evenement(live_server, page, mailoutbox):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_remove_contact_agent_from_an_evenement(live_server, page, evenement, mailoutbox)


def test_remove_contact_structure_from_an_evenement(live_server, page, mailoutbox):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_remove_contact_structure_from_an_evenement(live_server, page, evenement, mailoutbox)


def test_add_multiple_contacts_agents_to_an_evenement(live_server, page, choice_js_fill, mailoutbox):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_add_multiple_contacts_agents_to_an_evenement(live_server, page, evenement, choice_js_fill, mailoutbox)


def test_cant_add_contact_agent_if_he_cant_access_domain(live_server, page, choice_js_cant_pick):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_cant_add_contact_agent_if_he_cant_access_domain(
        live_server,
        page,
        choice_js_cant_pick,
        evenement,
    )


def test_cant_add_contact_structure_if_any_agent_cant_access_domain(live_server, page, choice_js_cant_pick):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_cant_add_contact_structure_if_any_agent_cant_access_domain(
        live_server,
        page,
        choice_js_cant_pick,
        evenement,
    )
