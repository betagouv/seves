from core.tests.generic_tests.contacts import generic_test_add_contact_structure_to_an_evenement
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple


def test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill):
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, evenement)
