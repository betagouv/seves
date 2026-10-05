from django.urls import reverse

from core.tests.generic_tests.fin_suivi import (
    generic_test_can_add_fin_de_suivi,
    generic_test_can_filter_by_fin_de_suivi,
)
from sa.models import EvenementAnimal

from .factories import EvenementAnimalFactory


def test_can_add_fin_de_suivi(live_server, page, mailoutbox, mocked_authentification_user):
    generic_test_can_add_fin_de_suivi(
        live_server,
        page,
        EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS),
        mailoutbox,
        mocked_authentification_user,
    )


def test_can_filter_by_fin_de_suivi(live_server, page, mocked_authentification_user):
    generic_test_can_filter_by_fin_de_suivi(
        live_server,
        page,
        EvenementAnimalFactory,
        reverse("sa:evenement-liste"),
        mocked_authentification_user,
    )
