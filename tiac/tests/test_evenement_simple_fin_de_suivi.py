from core.tests.generic_tests.fin_suivi import generic_test_can_add_fin_de_suivi
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple


def test_can_add_fin_de_suivi(live_server, page, mailoutbox, mocked_authentification_user):
    generic_test_can_add_fin_de_suivi(
        live_server,
        page,
        EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS),
        mailoutbox,
        mocked_authentification_user,
    )
