from playwright.sync_api import Page, expect
import pytest

from core.factories import ContactAgentFactory
from core.mixins import WithEtatMixin
from core.models import LienLibre
from sa.models import EvenementAnimal
from sa.models.analyse import ResultatAnalyse
from sa.models.evenement import StatutAnimal
from sa.tests.factories import (
    AnalyseFactory,
    EspeceConcerneeFactory,
    EspeceFactory,
    EvenementAnimalFactory,
    MaladieFactory,
    VeterinaireFactory,
)
from sa.tests.pages import EvenementAnimalDetailsPage

FIELDS_COPIED_FROM_SOURCE = [
    "espece_id",
    "statut_animal",
    "statut_evenement",
    "date_statut_changed",
    "adresse_lieu_dit",
    "commune",
    "code_insee",
    "departement_id",
    "numero_identifiant",
    "type_lieu",
    "coordinates",
    "context_suspicion",
    "date_first_symptoms",
    "human_involved",
    "description",
    "commentaire",
    "typage_champ_libre",
]
ETABLISSEMENT_FIELDS = [
    "numero_identifiant_etablissement",
    "raison_sociale_etablissement",
    "departement_etablissement_id",
    "autre_identifiant_etablissement",
    "adresse_lieu_dit_etablissement",
    "code_insee_etablissement",
    "siret_etablissement",
    "commune_etablissement",
    "pays_etablissement",
]
PARTICULIER_FIELDS = [
    "nom_particulier",
    "prenom_particulier",
    "adresse_particulier",
    "commune_particulier",
    "departement_particulier_id",
    "code_insee_particulier",
    "email_particulier",
    "telephone_particulier",
]


def test_detected_maladies_without_evenement_enfant_only_returns_other_detected_maladies(db):
    evenement = EvenementAnimalFactory()
    detected_maladie = MaladieFactory()
    AnalyseFactory(evenement=evenement, resultat=ResultatAnalyse.DETECTE)
    AnalyseFactory(evenement=evenement, maladie=detected_maladie, resultat=ResultatAnalyse.DETECTE)
    AnalyseFactory(evenement=evenement, maladie=detected_maladie, resultat=ResultatAnalyse.DETECTE)
    for resultat in ResultatAnalyse.values:
        if resultat != ResultatAnalyse.DETECTE:
            AnalyseFactory(evenement=evenement, maladie=MaladieFactory(), resultat=resultat)

    assert list(evenement.detected_maladies_without_evenement_enfant) == [detected_maladie]


def test_detected_maladies_without_evenement_enfant_excludes_maladies_with_evenement_enfant(db):
    evenement = EvenementAnimalFactory()
    maladie_with_evenement_enfant = MaladieFactory()
    maladie_without_evenement_enfant = MaladieFactory()
    AnalyseFactory(evenement=evenement, maladie=maladie_with_evenement_enfant, resultat=ResultatAnalyse.DETECTE)
    AnalyseFactory(evenement=evenement, maladie=maladie_without_evenement_enfant, resultat=ResultatAnalyse.DETECTE)
    EvenementAnimalFactory(
        maladie=maladie_with_evenement_enfant, evenement_source=evenement, etat=WithEtatMixin.Etat.BROUILLON
    )

    assert list(evenement.detected_maladies_without_evenement_enfant) == [maladie_without_evenement_enfant]


def test_detected_maladies_without_evenement_enfant_ignores_deleted_evenement_enfant(db):
    evenement = EvenementAnimalFactory()
    detected_maladie = MaladieFactory()
    AnalyseFactory(evenement=evenement, maladie=detected_maladie, resultat=ResultatAnalyse.DETECTE)
    EvenementAnimalFactory(maladie=detected_maladie, evenement_source=evenement, is_deleted=True)

    assert list(evenement.detected_maladies_without_evenement_enfant) == [detected_maladie]


def test_alert_displayed_when_analyse_detects_another_maladie(live_server, page: Page):
    evenement = EvenementAnimalFactory()
    detected_maladie = MaladieFactory()
    AnalyseFactory(evenement=evenement, maladie=detected_maladie, resultat=ResultatAnalyse.DETECTE)

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    alert = page.get_by_test_id("detected-maladie-alert")
    expect(alert).to_have_count(1)
    expect(
        alert.get_by_role("heading", name="La maladie détectée est différente de la maladie suspectée")
    ).to_be_visible()
    expect(alert).to_contain_text(
        f"Une analyse a détecté {detected_maladie.name}, alors que cet événement a été créé pour une suspicion de "
        f"{evenement.maladie.name}."
    )
    expect(alert).to_contain_text(f"Pour rappel : {detected_maladie.get_description_type_display()}")
    expect(alert.get_by_role("link", name="Créer un nouvel événement")).to_be_visible()
    expect(alert.locator(".fr-btn--close")).to_have_count(0)


