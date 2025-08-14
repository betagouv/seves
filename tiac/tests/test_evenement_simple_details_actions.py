from playwright.sync_api import expect

from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple
from .pages import EvenementSimpleDetailsPage


def test_can_delete_evenement_simple(live_server, page):
    evenement = EvenementSimpleFactory()
    assert EvenementSimple.objects.count() == 1

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'évènement {evenement.numero} a bien été supprimé")).to_be_visible()

    assert EvenementSimple.objects.count() == 0
    assert EvenementSimple._base_manager.get().pk == evenement.pk
