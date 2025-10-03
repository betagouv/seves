from playwright.sync_api import Page, expect

from tiac.constants import DangersSyndromiques
from tiac.factories import InvestigationTiacFactory
from tiac.tests.pages import InvestigationTiacDetailsPage


def test_evenement_produit_detail_page_content(live_server, page: Page):
    evenement = InvestigationTiacFactory(nb_sick_persons=22, nb_sick_persons_to_hospital=44, nb_dead_persons=3)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.title.text_content() == f"Événement {evenement.numero}"
    assert "Dernière mise à jour" in details_page.last_modification.text_content()

    expect(details_page.context_block.get_by_text(str(evenement.createur), exact=True)).to_be_visible()
    expect(
        details_page.context_block.get_by_text(evenement.date_creation.strftime("%d/%m/%Y"), exact=True)
    ).to_be_visible()
    expect(
        details_page.context_block.get_by_text(evenement.date_reception.strftime("%d/%m/%Y"), exact=True)
    ).to_be_visible()
    expect(details_page.origin.get_by_text(evenement.get_evenement_origin_display(), exact=True)).to_be_visible()
    expect(details_page.modalite.get_by_text(evenement.get_modalites_declaration_display(), exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text(evenement.contenu, exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text(evenement.numero_sivss, exact=True)).to_be_visible()
    expect(details_page.context_block.get_by_text("Investigation de TIAC", exact=True)).to_be_visible()

    expect(details_page.cas_block.get_by_text("22", exact=True)).to_be_visible()
    expect(details_page.cas_block.get_by_text("44", exact=True)).to_be_visible()
    expect(details_page.cas_block.get_by_text("3", exact=True)).to_be_visible()

    expected_date = evenement.datetime_first_symptoms.strftime("%d/%m/%Y  à %H:%M")
    expect(details_page.cas_block.get_by_text(expected_date, exact=True)).to_be_visible()

    expected_date = evenement.datetime_last_symptoms.strftime("%d/%m/%Y  à %H:%M")
    expect(details_page.cas_block.get_by_text(expected_date, exact=True)).to_be_visible()

    for motif in evenement.danger_syndromiques_suspectes:
        expect(details_page.etiologie_block.get_by_text(DangersSyndromiques(motif).help_text)).to_be_visible()
