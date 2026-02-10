from playwright.sync_api import Page, expect

from tiac.constants import DangersSyndromiques
from tiac.factories import (
    AlimentSuspectFactory,
    AnalyseAlimentaireFactory,
    EtablissementFactory,
    InvestigationTiacFactory,
    RepasSuspectFactory,
)
from tiac.tests.pages import InvestigationTiacDetailsPage


def test_evenement_produit_detail_page_content(live_server, page: Page):
    evenement = InvestigationTiacFactory(nb_sick_persons=22, nb_sick_persons_to_hospital=44, nb_dead_persons=3)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
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


def test_evenement_produit_detail_page_content_etablissement(
    live_server, page: Page, assert_etablissement_card_is_correct
):
    evenement = InvestigationTiacFactory()
    etablissement = EtablissementFactory(investigation=evenement, inspection=True)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    etablissement_card = details_page.etablissement_card()
    assert_etablissement_card_is_correct(etablissement_card, etablissement)

    details_page.etablissement_open_modal()
    expect(details_page.current_modal.get_by_text(etablissement.raison_sociale, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.type_etablissement, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.siret, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.numero_agrement, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.autre_identifiant, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.enseigne_usuelle, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.adresse_lieu_dit, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.commune, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(str(etablissement.departement), exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.numero_resytal, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.evaluation, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(etablissement.commentaire, exact=True)).to_be_visible()


def test_evenement_produit_detail_page_content_aliment_cuisine(live_server, page: Page):
    evenement = InvestigationTiacFactory()
    aliment = AlimentSuspectFactory(investigation=evenement, cuisine=True)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    card = details_page.aliment_card()
    expect(card.get_by_text(aliment.denomination, exact=True)).to_be_visible()
    expect(card.get_by_text(aliment.get_type_aliment_display(), exact=True)).to_be_visible()
    expect(card.get_by_text(aliment.motif_suspicion_labels, exact=True)).to_be_visible()

    details_page.aliment_open_modal()
    expect(details_page.current_modal.get_by_text(aliment.denomination, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(aliment.get_type_aliment_display(), exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(aliment.motif_suspicion_labels, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(aliment.description_composition, exact=True)).to_be_visible()


def test_evenement_produit_detail_page_content_aliment_simple(live_server, page: Page):
    evenement = InvestigationTiacFactory()
    aliment = AlimentSuspectFactory(investigation=evenement, simple=True)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    card = details_page.aliment_card()
    expect(card.get_by_text(aliment.denomination, exact=True)).to_be_visible()
    expect(card.get_by_text(aliment.get_type_aliment_display(), exact=True)).to_be_visible()
    expect(card.get_by_text(aliment.motif_suspicion_labels, exact=True)).to_be_visible()

    details_page.aliment_open_modal()
    expect(details_page.current_modal.get_by_text(aliment.denomination, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(aliment.get_type_aliment_display(), exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(aliment.motif_suspicion_labels, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(aliment.get_categorie_produit_display(), exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(aliment.description_produit, exact=True)).to_be_visible()


def test_evenement_produit_detail_page_content_repas(live_server, page: Page):
    evenement = InvestigationTiacFactory()
    repas = RepasSuspectFactory(investigation=evenement)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    card = details_page.repas_card()
    expect(card.get_by_text(repas.denomination, exact=True)).to_be_visible()
    expect(card.get_by_text(repas.get_type_repas_display(), exact=True)).to_be_visible()
    expect(card.get_by_text(repas.nombre_participant, exact=True)).to_be_visible()

    details_page.repas_open_modal()
    expect(details_page.current_modal.get_by_text(repas.denomination, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(repas.menu, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(repas.motif_suspicion_labels, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(str(repas.departement), exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(repas.get_type_repas_display(), exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(repas.nombre_participant, exact=True)).to_be_visible()


def test_evenement_produit_detail_page_content_analyse_alimentaires(live_server, page: Page):
    evenement = InvestigationTiacFactory()
    analyse = AnalyseAlimentaireFactory(investigation=evenement)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    card = details_page.analyse_card()
    expect(card.get_by_text(analyse.reference_prelevement, exact=True)).to_be_visible()
    expect(card.get_by_text(analyse.get_etat_prelevement_display(), exact=True)).to_be_visible()
    for danger in analyse.categorie_danger_labels:
        expect(card.get_by_text(danger, exact=True)).to_be_visible()

    details_page.analyse_open_modal()
    expect(details_page.current_modal.get_by_text(analyse.reference_prelevement, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(analyse.get_etat_prelevement_display(), exact=True)).to_be_visible()
    for danger in analyse.categorie_danger_labels:
        expect(details_page.current_modal.get_by_text(danger, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(analyse.comments, exact=True)).to_be_visible()
    expect(details_page.current_modal.get_by_text(analyse.reference_souche, exact=True)).to_be_visible()