def test_alert_not_displayed_when_analyse_detects_same_maladie(live_server, page: Page):
    evenement = EvenementAnimalFactory()
    AnalyseFactory(evenement=evenement, resultat=ResultatAnalyse.DETECTE)

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)

    expect(details_page.title).to_be_visible()
    expect(page.get_by_test_id("detected-maladie-alert")).to_have_count(0)


def test_alert_still_displayed_when_creation_is_abandoned(live_server, page: Page):
    evenement = EvenementAnimalFactory()
    AnalyseFactory(evenement=evenement, maladie=MaladieFactory(), resultat=ResultatAnalyse.DETECTE)

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    page.get_by_role("link", name="Créer un nouvel événement").click()
    page.wait_for_url("**/sa/evenement-animal/creation**")
    page.get_by_test_id("top-action-btns").get_by_role("link", name="Annuler", exact=True).click()

    details_page.navigate(evenement)
    expect(page.get_by_test_id("detected-maladie-alert")).to_have_count(1)
    assert EvenementAnimal.objects.count() == 1


@pytest.mark.parametrize(
    "source_kwargs,detenteur_fields",
    [
        ({"statut_animal": StatutAnimal.DETENU}, ETABLISSEMENT_FIELDS),
        ({"statut_animal": StatutAnimal.DETENU, "particulier": True}, PARTICULIER_FIELDS),
        ({"statut_animal": StatutAnimal.SAUVAGE}, []),
    ],
    ids=["etablissement", "particulier", "sauvage"],
)
def test_can_create_evenement_from_alert(
    live_server, page: Page, mocked_authentification_user, assert_models_are_equal, source_kwargs, detenteur_fields
):
    source = EvenementAnimalFactory(**source_kwargs, etat=WithEtatMixin.Etat.EN_COURS)
    detected_maladie = MaladieFactory()
    AnalyseFactory(evenement=source, resultat=ResultatAnalyse.NON_DETECTE)
    detected_analyse = AnalyseFactory(
        evenement=source, maladie=detected_maladie, resultat=ResultatAnalyse.DETECTE, resultat_confirmation=False
    )
    other_analyse = AnalyseFactory(
        evenement=source, maladie=MaladieFactory(), resultat=ResultatAnalyse.NON_DETECTE, resultat_confirmation=False
    )
    other_espece_concernee = EspeceConcerneeFactory(evenement=source, espece=EspeceFactory())
    espece_concernee = EspeceConcerneeFactory(evenement=source, espece=source.espece)
    veterinaire = VeterinaireFactory(evenement=source)
    source_contact = ContactAgentFactory()
    source.contacts.add(source_contact)

    details_page = EvenementAnimalDetailsPage(page, live_server.url)
    details_page.navigate(source)
    page.get_by_test_id("detected-maladie-alert").get_by_role("link", name="Créer un nouvel événement").click()
    page.wait_for_url("**/sa/evenement-animal/creation**")

    expect(page.locator(".analyse-card")).to_have_count(2)
    page.get_by_test_id("top-action-btns").get_by_role("button", name="Enregistrer le brouillon").click()
    page.wait_for_url("**/sa/evenement-animal/**/")

    evenement_enfant = EvenementAnimal.objects.get(evenement_source=source)
    assert evenement_enfant.maladie == detected_maladie
    assert evenement_enfant.is_draft is True
    assert_models_are_equal(source, evenement_enfant, fields=FIELDS_COPIED_FROM_SOURCE + detenteur_fields)

    to_exclude = ["_state", "id", "evenement_id"]
    analyses = evenement_enfant.analyses.order_by("maladie__name")
    assert len(analyses) == 2
    for expected, actual in zip(sorted([detected_analyse, other_analyse], key=lambda a: a.maladie.name), analyses):
        assert_models_are_equal(expected, actual, to_exclude=to_exclude)

    especes_concernees = evenement_enfant.especes_exposees.order_by("pk")
    assert len(especes_concernees) == 2
    assert_models_are_equal(espece_concernee, especes_concernees[0], to_exclude=to_exclude)
    assert_models_are_equal(other_espece_concernee, especes_concernees[1], to_exclude=to_exclude)

    copied_veterinaire = evenement_enfant.veterinaires.get()
    assert_models_are_equal(veterinaire, copied_veterinaire, to_exclude=to_exclude)
    assert list(copied_veterinaire.especes.all()) == [source.espece]

    assert LienLibre.objects.for_both_objects(source, evenement_enfant) is not None
    assert source_contact not in evenement_enfant.contacts.all()

    details_page.navigate(source)
    expect(details_page.title).to_be_visible()
    expect(page.get_by_test_id("detected-maladie-alert")).to_have_count(0)
