from playwright.sync_api import Page, expect

from core.tests.generic_tests.actions import generic_test_can_cloturer_evenement
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitDetailsPage


def test_can_delete_evenement_produit(live_server, page):
    evenement = EvenementProduitFactory()
    assert EvenementProduit.objects.count() == 1

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'évènement {evenement.numero} a bien été supprimé")).to_be_visible()

    assert EvenementProduit.objects.count() == 0
    assert EvenementProduit._base_manager.get().pk == evenement.pk


def test_can_cloturer_evenement(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    generic_test_can_cloturer_evenement(live_server, page, evenement, mocked_authentification_user, mailoutbox)


def test_can_cloturer_evenement_produit_if_last_remaining_structure(
    live_server, page: Page, mocked_authentification_user, mus_contact
):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS, createur=mus_contact.structure)
    mocked_authentification_user.agent.structure = mus_contact.structure
    evenement.contacts.add(mus_contact)

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer()

    evenement.refresh_from_db()
    assert evenement.etat == EvenementProduit.Etat.CLOTURE
    assert page.get_by_text("Fin de suivi").count() == 2
    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()


def test_can_publish_evenement_produit(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.BROUILLON)

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.publish()

    evenement.refresh_from_db()
    assert evenement.etat == EvenementProduit.Etat.EN_COURS
    expect(page.get_by_text("En cours", exact=True)).to_be_visible()
    expect(page.get_by_text("Événement produit publié avec succès")).to_be_visible()


def test_can_edit_evenement_produit(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementProduitFactory()

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.edit()
    page.wait_for_url(f"**{evenement.get_update_url()}")


def test_can_download_document_evenement_produit(live_server, page):
    evenement = EvenementProduitFactory()

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    with page.expect_download() as download_info:
        details_page.download()

    download = download_info.value
    assert download.suggested_filename == f"evenement_produit_{evenement.numero}.docx"
