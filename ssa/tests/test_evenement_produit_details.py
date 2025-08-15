import json
import pytest
from playwright.sync_api import Page, expect

from core.factories import StructureFactory
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitDetailsPage


def test_evenement_produit_detail_page_content(live_server, page: Page):
    evenement = EvenementProduitFactory(bacterie=True, numeros_rappel_conso=["1999-01-0123"])

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    assert details_page.title.text_content() == f"Événement {evenement.numero}"
    assert "Dernière mise à jour" in details_page.last_modification.text_content()

    expect(details_page.information_block.get_by_text(str(evenement.createur), exact=True)).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.numero_rasff, exact=True)).to_be_visible()
    type_evenement = details_page.information_block.get_by_text(evenement.get_type_evenement_display(), exact=True)
    expect(type_evenement).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.get_source_display(), exact=True)).to_be_visible()
    expect(details_page.information_block.get_by_text(evenement.description, exact=True)).to_be_visible()

    expect(
        details_page.produit_block.get_by_text(evenement.get_categorie_produit_display(), exact=True)
    ).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.denomination, exact=True)).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.marque, exact=True)).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.lots, exact=True)).to_be_visible()
    expect(details_page.produit_block.get_by_text(evenement.description_complementaire, exact=True)).to_be_visible()
    temperature = details_page.produit_block.get_by_text(evenement.get_temperature_conservation_display(), exact=True)
    expect(temperature).to_be_visible()

    expect(details_page.risque_block.get_by_text(evenement.get_categorie_danger_display(), exact=True)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.precision_danger, exact=True)).to_be_visible()
    quantification_str = f"{evenement.quantification} {evenement.get_quantification_unite_display()}"
    quantification = details_page.risque_block.get_by_text(quantification_str)
    expect(quantification).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.evaluation, exact=True)).to_be_visible()
    produit_pam = details_page.risque_block.get_by_text(evenement.get_produit_pret_a_manger_display(), exact=True)
    expect(produit_pam).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.reference_souches, exact=True)).to_be_visible()
    expect(details_page.risque_block.get_by_text(evenement.reference_clusters, exact=True)).to_be_visible()

    expect(details_page.actions_block.get_by_text(evenement.get_actions_engagees_display())).to_be_visible()
    expect(details_page.rappel_block.get_by_text("1999-01-0123")).to_be_visible()


def test_evenement_produit_detail_wont_show_pam_if_not_danger_bacterien(live_server, page: Page):
    evenement = EvenementProduitFactory(not_bacterie=True)
    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    expect(details_page.page.get_by_text("Produit prêt à manger (PAM)", exact=True)).not_to_be_visible()


def test_evenement_produit_detail_page_content_etablissement(
    live_server, page: Page, assert_etablissement_card_is_correct
):
    evenement = EvenementProduitFactory()
    etablissement = EtablissementFactory(evenement_produit=evenement)

    details_page = EvenementProduitDetailsPage(page, live_server.url)
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
