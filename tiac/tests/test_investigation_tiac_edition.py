from faker import Faker
from playwright.sync_api import Page, expect
import pytest

from core.constants import MUS_STRUCTURE
from core.models import Contact, LienLibre
from ssa.constants import CategorieDanger
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from tiac.factories import (
    AlimentSuspectFactory,
    AnalyseAlimentaireFactory,
    EtablissementFactory,
    EvenementSimpleFactory,
    InvestigationTiacFactory,
    RepasSuspectFactory,
)

from ..constants import DangersSyndromiques, SuspicionConclusion, TypeRepas
from ..models import Analyses, Etablissement, EvenementSimple, InvestigationFollowUp, InvestigationTiac
from .pages import InvestigationTiacDetailsPage, InvestigationTiacEditPage

pytestmark = pytest.mark.usefixtures("mus_contact")


def test_can_edit_required_fields(live_server, page: Page, assert_models_are_equal):
    investigation = InvestigationTiacFactory(suspicion_conclusion=SuspicionConclusion.UNKNOWN)
    new_data = InvestigationTiacFactory.build(suspicion_conclusion=SuspicionConclusion.UNKNOWN)
    previous_count = InvestigationTiac.objects.count()

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()
    expect(
        edit_page.page.get_by_text(f"Modification de l'événement {investigation.numero}", exact=True)
    ).to_be_visible()
    edit_page.fill_context_block(new_data)
    edit_page.submit()

    investigation.refresh_from_db()
    assert_models_are_equal(
        investigation,
        new_data,
        fields=[
            "date_reception",
            "evenement_origin",
            "modalites_declaration",
            "contenu",
            "notify_ars",
            "numero_sivss",
            "follow_up",
            "nb_sick_persons",
            "nb_sick_persons_to_hospital",
            "nb_dead_persons",
            "datetime_first_symptoms",
            "datetime_last_symptoms",
        ],
    )
    assert previous_count == InvestigationTiac.objects.count()


def test_can_edit_etiologie(live_server, page: Page, assert_models_are_equal, choose_different_values):
    investigation = InvestigationTiacFactory(
        suspicion_conclusion=SuspicionConclusion.UNKNOWN,
        with_danger_syndromiques_suspectes_count=3,
        analyses_sur_les_malades=Analyses.INCONNU,
    )

    new_danger_syndromique = choose_different_values(
        DangersSyndromiques.values, investigation.danger_syndromiques_suspectes, singleton=True
    )

    previous_count = InvestigationTiac.objects.count()
    expected_danger_syndromique = [*investigation.danger_syndromiques_suspectes[:-1], new_danger_syndromique]

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    # Remove one danger syndromique and add one. One stay unchanged
    edit_page.page.locator(".etiologie-card-container").get_by_role("button", name="Supprimer").last.click()
    assert edit_page.get_dangers_syndromiques().count() == 2
    edit_page.add_danger_syndromique(DangersSyndromiques(new_danger_syndromique).label)
    assert edit_page.get_dangers_syndromiques().count() == 3
    edit_page.submit()

    investigation.refresh_from_db()
    assert investigation.danger_syndromiques_suspectes == expected_danger_syndromique
    assert previous_count == InvestigationTiac.objects.count()


COMMON_FIELDS_TO_EXCLUDE = [
    "_state",
    "id",
    "departement_id",
    "code_postal",
    "investigation_id",
    "evenement_simple_id",
]


def test_can_edit_ars_block(live_server, page: Page, assert_models_are_equal, choose_different_values):
    investigation = InvestigationTiacFactory(analyses_sur_les_malades=Analyses.INCONNU, agents_confirmes_ars=[])

    new_analyses_sur_les_malades = Analyses.OUI
    new_precision = Faker().sentence()

    previous_count = InvestigationTiac.objects.count()

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    edit_page.set_analyses(new_analyses_sur_les_malades.value)
    edit_page.precisions.fill(new_precision)
    edit_page.add_agent_pathogene_confirme_via_shortcut("Shigella")
    edit_page.submit_from_top()

    investigation.refresh_from_db()
    assert_models_are_equal(
        investigation,
        {
            "agents_confirmes_ars": ["Shigella"],
            "analyses_sur_les_malades": new_analyses_sur_les_malades.label,
            "precisions": new_precision,
        },
        fields=[
            "agents_confirmes_ars",
            "analyses_sur_les_malades",
            "precisions",
        ],
    )
    assert previous_count == InvestigationTiac.objects.count()


