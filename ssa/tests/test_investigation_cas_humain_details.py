from playwright.sync_api import Page, expect

from ssa.factories import InvestigationCasHumainFactory, EtablissementFactory
from ssa.tests.pages import InvestigationCasHumainDetailsPage


def test_investigation_cas_humain_detail_page_content(live_server, page: Page):
    evenement = InvestigationCasHumainFactory()

    details_page = InvestigationCasHumainDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.title.text_content() == f"Événement {evenement.numero}"
    assert "Dernière mise à jour" in details_page.last_modification.text_content()

    expect(details_page.information_block.get_by_text(str(evenement.createur), exact=True)).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.numero_rasff, exact=True)).to_be_visible()
    type_evenement = details_page.information_block.get_by_text(evenement.get_type_evenement_display(), exact=True)
    expect(type_evenement).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.get_source_display(), exact=True)).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.description, exact=True)).to_be_visible()

    expect(details_page.risque_block.get_by_text(evenement.get_categorie_danger_display(), exact=True)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.precision_danger, exact=True)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.evaluation, exact=True)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.reference_souches, exact=True)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.reference_clusters, exact=True)).to_be_visible()


def test_investigation_cas_humain_detail_page_content_etablissement(
    live_server, page: Page, assert_etablissement_card_is_correct
):
    evenement = InvestigationCasHumainFactory()
    etablissement = EtablissementFactory(investigation_cas_humain=evenement)

    details_page = InvestigationCasHumainDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    etablissement_card = details_page.etablissement_card()
    assert_etablissement_card_is_correct(etablissement_card, etablissement)

    details_page.etablissement_open_modal()
    expect(details_page.etablissement_modal.get_by_text(etablissement.raison_sociale, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.siret, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.adresse_lieu_dit, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.commune, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(f"{etablissement.departement}")).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.pays.name, exact=True)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.type_exploitant, exact=True)).to_be_visible()
    expect(
        details_page.etablissement_modal.get_by_text(etablissement.get_position_dossier_display(), exact=True)
    ).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.numero_agrement, exact=True)).to_be_visible()
