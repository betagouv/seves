from playwright.sync_api import expect

from core.tests.generic_tests.actions import generic_test_can_cloturer_evenement
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac

from .pages import InvestigationTiacDetailsPage


def test_can_delete_investigation_tiac(live_server, page):
    evenement = InvestigationTiacFactory()
    assert InvestigationTiac.objects.count() == 1

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'investigation TIAC {evenement.numero} a bien été supprimée")).to_be_visible()

    assert InvestigationTiac.objects.count() == 0
    assert InvestigationTiac._base_manager.get().pk == evenement.pk


def test_can_cloturer_evenement(live_server, page, mocked_authentification_user, mailoutbox):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_cloturer_evenement(
        live_server, page, evenement, mocked_authentification_user, mailoutbox, nav_name="Clôturer l'investigation"
    )


def test_can_cloturer_investigation_if_last_remaining_structure(
    live_server, page, mocked_authentification_user, mus_contact
):
    ac_structure = mus_contact.structure
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS, createur=ac_structure)
    mocked_authentification_user.agent.structure = ac_structure
    evenement.contacts.add(mus_contact)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer()

    evenement.refresh_from_db()
    assert evenement.etat == InvestigationTiac.Etat.CLOTURE
    assert page.get_by_text("Fin de suivi").count() == 2
    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