def test_can_edit_investigation_elements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")

    investigation: InvestigationTiac = InvestigationTiacFactory(
        suspicion_conclusion=SuspicionConclusion.UNKNOWN,
        with_etablissements=3,
        with_etablissements__departement=departement,
        with_repas=3,
        with_repas__departement=departement,
        with_analyse_alimentaires=3,
        with_aliment_suspect=3,
    )
    new_etablissement = EtablissementFactory.build(departement=departement)
    etablissement_to_modify = EtablissementFactory.build()
    new_repas = RepasSuspectFactory.build(departement=departement)
    repas_to_modify = RepasSuspectFactory.build()
    new_aliment_suspect = AlimentSuspectFactory.build(cuisine=True)
    aliment_suspect_to_modify = AlimentSuspectFactory.build()
    new_analyse_alimentaire = AnalyseAlimentaireFactory.build()
    analyse_alimentaires_to_modify = AnalyseAlimentaireFactory.build()

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    edit_page.delete_etablissement(2)
    edit_page.edit_etablissement(1, enseigne_usuelle=etablissement_to_modify.enseigne_usuelle)
    edit_page.add_etablissement(new_etablissement)

    edit_page.delete_repas(2)
    edit_page.edit_repas(1, denomination=repas_to_modify.denomination)
    edit_page.add_repas(new_repas)

    edit_page.delete_aliment(2)
    edit_page.edit_aliment(1, denomination=aliment_suspect_to_modify.denomination)
    edit_page.add_aliment_cuisine(new_aliment_suspect)

    edit_page.delete_analyse_alimentaire(2)
    edit_page.edit_analyse_alimentaire(1, reference_prelevement=analyse_alimentaires_to_modify.reference_prelevement)
    edit_page.add_analyse_alimentaire(new_analyse_alimentaire)

    edit_page.submit()

    investigation.refresh_from_db()

    assert investigation.etablissements.count() == 3
    assert (
        investigation.etablissements.order_by("pk").all()[1].enseigne_usuelle
        == etablissement_to_modify.enseigne_usuelle
    )
    assert_models_are_equal(
        investigation.etablissements.order_by("pk").last(),
        new_etablissement,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE, "code_insee", "siret"],
    )

    assert investigation.repas.count() == 3
    assert investigation.repas.order_by("pk").all()[1].denomination == repas_to_modify.denomination
    assert_models_are_equal(
        investigation.repas.order_by("pk").last(),
        new_repas,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE],
        ignore_array_order=True,
    )

    assert investigation.aliments.count() == 3
    assert investigation.aliments.order_by("pk").all()[1].denomination == aliment_suspect_to_modify.denomination
    assert_models_are_equal(
        investigation.aliments.order_by("pk").last(),
        new_aliment_suspect,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE],
        ignore_array_order=True,
    )

    assert investigation.analyses_alimentaires.count() == 3
    assert (
        investigation.analyses_alimentaires.order_by("pk").all()[1].reference_prelevement
        == analyse_alimentaires_to_modify.reference_prelevement
    )
    assert_models_are_equal(
        investigation.analyses_alimentaires.order_by("pk").last(),
        new_analyse_alimentaire,
        to_exclude=[*COMMON_FIELDS_TO_EXCLUDE],
        ignore_array_order=True,
    )


