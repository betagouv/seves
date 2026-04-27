from playwright.sync_api import expect

from core.tests.generic_tests.actions import (
    generic_test_ac_can_update_fiche_even_when_state_is_cloture,
    generic_test_can_cloturer_evenement,
    generic_test_can_update_fiche_even_when_free_links_exists_to_a_deleted_object,
    generic_test_soft_delete_object_also_removes_existing_lien_libre,
)
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


def test_ac_can_update_fiche_even_when_state_is_cloture(live_server, page, mocked_authentification_user):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_ac_can_update_fiche_even_when_state_is_cloture(
        live_server, page, evenement, mocked_authentification_user, field_to_edit="#id_contenu"
    )


def test_can_update_fiche_even_when_free_links_exists_to_a_deleted_object(live_server, page):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_can_update_fiche_even_when_free_links_exists_to_a_deleted_object(
        live_server, page, evenement, field_name="contenu", other_object=InvestigationTiacFactory()
    )


def test_soft_delete_object_also_removes_existing_lien_libre(live_server, page):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    generic_test_soft_delete_object_also_removes_existing_lien_libre(
        live_server, page, evenement, other_object=InvestigationTiacFactory()
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


def test_can_download_document_investigation_cas_humain_when_no_publication_date(live_server, page):
    evenement = InvestigationTiacFactory(date_publication=None)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    download = details_page.download().value
    assert download.suggested_filename == f"investigation_tiac_{evenement.numero}.docx"
