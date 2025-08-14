from playwright.sync_api import Page, expect

from core.models import LienLibre
from tiac.factories import EvenementSimpleFactory
from tiac.models import EvenementSimple
from tiac.tests.pages import EvenementSimpleDetailsPage


def test_evenement_simple_detail_page_content(live_server, page: Page):
    evenement: EvenementSimple = EvenementSimpleFactory()

    other_evenement = EvenementSimpleFactory()
    LienLibre.objects.create(related_object_1=evenement, related_object_2=other_evenement)

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.title.text_content() == f"Événement {evenement.numero}"
    assert "Dernière mise à jour" in details_page.last_modification.text_content()

    expect(details_page.context_block.get_by_text(str(evenement.createur), exact=True)).to_be_visible()
    expect(
        details_page.context_block.get_by_text(evenement.date_reception.strftime("%d/%m/%Y"), exact=True)
    ).to_be_visible()
    expect(details_page.origin.get_by_text(evenement.get_evenement_origin_display(), exact=True)).to_be_visible()
    expect(details_page.modalite.get_by_text(evenement.get_modalites_declaration_display(), exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text(evenement.contenu, exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text("Oui" if evenement.notify_ars else "Non", exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text(str(evenement.nb_sick_persons), exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text("Enregistrement simple", exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text(evenement.get_follow_up_display(), exact=True)).to_be_visible()

    expect(details_page.links_block.get_by_text(other_evenement.numero, exact=True)).to_be_visible()
