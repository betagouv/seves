from playwright.sync_api import expect

from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac
from .pages import InvestigationTiacDetailsPage


def test_can_delete_investigation_tiac(live_server, page):
    evenement = InvestigationTiacFactory()
    assert InvestigationTiac.objects.count() == 1

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'investigation TIAC {evenement.numero} a bien été supprimée")).to_be_visible()

    assert InvestigationTiac.objects.count() == 0
    assert InvestigationTiac._base_manager.get().pk == evenement.pk
