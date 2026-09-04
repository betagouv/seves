from playwright.sync_api import expect

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
