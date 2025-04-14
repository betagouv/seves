import json
import pytest
from playwright.sync_api import Page, expect

from core.factories import StructureFactory
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitDetailsPage


def test_evenement_produit_detail_page_content(live_server, page: Page):
    evenement = EvenementProduitFactory(numeros_rappel_conso=["1999-01-0123"])

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.title.text_content() == f"Événement {evenement.numero}"
    assert "Dernière mise à jour" in details_page.last_modification.text_content()

    expect(details_page.information_block.get_by_text(str(evenement.createur))).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.numero_rasff)).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.get_type_evenement_display())).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.get_source_display())).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.get_cerfa_recu_display())).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.description)).to_be_visible()

    expect(details_page.produit_block.get_by_text(evenement.denomination)).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.marque)).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.lots)).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.description_complementaire)).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.get_temperature_conservation_display())).to_be_visible()

    expect(
        details_page.risque_block.get_by_text(
            f"{evenement.quantification} {evenement.get_quantification_unite_display()}"
        )
    ).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.evaluation)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.get_produit_pret_a_manger_display())).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.reference_souches)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.reference_clusters)).to_be_visible()

    expect(details_page.actions_block.get_by_text(evenement.get_actions_engagees_display())).to_be_visible()
    expect(details_page.rappel_block.get_by_text("1999-01-0123")).to_be_visible()


def test_evenement_produit_detail_page_content_etablissement(live_server, page: Page):
    evenement = EvenementProduitFactory()
    etablissement = EtablissementFactory(evenement_produit=evenement)

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    etablissement_card = details_page.etablissement_card()
    expect(etablissement_card.get_by_text(etablissement.raison_sociale)).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.pays.name)).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.get_type_exploitant_display())).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.departement)).to_be_visible()
    expect(etablissement_card.get_by_text(etablissement.get_position_dossier_display())).to_be_visible()

    details_page.etablissement_open_modal()
    expect(details_page.etablissement_modal.get_by_text(etablissement.raison_sociale)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.siret)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.adresse_lieu_dit)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.commune)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.departement)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.pays.name)).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.get_type_exploitant_display())).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.get_position_dossier_display())).to_be_visible()
    expect(details_page.etablissement_modal.get_by_text(etablissement.numero_agrement)).to_be_visible()


def test_evenement_produit_detail_page_link_to_rappel_conso(live_server, page: Page):
    def handle(route):
        data = {"nhits": 1, "records": [{"fields": {"id": 1234}}]}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(data))

    evenement = EvenementProduitFactory(numeros_rappel_conso=["2025-03-0176"])

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.page.route(
        "https://data.economie.gouv.fr/api/records/1.0/search/?dataset=rappelconso-v2-gtin-espaces&refine.numero_fiche=2025-03-0176",
        handle,
    )

    details_page.navigate(evenement)

    assert (
        details_page.rappel_block.get_by_role("link", name="2025-03-0176").get_attribute("href")
        == "https://rappel.conso.gouv.fr/fiche-rappel/1234/Interne"
    )
    assert details_page.rappel_block.get_by_role("link", name="2025-03-0176").get_attribute("target") == "_blank"


def test_evenement_produit_detail_page_access_createur(live_server, page: Page):
    for etat in [EvenementProduit.Etat.BROUILLON, EvenementProduit.Etat.EN_COURS, EvenementProduit.Etat.CLOTURE]:
        evenement = EvenementProduitFactory(etat=etat)
        details_page = EvenementProduitDetailsPage(page, live_server.url)
        response = details_page.navigate(evenement)
        assert response.status == 200


@pytest.mark.parametrize(
    "etat,status_code",
    [
        (EvenementProduit.Etat.BROUILLON, 403),
        (EvenementProduit.Etat.EN_COURS, 200),
        (EvenementProduit.Etat.CLOTURE, 200),
    ],
)
def test_evenement_produit_detail_page_access_other_structure(live_server, page: Page, etat, status_code):
    evenement = EvenementProduitFactory(etat=etat, createur=StructureFactory())
    details_page = EvenementProduitDetailsPage(page, live_server.url)
    response = details_page.navigate(evenement)
    assert response.status == status_code
