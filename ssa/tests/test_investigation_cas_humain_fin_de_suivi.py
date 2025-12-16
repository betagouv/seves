from django.urls import reverse

from core.tests.generic_tests.fin_suivi import (
    generic_test_can_add_fin_de_suivi,
    generic_test_can_filter_by_fin_de_suivi,
)
from ssa.factories import InvestigationCasHumainFactory
from ssa.models import EvenementProduit


def test_can_add_fin_de_suivi(live_server, page, mailoutbox, mocked_authentification_user):
    generic_test_can_add_fin_de_suivi(
        live_server,
        page,
        InvestigationCasHumainFactory(etat=EvenementProduit.Etat.EN_COURS),
        mailoutbox,
        mocked_authentification_user,
    )


def test_can_filter_by_fin_de_suivi(live_server, page, mocked_authentification_user):
    generic_test_can_filter_by_fin_de_suivi(
        live_server,
        page,
        InvestigationCasHumainFactory,
        reverse("ssa:evenements-liste"),
        mocked_authentification_user,
    )
