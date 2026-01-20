import pytest
from faker import Faker
from playwright.sync_api import Page

from core.constants import MUS_STRUCTURE
from core.factories import ContactAgentFactory
from core.models import LienLibre, Contact
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from tiac.factories import (
    InvestigationTiacFactory,
    EtablissementFactory,
    RepasSuspectFactory,
    AnalyseAlimentaireFactory,
    AlimentSuspectFactory,
    EvenementSimpleFactory,
)
from .pages import InvestigationTiacEditPage
from ..constants import SuspicionConclusion, DangersSyndromiques
from ..models import InvestigationTiac, Analyses, EvenementSimple, InvestigationFollowUp

pytestmark = pytest.mark.usefixtures("mus_contact")


def test_can_edit_required_fields(live_server, page: Page, assert_models_are_equal):
    investigation = InvestigationTiacFactory(suspicion_conclusion=SuspicionConclusion.UNKNOWN)
    new_data = InvestigationTiacFactory.build(suspicion_conclusion=SuspicionConclusion.UNKNOWN)
    previous_count = InvestigationTiac.objects.count()

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()
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
            "will_trigger_inquiry",
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
    new_analyses_sur_les_malades = Analyses.OUI
    new_precision = Faker().sentence()

    previous_count = InvestigationTiac.objects.count()
    expected_danger_syndromique = [*investigation.danger_syndromiques_suspectes[:-1], new_danger_syndromique]

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()

    # Remove one danger syndromique and add one. One stay unchanged
    edit_page.page.locator(".etiologie-card-container").get_by_role("button", name="Supprimer").last.click()
    assert edit_page.get_dangers_syndromiques().count() == 2
    edit_page.add_danger_syndromique(DangersSyndromiques(new_danger_syndromique).label)
    assert edit_page.get_dangers_syndromiques().count() == 3
    edit_page.set_analyses(new_analyses_sur_les_malades.value)
    edit_page.precisions.fill(new_precision)

    edit_page.submit()

    investigation.refresh_from_db()
    assert_models_are_equal(
        investigation,
        {
            "danger_syndromiques_suspectes": expected_danger_syndromique,
            "analyses_sur_les_malades": new_analyses_sur_les_malades.label,
            "precisions": new_precision,
        },
        fields=[
            "danger_syndromiques_suspectes",
            "analyses_sur_les_malades",
            "precisions",
        ],
    )
    assert previous_count == InvestigationTiac.objects.count()


COMMON_FIELDS_TO_EXCLUDE = [
    "_state",
    "id",
    "departement_id",
    "investigation_id",
    "evenement_simple_id",
]


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


def test_can_edit_etiologie_conclusion_and_freelinks(
    live_server, page: Page, ensure_departements, assert_models_are_equal, choose_different_values, choice_js_fill
):
    investigation: InvestigationTiac = InvestigationTiacFactory(with_liens_libres=2)
    other_event_1 = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    other_event_2 = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    other_event_3 = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)

    new_investigation: InvestigationTiac = InvestigationTiacFactory(
        agents_confirmes_ars=choose_different_values(SuspicionConclusion.values, investigation.agents_confirmes_ars),
        suspicion_conclusion=choose_different_values(
            SuspicionConclusion.values, [investigation.suspicion_conclusion], singleton=True
        ),
    )

    edit_page = InvestigationTiacEditPage(page, live_server.url, investigation)
    edit_page.navigate()
    edit_page.remove_free_link(1)
    edit_page.remove_free_link(0)
    edit_page.add_free_link(other_event_1.numero, choice_js_fill)
    edit_page.add_free_link(other_event_2.numero, choice_js_fill, link_label="Enregistrement simple : ")
    edit_page.add_free_link(other_event_3.numero, choice_js_fill, link_label="Événement produit : ")
    edit_page.fill_conlusion(new_investigation)

    edit_page.submit()

    investigation.refresh_from_db()
    assert set(lien.related_object_2 for lien in LienLibre.objects.for_object(investigation)) == {
        other_event_1,
        other_event_2,
        other_event_3,
    }
    assert_models_are_equal(
        investigation,
        new_investigation,
        fields=[
            "suspicion_conclusion",
            "selected_hazard",
            "conclusion_comment",
            "conclusion_repas",
            "conclusion_aliment",
        ],
        ignore_array_order=True,
    )


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


def test_edit_investigation_tiac_with_conclusion_notification(live_server, page: Page, mailoutbox):
    investigation = InvestigationTiacFactory(suspicion_conclusion=None)
    contact_1, contact_2, contact_3 = ContactAgentFactory.create_batch(3)
    investigation.contacts.add(contact_1, contact_2, contact_3)
    creation_page = InvestigationTiacEditPage(page, live_server.url, investigation=investigation)
    creation_page.navigate()
    creation_page.suspicion_conclusion.select_option(SuspicionConclusion.CONFIRMED)
    creation_page._set_treeselect_option(
        "selected_hazard-treeselect", "Allergène - composition ou étiquetage > Allergène - Arachide"
    )
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.suspicion_conclusion == SuspicionConclusion.CONFIRMED

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert set(mail.to) == {contact_1.email, contact_2.email, contact_3.email}
    assert "Conclusion suspicion TIAC" in mail.subject
    assert "TIAC à agent confirmé" in mail.body