def test_cancel_edit_on_etablissement_reset_all_value(
    live_server, page: Page, ensure_departements, assert_models_are_equal
):
    departement, *_ = ensure_departements("Paris")
    departement_2, *_ = ensure_departements("Nord")

    investigation: InvestigationTiac = InvestigationTiacFactory(
        with_etablissements=1,
        with_etablissements__departement=departement,
        with_etablissements__inspection=True,
    )
    initial_etablissement: Etablissement = investigation.etablissements.get()

    new_etablissement = EtablissementFactory.build(departement=departement_2)
    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    card = edit_page.get_etablissement_card()
    card.locator(".modify-button").click()
    edit_page.fill_etablissement(edit_page.current_modal, new_etablissement)
    edit_page.current_modal.get_by_role("button", name="Annuler").click()
    card.locator(".modify-button").click()

    modal = edit_page.current_modal
    expect(modal.locator('[id$="type_etablissement"]')).to_have_value(initial_etablissement.type_etablissement)
    expect(modal.locator('[id$="raison_sociale"]')).to_have_value(initial_etablissement.raison_sociale)
    expect(modal.locator('[id$="numero_agrement"]')).to_have_value(initial_etablissement.numero_agrement)
    expect(modal.locator('[id$="autre_identifiant"]')).to_have_value(initial_etablissement.autre_identifiant)
    expect(modal.locator('[id$="enseigne_usuelle"]')).to_have_value(initial_etablissement.enseigne_usuelle)
    expect(modal.locator('[id$="adresse_lieu_dit"]')).to_have_value(initial_etablissement.adresse_lieu_dit)
    expect(modal.locator('[id$="siret"]')).to_have_value(initial_etablissement.siret)
    expect(modal.locator('[id$="-commune"]')).to_have_value(initial_etablissement.commune)
    expect(modal.locator('[id$="-departement"]')).to_have_value(initial_etablissement.departement.numero)
    expect(modal.locator('[id$="-pays"]')).to_have_value(initial_etablissement.pays.code)

    expect(modal.get_by_text("Inspection", exact=True)).to_be_checked()
    expect(modal.locator('[id$="-numero_resytal"]')).to_have_value(initial_etablissement.numero_resytal)
    expect(modal.locator('[id$="-date_inspection"]')).to_have_value(
        initial_etablissement.date_inspection.strftime("%Y-%m-%d")
    )
    expect(modal.locator('[id$="-evaluation"]')).to_have_value(initial_etablissement.evaluation)
    expect(modal.locator('[id$="-commentaire"]')).to_have_value(initial_etablissement.commentaire)

    edit_page.current_modal.get_by_role("button", name="Annuler").click()
    edit_page.submit()

    investigation.refresh_from_db()

    assert investigation.etablissements.count() == 1
    assert initial_etablissement == investigation.etablissements.get()


def test_can_edit_freelinks(
    live_server, page: Page, ensure_departements, assert_models_are_equal, choose_different_values, choice_js_fill
):
    investigation: InvestigationTiac = InvestigationTiacFactory(with_liens_libres=2)
    other_event_1 = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    other_event_2 = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    other_event_3 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()
    edit_page.remove_free_link(1)
    edit_page.remove_free_link(0)
    edit_page.add_free_link(other_event_1.numero, choice_js_fill)
    edit_page.add_free_link(other_event_2.numero, choice_js_fill, link_label="Enregistrement simple : ")
    edit_page.add_free_link(other_event_3.numero, choice_js_fill, link_label="Événement produit : ")
    edit_page.submit()

    investigation.refresh_from_db()
    assert set(lien.related_object_2 for lien in LienLibre.objects.for_object(investigation)) == {
        other_event_1,
        other_event_2,
        other_event_3,
    }


def test_edit_investigation_tiac_with_investigation_coordonnee_notification(live_server, page: Page, mailoutbox):
    investigation = InvestigationTiacFactory(follow_up=InvestigationFollowUp.INVESTIGATION_DD)
    contact_structure_mus = Contact.objects.get(structure__libelle=MUS_STRUCTURE)
    creation_page = InvestigationTiacEditPage(page, live_server.url, investigation=investigation)
    creation_page.navigate()
    creation_page.set_follow_up(InvestigationFollowUp.INVESTIGATION_COORDONNEE)
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.follow_up == InvestigationFollowUp.INVESTIGATION_COORDONNEE

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert set(mail.to) == {"text@example.com", contact_structure_mus.email}
    assert "Investigation coordonnée" in mail.subject
    assert contact_structure_mus in investigation.contacts.all()


def test_can_update_ars_block_only_when_analysis_is_true(live_server, mocked_authentification_user, page: Page):
    input_data: InvestigationTiac = InvestigationTiacFactory(analyses_sur_les_malades=Analyses.NON)

    creation_page = InvestigationTiacEditPage(
        page,
        live_server.url,
        investigation=input_data,
    )
    creation_page.navigate()

    expect(creation_page.precisions).to_be_disabled()
    expect(page.locator("#agents-pathogene .fr-treeselect--disabled")).to_have_count(1)

    creation_page.set_analyses("Oui")
    expect(creation_page.precisions).to_be_enabled()
    expect(page.locator("#agents-pathogene .fr-treeselect--disabled")).to_have_count(0)

    creation_page.set_analyses("Non")
    expect(creation_page.precisions).to_be_disabled()
    expect(page.locator("#agents-pathogene .fr-treeselect--disabled")).to_have_count(1)


