import random

from playwright.sync_api import Page, expect
import pytest

from core.factories import ContactAgentFactory
from core.tests.generic_tests.actions import (
    generic_test_ac_can_update_fiche_even_when_state_is_cloture,
    generic_test_can_cloturer_evenement,
    generic_test_can_update_fiche_even_when_free_links_exists_to_a_deleted_object,
    generic_test_soft_delete_object_also_removes_existing_lien_libre,
)
from ssa.constants import CategorieDanger
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac

from ..constants import DANGERS_COURANTS, DangersSyndromiques, SuspicionConclusion
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
    details_page.cloturer(wording="Clôturer l'investigation")

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


test_data = [
    pytest.param(
        SuspicionConclusion.CONFIRMED.value,
        random.sample(CategorieDanger.values, k=1),
        id=f"{SuspicionConclusion.CONFIRMED}-single",
    ),
    pytest.param(
        SuspicionConclusion.CONFIRMED.value,
        random.sample(CategorieDanger.values, k=2),
        id=f"{SuspicionConclusion.CONFIRMED}-multiple",
    ),
    pytest.param(
        SuspicionConclusion.CONFIRMED.value,
        random.sample(DANGERS_COURANTS, k=1),
        id=f"{SuspicionConclusion.CONFIRMED}-common-choices",
    ),
    pytest.param(
        SuspicionConclusion.SUSPECTED.value,
        random.sample(DangersSyndromiques.values, k=1),
        id=f"{SuspicionConclusion.SUSPECTED}-single",
    ),
    pytest.param(
        SuspicionConclusion.SUSPECTED.value,
        random.sample(DangersSyndromiques.values, k=2),
        id=f"{SuspicionConclusion.SUSPECTED}-multiple",
    ),
    *[(item.value, []) for item in SuspicionConclusion.no_clue],
]


@pytest.mark.parametrize("suspicion_conclusion,selected_hazard", test_data)
def test_can_add_conclusion_to_investigation_tiac(
    live_server,
    mocked_authentification_user,
    page: Page,
    assert_models_are_equal,
    suspicion_conclusion,
    selected_hazard,
):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        suspicion_conclusion="",
        selected_hazard=[],
        conclusion_comment="",
        conclusion_repas=None,
        conclusion_aliment=None,
        with_repas=1,
        with_aliment_suspect=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    contact = mocked_authentification_user.agent.contact_set.get()
    assert contact not in evenement.contacts.all()

    input_data = {
        "conclusion_comment": "Mon commentaire",
        "suspicion_conclusion": suspicion_conclusion,
        "selected_hazard": selected_hazard,
        "conclusion_repas": evenement.repas.get().pk,
        "conclusion_aliment": evenement.aliments.get().pk,
    }

    detail_page.fill_conclusion(input_data)
    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.conclusion_comment == "Mon commentaire"
    assert investigation.suspicion_conclusion == suspicion_conclusion
    assert sorted(investigation.selected_hazard) == sorted(selected_hazard)
    if suspicion_conclusion not in (SuspicionConclusion.DISCARDED, SuspicionConclusion.UNKNOWN):
        assert investigation.conclusion_repas == evenement.repas.get()
        assert investigation.conclusion_aliment == evenement.aliments.get()
    assert contact in evenement.contacts.all()


def test_can_add_conclusion_button_is_hidden_for_other_states(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.BROUILLON,
        suspicion_conclusion="",
        selected_hazard=[],
        conclusion_comment="",
        conclusion_repas=None,
        conclusion_aliment=None,
        with_repas=1,
        with_aliment_suspect=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    expect(detail_page.add_conclusion_button).not_to_be_visible()

    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.CLOTURE,
        suspicion_conclusion="",
        selected_hazard=[],
        conclusion_comment="",
        conclusion_repas=None,
        conclusion_aliment=None,
        with_repas=1,
        with_aliment_suspect=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    expect(detail_page.add_conclusion_button).not_to_be_visible()


def test_can_edit_existing_conclusion(live_server, page: Page):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.edit_conclusion_button.click()

    detail_page.page.locator("#id_conclusion_comment").fill("New comment")
    detail_page.page.locator(".fr-modal__body").locator("visible=true").get_by_role(
        "button", name="Enregistrer"
    ).click()
    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.conclusion_comment == "New comment"


def test_edit_investigation_tiac_with_conclusion_notification(live_server, page: Page, mailoutbox):
    investigation = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS, suspicion_conclusion=None)
    contact_1, contact_2, contact_3 = ContactAgentFactory.create_batch(3)
    investigation.contacts.add(contact_1, contact_2, contact_3)
    creation_page = InvestigationTiacDetailsPage(page, live_server.url)
    creation_page.navigate(investigation)

    input_data = {
        "conclusion_comment": "Commentaire",
        "suspicion_conclusion": SuspicionConclusion.CONFIRMED,
        "selected_hazard": [CategorieDanger.ALLERGENE_LAIT],
    }
    creation_page.fill_conclusion(input_data)

    expect(creation_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion == SuspicionConclusion.CONFIRMED

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert set(mail.to) == {contact_1.email, contact_2.email, contact_3.email}
    assert "Conclusion suspicion TIAC" in mail.subject
    assert "TIAC à agent confirmé" in mail.body


def test_edit_investigation_show_previous_danger_value(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        suspicion_conclusion=SuspicionConclusion.CONFIRMED,
        selected_hazard=[CategorieDanger.ALLERGENE_LAIT],
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.edit_conclusion_button.click()
    expect(detail_page.current_modal.get_by_text("Allergène - Lait")).to_be_visible()


def test_edit_investigation_show_previous_danger_values(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        suspicion_conclusion=SuspicionConclusion.CONFIRMED,
        selected_hazard=[
            CategorieDanger.ALLERGENE_LAIT,
            CategorieDanger.ALLERGENE_SESAME,
            CategorieDanger.ALLERGENE_SOJA,
        ],
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.edit_conclusion_button.click()
    expect(detail_page.current_modal.get_by_text("3 éléments sélectionnés")).to_be_visible()
