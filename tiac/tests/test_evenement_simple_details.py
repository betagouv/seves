from playwright.sync_api import Page, expect

from core.models import LienLibre
from tiac.factories import EvenementSimpleFactory, EtablissementFactory
from tiac.models import EvenementSimple, Etablissement
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


def test_evenement_simple_detail_page_content_etablissement(
    live_server, page: Page, assert_etablissement_card_is_correct
):
    evenement = EvenementSimpleFactory()
    etablissement: Etablissement = EtablissementFactory(evenement_simple=evenement, inspection=True)

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    etablissement_card = details_page.etablissement_card()
    assert_etablissement_card_is_correct(etablissement_card, etablissement)

    details_page.etablissement_open_modal()
    expect(details_page.etablissement_modal.get_by_text(etablissement.raison_sociale, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.type_etablissement, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.siret, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.enseigne_usuelle, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.adresse_lieu_dit, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.commune, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(str(etablissement.departement), exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.numero_resytal, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.evaluation, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.commentaire, exact=True)).to_be_visible()
