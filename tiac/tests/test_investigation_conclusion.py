import random

from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest

from core.factories import ContactAgentFactory
from core.models import Structure
from ssa.constants import CategorieDanger
from tiac.factories import InvestigationTiacFactory
from tiac.models import AlimentSuspect, InvestigationTiac, RepasSuspect

from ..constants import DANGERS_COURANTS, DangersSyndromiques, SuspicionConclusion
from .pages import InvestigationTiacDetailsPage

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
        no_conclusion=True,
        with_repas=1,
        with_aliment_suspect=1,
        agents_confirmes_ars=[],
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
    expect(detail_page.page.get_by_text("Conclu", exact=True)).to_be_visible()

    investigation = InvestigationTiac.objects.get()
    assert investigation.get_etat_display() == "Conclu"
    assert investigation.conclusion_comment == "Mon commentaire"
    assert investigation.suspicion_conclusion == suspicion_conclusion
    assert sorted(investigation.selected_hazard) == sorted(selected_hazard)
    if suspicion_conclusion != SuspicionConclusion.DISCARDED:
        assert investigation.conclusion_repas == evenement.repas.get()
        assert investigation.conclusion_aliment == evenement.aliments.get()
    assert contact in evenement.contacts.all()


def test_can_add_conclusion_button_is_hidden_for_other_states(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.BROUILLON,
        no_conclusion=True,
        with_repas=1,
        with_aliment_suspect=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    expect(detail_page.add_conclusion_button).not_to_be_visible()

    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.CLOTURE,
        no_conclusion=True,
        with_repas=1,
        with_aliment_suspect=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    expect(detail_page.add_conclusion_button).not_to_be_visible()


def test_can_edit_existing_conclusion(live_server, page: Page):
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS, with_repas=1)
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
    investigation = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.CONCLU, suspicion_conclusion=None, with_repas=1
    )
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
        etat=InvestigationTiac.Etat.CONCLU,
        suspicion_conclusion=SuspicionConclusion.CONFIRMED,
        selected_hazard=[CategorieDanger.ALLERGENE_LAIT],
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.edit_conclusion_button.click()
    expect(detail_page.current_modal.get_by_text("Allergène - Lait")).to_be_visible()


def test_edit_investigation_show_previous_danger_values(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.CONCLU,
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


def test_conclusion_investigation_tiac_conditional_ui(
    live_server,
    page: Page,
):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_repas=1,
        with_aliment_suspect=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)

    detail_page.add_conclusion_button.click()

    for conclusion in (SuspicionConclusion.CONFIRMED, SuspicionConclusion.UNKNOWN, SuspicionConclusion.SUSPECTED):
        detail_page.suspicion_conclusion_field.select_option(conclusion)
        expect(detail_page.repas_field).to_be_enabled()
        expect(detail_page.aliment_field).to_be_enabled()

    detail_page.suspicion_conclusion_field.select_option(SuspicionConclusion.DISCARDED)
    expect(detail_page.repas_field).to_be_disabled()
    expect(detail_page.aliment_field).to_be_disabled()


