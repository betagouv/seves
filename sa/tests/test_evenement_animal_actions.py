from playwright.sync_api import expect

from core.tests.generic_tests.actions import (
    generic_test_can_cloturer_evenement,
)

from ..models import EvenementAnimal
from .factories import EvenementAnimalFactory
from .pages import EvenementAnimalDetailsPage


def test_can_delete_evenement_animal(live_server, page):
    evenement = EvenementAnimalFactory()
    assert EvenementAnimal.objects.count() == 1

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L’événement {evenement.numero} a bien été supprimé.")).to_be_visible()

    assert EvenementAnimal.objects.count() == 0
    assert EvenementAnimal._base_manager.get().pk == evenement.pk


def test_can_cloturer_evenement(live_server, page, mocked_authentification_user, mailoutbox):
    evenement = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)
    generic_test_can_cloturer_evenement(
        live_server, page, evenement, mocked_authentification_user, mailoutbox, nav_name="Clôturer l'événement"
    )


def test_can_cloturer_investigation_if_last_remaining_structure(
    live_server, page, mocked_authentification_user, mus_contact
):
    ac_structure = mus_contact.structure
    evenement = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS, createur=ac_structure)
    mocked_authentification_user.agent.structure = ac_structure
    evenement.contacts.add(mus_contact)

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer(wording="Clôturer l'événement")

    evenement.refresh_from_db()
    assert evenement.etat == EvenementAnimal.Etat.CLOTURE
    assert page.get_by_text("Fin de suivi").count() == 2
    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
