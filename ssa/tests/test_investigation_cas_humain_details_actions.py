from playwright.sync_api import Page, expect

from core.tests.generic_tests.actions import generic_test_can_cloturer_evenement
from ssa.factories import InvestigationCasHumainFactory
from ssa.models import EvenementInvestigationCasHumain
from ssa.tests.pages import InvestigationCasHumainDetailsPage


def test_can_delete_investigation_cas_humain(live_server, page):
    evenement = InvestigationCasHumainFactory()
    assert EvenementInvestigationCasHumain.objects.count() == 1

    details_page = InvestigationCasHumainDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'investigation de cas humain {evenement.numero} a bien été supprimée")).to_be_visible()

    assert EvenementInvestigationCasHumain.objects.count() == 0
    assert EvenementInvestigationCasHumain._base_manager.get().pk == evenement.pk


def test_can_cloturer_investigation_cas_humain(live_server, page: Page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationCasHumainFactory(etat=EvenementInvestigationCasHumain.Etat.EN_COURS)
    generic_test_can_cloturer_evenement(live_server, page, evenement, mocked_authentification_user, mailoutbox)


def test_can_cloturer_investigation_cas_humain_if_last_remaining_structure(
    live_server, page: Page, mocked_authentification_user, mus_contact
):
    evenement = InvestigationCasHumainFactory(
        etat=EvenementInvestigationCasHumain.Etat.EN_COURS, createur=mus_contact.structure
    )
    mocked_authentification_user.agent.structure = mus_contact.structure
    evenement.contacts.add(mus_contact)

    details_page = InvestigationCasHumainDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer()

    evenement.refresh_from_db()
    assert evenement.etat == EvenementInvestigationCasHumain.Etat.CLOTURE
    assert page.get_by_text("Fin de suivi").count() == 2
    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()


def test_can_download_document_evenement_produit(live_server, page):
    evenement = InvestigationCasHumainFactory()

    details_page = InvestigationCasHumainDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    with page.expect_download() as download_info:
        details_page.download()

    download = download_info.value
    assert download.suggested_filename == f"investigtion_cas_humain_{evenement.numero}.docx"
