from core.tests.generic_tests.fin_suivi import generic_test_can_add_fin_de_suivi
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac


def test_can_add_fin_de_suivi(live_server, page, mailoutbox, mocked_authentification_user):
    generic_test_can_add_fin_de_suivi(
        live_server,
        page,
        InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS),
        mailoutbox,
        mocked_authentification_user,
    )
