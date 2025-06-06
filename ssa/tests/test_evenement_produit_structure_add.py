from core.tests.generic_tests.contacts import generic_test_add_contact_structure_to_an_evenement
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit


def test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, evenement)