def test_conclusion_form_is_initialized_when_agent_pathogene_is_set(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        agents_confirmes_ars=[CategorieDanger.ALLERGENE_ARACHIDE, CategorieDanger.ALLERGENE_CELERI],
        with_repas=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    detail_page.save_conclusion()

    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion == SuspicionConclusion.CONFIRMED
    assert sorted(investigation.selected_hazard) == sorted(
        [CategorieDanger.ALLERGENE_ARACHIDE, CategorieDanger.ALLERGENE_CELERI]
    )
    assert investigation.conclusion_repas == RepasSuspect.objects.get()


def test_can_conclusion_form_shows_notice_when_user_try_to_force_choice(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        agents_confirmes_ars=[CategorieDanger.ALLERGENE_ARACHIDE, CategorieDanger.ALLERGENE_CELERI],
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    detail_page.suspicion_conclusion_field.select_option(SuspicionConclusion.SUSPECTED)
    expect(
        detail_page.page.get_by_text("Êtes vous sûr qu'il ne s'agit pas d'une tiac à agent confirmé ?")
    ).to_be_visible()


def test_conclusion_form_is_initialized_when_dangers_detectes_is_set(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_analyse_alimentaires=2,
        agents_confirmes_ars=[],
        with_repas=1,
    )
    analyse = evenement.analyses_alimentaires.first()
    analyse.categorie_danger = [CategorieDanger.ALLERGENE_ARACHIDE]
    analyse.save()
    analyse = evenement.analyses_alimentaires.last()
    analyse.categorie_danger = [CategorieDanger.ALLERGENE_CELERI]
    analyse.save()
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    detail_page.save_conclusion()

    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion == SuspicionConclusion.CONFIRMED
    assert sorted(investigation.selected_hazard) == sorted(
        [CategorieDanger.ALLERGENE_ARACHIDE, CategorieDanger.ALLERGENE_CELERI]
    )
    assert investigation.conclusion_repas == RepasSuspect.objects.get()


def test_conclusion_form_is_initialized_when_both_dangers_detectes_and_agents_confirmes_are_set(
    live_server, page: Page
):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_analyse_alimentaires=1,
        agents_confirmes_ars=[CategorieDanger.ALLERGENE_CELERI],
        with_repas=1,
    )
    analyse = evenement.analyses_alimentaires.first()
    analyse.categorie_danger = [CategorieDanger.ALLERGENE_ARACHIDE]
    analyse.save()
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    detail_page.save_conclusion()

    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion == SuspicionConclusion.CONFIRMED
    assert sorted(investigation.selected_hazard) == sorted(
        [CategorieDanger.ALLERGENE_ARACHIDE, CategorieDanger.ALLERGENE_CELERI]
    )
    assert investigation.conclusion_repas == RepasSuspect.objects.get()


def test_conclusion_form_is_initialized_when_dangers_syndromiques_are_set(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        agents_confirmes_ars=[],
        danger_syndromiques_suspectes=[
            DangersSyndromiques.INTOXINATION_BACILLUS,
            DangersSyndromiques.TOXI_INFECTION_BACILLUS,
        ],
        with_repas=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    detail_page.save_conclusion()

    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion == SuspicionConclusion.SUSPECTED
    assert sorted(investigation.selected_hazard) == sorted(
        [DangersSyndromiques.INTOXINATION_BACILLUS, DangersSyndromiques.TOXI_INFECTION_BACILLUS]
    )
    assert investigation.conclusion_repas == RepasSuspect.objects.get()


def test_conclusion_form_is_initialized_when_dangers_syndromiques_are_not_set(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        agents_confirmes_ars=[],
        danger_syndromiques_suspectes=[],
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    expect(detail_page.suspicion_conclusion_field).to_have_value("")
    expect(detail_page.page.locator("#selected_hazard-treeselect .treeselect--disabled")).to_have_count(1)


def test_conclusion_form_shows_notice_when_multiple_repas(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_repas=2,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    expect(
        detail_page.page.get_by_text(
            "Si le repas à l'origine de la TIAC est identifié, il doit être enregistré dans la fiche et sélectionné dans la conclusion",
            exact=True,
        )
    ).to_be_visible()


def test_conclusion_form_shows_notice_when_multiple_aliments(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_aliment_suspect=2,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()
    expect(
        detail_page.page.get_by_text(
            "Si l’aliment à l'origine de la TIAC est identifié, il doit être enregistré dans la fiche et sélectionné dans la conclusion",
            exact=True,
        )
    ).to_be_visible()


def test_conclusion_form_required_fields(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_repas=2,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()

    detail_page.suspicion_conclusion_field.select_option(SuspicionConclusion.CONFIRMED)
    expect(detail_page.selected_hazard_hidden_field).to_have_attribute("required", "")
    expect(detail_page.repas_field).to_have_attribute("required", "")
    assert detail_page.selected_hazard_label.evaluate("(el) =>   getComputedStyle(el, '::after').content") == '"*"'

    detail_page.suspicion_conclusion_field.select_option(SuspicionConclusion.SUSPECTED)
    expect(detail_page.selected_hazard_hidden_field).to_have_attribute("required", "")
    assert detail_page.selected_hazard_label.evaluate("(el) => getComputedStyle(el, '::after').content") == '"*"'
    expect(detail_page.repas_field).to_have_attribute("required", "")

    detail_page.suspicion_conclusion_field.select_option(SuspicionConclusion.DISCARDED)
    expect(detail_page.selected_hazard_hidden_field).not_to_have_attribute("required", "")
    expect(detail_page.repas_field).not_to_have_attribute("required", "")
    assert detail_page.selected_hazard_label.evaluate("(el) => getComputedStyle(el, '::after').content") == "none"

    detail_page.suspicion_conclusion_field.select_option(SuspicionConclusion.UNKNOWN)
    expect(detail_page.selected_hazard_hidden_field).not_to_have_attribute("required", "")
    expect(detail_page.repas_field).not_to_have_attribute("required", "")
    assert detail_page.selected_hazard_label.evaluate("(el) => getComputedStyle(el, '::after').content") == "none"


def test_conclusion_form_aliment_is_pre_filled_when_unique(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_aliment_suspect=1,
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.add_conclusion_button.click()

    detail_page.suspicion_conclusion_field.select_option(SuspicionConclusion.UNKNOWN)
    detail_page.save_conclusion()

    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion == SuspicionConclusion.UNKNOWN
    assert investigation.conclusion_aliment == AlimentSuspect.objects.get()


def test_can_add_conclusion_to_investigation_tiac_when_no_prefill_at_all(
    live_server,
    page: Page,
):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_repas=1,
        agents_confirmes_ars=[],
        danger_syndromiques_suspectes=[],
    )
    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)

    input_data = {
        "conclusion_comment": "Mon commentaire",
        "suspicion_conclusion": SuspicionConclusion.CONFIRMED,
        "selected_hazard": [CategorieDanger.ALLERGENE_ARACHIDE],
        "conclusion_repas": evenement.repas.get().pk,
    }

    detail_page.fill_conclusion(input_data)
    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()
    expect(detail_page.page.get_by_text("Conclu", exact=True)).to_be_visible()

    investigation = InvestigationTiac.objects.get()
    assert investigation.get_etat_display() == "Conclu"
    assert investigation.conclusion_comment == "Mon commentaire"
    assert investigation.suspicion_conclusion == SuspicionConclusion.CONFIRMED
    assert investigation.selected_hazard == [CategorieDanger.ALLERGENE_ARACHIDE]


def test_can_delete_existing_conclusion(live_server, page: Page):
    evenement = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.CONCLU,
        suspicion_conclusion=SuspicionConclusion.CONFIRMED,
        selected_hazard=[CategorieDanger.ALLERGENE_LAIT],
        with_repas=1,
        with_aliment_suspect=1,
    )
    evenement.conclusion_repas = evenement.repas.get()
    evenement.conclusion_aliment = evenement.aliments.get()
    evenement.save()

    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(evenement)
    detail_page.edit_conclusion_button.click()
    detail_page.delete_conclusion_button.click()

    expect(detail_page.page.get_by_text("La conclusion a été supprimée.", exact=True)).to_be_visible()
    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion is None
    assert investigation.selected_hazard == []
    assert investigation.conclusion_comment == ""
    assert investigation.conclusion_repas is None
    assert investigation.conclusion_aliment is None


def test_cant_forge_conclusion_update_on_cloture_investigation_i_cant_modify(client, mocked_authentification_user):
    evenement = InvestigationTiacFactory(
        createur=Structure.objects.create(libelle="A new structure"),
        etat=InvestigationTiac.Etat.CLOTURE,
        conclusion_comment="Initial value",
    )
    assert evenement.can_be_modified(mocked_authentification_user) is False

    client.post(
        reverse("tiac:investigation-tiac-edition-conclusion", kwargs={"pk": evenement.pk}),
        data={
            "conclusion_comment": "New comment for test",
            "suspicion_conclusion": SuspicionConclusion.UNKNOWN,
            "conclusion_repas": "",
            "conclusion_aliment": "",
            "selected_hazard": "",
        },
    )
    evenement.refresh_from_db()
    assert evenement.conclusion_comment == "Initial value"
