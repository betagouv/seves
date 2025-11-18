from core.tests.generic_tests.fin_suivi import generic_test_can_add_fin_de_suivi
from sv.factories import EvenementFactory


def test_can_add_fin_de_suivi(live_server, page, mailoutbox, mocked_authentification_user):
    generic_test_can_add_fin_de_suivi(live_server, page, EvenementFactory(), mailoutbox, mocked_authentification_user)
