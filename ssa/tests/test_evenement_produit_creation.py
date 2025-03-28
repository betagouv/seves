from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitCreationPage


def test_can_create_evenement_produit_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.type_evenement == input_data.type_evenement
    assert evenement_produit.description == input_data.description
    assert evenement_produit.denomination == input_data.denomination
    assert evenement_produit.numero is not None
    assert evenement_produit.is_draft is True


def test_can_create_evenement_produit_with_all_fields(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.source.select_option(input_data.source)
    creation_page.cerfa_recu.select_option(input_data.cerfa_recu)

    creation_page.marque.fill(input_data.marque)
    creation_page.lots.fill(input_data.lots)
    creation_page.description_complementaire.fill(input_data.description_complementaire)
    creation_page.set_temperature_conservation(input_data.temperature_conservation)
    creation_page.set_pret_a_manger(input_data.produit_pret_a_manger)

    creation_page.quantification.fill(str(input_data.quantification))
    creation_page.quantification_unite.select_option(input_data.quantification_unite)
    creation_page.evaluation.fill(input_data.evaluation)
    creation_page.reference_souches.fill(input_data.reference_souches)
    creation_page.reference_clusters.fill(input_data.reference_clusters)

    creation_page.actions_engagees.select_option(input_data.actions_engagees)
    creation_page.submit_as_draft()

    evenement_produit = EvenementProduit.objects.get()

    fields_to_exclude = ["_state", "id", "numero_annee", "numero_evenement", "date_creation", "numero_rasff"]
    evenement_produit_data = {k: v for k, v in evenement_produit.__dict__.items() if k not in fields_to_exclude}
    input_data = {k: v for k, v in input_data.__dict__.items() if k not in fields_to_exclude}

    assert evenement_produit_data == input_data


def test_can_publish_evenement_produit(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.publish()

    evenement_produit = EvenementProduit.objects.get()
    assert evenement_produit.createur == mocked_authentification_user.agent.structure
    assert evenement_produit.type_evenement == input_data.type_evenement
    assert evenement_produit.description == input_data.description
    assert evenement_produit.denomination == input_data.denomination
    assert evenement_produit.numero is not None
    assert evenement_produit.is_draft is False


def test_ac_can_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    structure = mocked_authentification_user.agent.structure
    structure.niveau1 = AC_STRUCTURE
    structure.save()
    input_data = EvenementProduitFactory.build()
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.numero_rasff.fill("2024.2222")
    creation_page.submit_as_draft()


def test_non_ac_cant_fill_rasff_number(live_server, mocked_authentification_user, page: Page):
    creation_page = EvenementProduitCreationPage(page, live_server.url)
    creation_page.navigate()
    expect(creation_page.numero_rasff).not_to_be_visible()