def test_investigation_tiac_update_has_locking_protection(
    live_server,
    page,
    mocked_authentification_user,
):
    evenement = InvestigationTiacFactory(contenu="AAA")
    update_page = InvestigationTiacEditPage(page, live_server.url, evenement)
    update_page.navigate()
    update_page.contenu.fill("BBB")

    evenement.contenu = "CCC"
    evenement.save()

    update_page.page.get_by_test_id("bottom-action-btns").get_by_test_id("submit-publish").click()
    update_page.page.wait_for_url("**edition**")

    evenement.refresh_from_db()
    assert evenement.contenu == "CCC"
    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    expect(
        page.get_by_text(
            "Vos modifications n'ont pas été enregistrées. Un autre utilisateur a modifié cet objet. Fermer cette modale pour charger la dernière version."
        )
    ).to_be_visible()
    page.keyboard.press("Escape")
    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")


def test_update_investigation_tiac_updates_last_updated_field(live_server, page):
    evenement = InvestigationTiacFactory()
    initial_last_update = evenement.last_updated
    update_page = InvestigationTiacEditPage(page, live_server.url, evenement)
    update_page.navigate()
    update_page.contenu.fill("Test")
    update_page.submit()
    update_page.page.wait_for_url(f"**{evenement.numero_evenement}**")
    evenement.refresh_from_db()
    assert evenement.last_updated > initial_last_update


def test_cancel_edit_on_repas_reset_values(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")

    investigation: InvestigationTiac = InvestigationTiacFactory(
        with_repas=1,
        with_repas__departement=departement,
    )
    initial_repas = investigation.repas.get()

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    card = edit_page.get_repas_card(0)
    card.locator(".modify-button").click()
    edit_page.current_modal.locator("visible=true").locator('[id$="denomination"]').fill("New value")
    edit_page.current_modal.get_by_role("button", name="Annuler").click()
    edit_page.get_repas_card(0).locator(".modify-button").click()

    modal = edit_page.current_modal
    expect(modal.locator('[id$="denomination"]')).to_have_value(initial_repas.denomination)

    edit_page.current_modal.get_by_role("button", name="Annuler").click()
    edit_page.submit()

    investigation.refresh_from_db()

    assert investigation.repas.count() == 1
    assert initial_repas == investigation.repas.get()


def test_cancel_edit_on_repas_show_correct_conditional_field(
    live_server, page: Page, ensure_departements, assert_models_are_equal
):
    investigation: InvestigationTiac = InvestigationTiacFactory(
        with_repas=1,
        with_repas__type_repas=TypeRepas.DOMICILE,
    )

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    card = edit_page.get_repas_card(0)
    card.locator(".modify-button").click()
    edit_page.current_modal.locator('[id$="type_repas"]').select_option(TypeRepas.RESTAURATION_COLLECTIVE)
    edit_page.current_modal.get_by_role("button", name="Annuler").click()

    edit_page.get_repas_card(0).locator(".modify-button").click()
    expect(edit_page.current_modal.locator('[id$="type_collectivite"]')).not_to_be_visible()


def test_editing_investigation_does_not_wipe_existing_conclusion(
    live_server, page: Page, ensure_departements, assert_models_are_equal
):
    departement, *_ = ensure_departements("Paris")

    investigation = InvestigationTiacFactory(
        etat=InvestigationTiac.Etat.EN_COURS,
        no_conclusion=True,
        with_repas=1,
        with_aliment_suspect=1,
    )

    detail_page = InvestigationTiacDetailsPage(page, live_server.url)
    detail_page.navigate(investigation)
    detail_page.fill_conclusion(
        {
            "conclusion_comment": "Mon commentaire",
            "suspicion_conclusion": SuspicionConclusion.CONFIRMED.value,
            "selected_hazard": [CategorieDanger.values[0]],
            "conclusion_repas": investigation.repas.get().pk,
            "conclusion_aliment": investigation.aliments.get().pk,
        }
    )
    expect(detail_page.page.get_by_text("L’évènement a été mis à jour avec succès.", exact=True)).to_be_visible()

    investigation.refresh_from_db()
    original_conclusion_repas = investigation.conclusion_repas
    original_conclusion_aliment = investigation.conclusion_aliment
    assert original_conclusion_repas is not None
    assert original_conclusion_aliment is not None

    new_repas = RepasSuspectFactory.build(departement=departement)
    new_aliment = AlimentSuspectFactory.build(cuisine=True)

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()
    edit_page.add_repas(new_repas)
    edit_page.add_aliment_cuisine(new_aliment)
    edit_page.submit()

    investigation.refresh_from_db()
    assert investigation.repas.count() == 2
    assert investigation.aliments.count() == 2
    assert investigation.conclusion_repas == original_conclusion_repas
    assert investigation.conclusion_aliment == original_conclusion_aliment
    assert investigation.suspicion_conclusion == SuspicionConclusion.CONFIRMED.value
    assert investigation.conclusion_comment == "Mon commentaire"
