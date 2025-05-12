import re
from zoneinfo import ZoneInfo

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils import timezone, formats
from playwright.sync_api import expect, Page
from reversion.models import Version

from core.constants import MUS_STRUCTURE, BSV_STRUCTURE
from core.factories import StructureFactory
from core.models import Structure, Visibilite, Contact
from seves import settings
from sv.factories import (
    EvenementFactory,
    FicheZoneFactory,
    FicheDetectionFactory,
    LieuFactory,
    PrelevementFactory,
    ZoneInfesteeFactory,
    OrganismeNuisibleFactory,
)
from sv.models import Evenement, FicheDetection, Etat, Prelevement, FicheZoneDelimitee


def get_date_formated(date_derniere_mise_a_jour):
    local_timezone = ZoneInfo(settings.TIME_ZONE)
    local_date = timezone.localtime(date_derniere_mise_a_jour, local_timezone)
    return formats.date_format(local_date, "j F Y H:i")


@pytest.fixture
def assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(page: Page):
    """Fixture pour vérifier que la date de dernière mise à jour de la fiche zone est correctement affichée."""

    def _assert_fiche_zone_derniere_mise_a_jour_visible(fiche_zone_delimitee: FicheZoneDelimitee):
        last_update_text = (
            f"Dernière mise à jour le {get_date_formated(fiche_zone_delimitee.date_derniere_mise_a_jour)}"
        )
        expect(page.get_by_test_id("evenement-header").get_by_text(last_update_text)).to_be_visible()
        page.get_by_role("tab", name="Zone").click()
        expect(page.get_by_label("Zone", exact=True).get_by_text(last_update_text)).to_be_visible()

    return _assert_fiche_zone_derniere_mise_a_jour_visible


@pytest.fixture
def assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(page: Page):
    """Fixture pour vérifier que la date de dernière mise à jour de la fiche détection est correctement affichée."""

    def _assert_fiche_detection_derniere_mise_a_jour_visible(fiche_detection: FicheDetection):
        last_update_text = f"Dernière mise à jour le {get_date_formated(fiche_detection.date_derniere_mise_a_jour)}"
        expect(page.get_by_test_id("evenement-header").get_by_text(last_update_text)).to_be_visible()
        page.get_by_role("tab", name="Détection").click()
        page.get_by_role("tab", name=fiche_detection.numero_detection).click()
        expect(page.locator("#tabpanel-detection-panel").get_by_text(last_update_text)).to_be_visible()

    return _assert_fiche_detection_derniere_mise_a_jour_visible


def test_can_add_zone(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()
    expect(page.get_by_text("Ajouter une zone", exact=True)).to_be_visible()


def test_cant_add_zone_if_already_one(live_server, page: Page):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()
    expect(page.get_by_text("Ajouter une zone", exact=True)).not_to_be_visible()


def test_can_publish_evenement(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    publish_btn = page.get_by_text("Publier l'événement", exact=True)
    expect(publish_btn).to_be_enabled()
    publish_btn.click()
    expect(page.get_by_text(f"Événement {evenement.numero} publié avec succès")).to_be_visible()

    publish_btn = page.get_by_text("Publier l'événement", exact=True)
    expect(publish_btn).not_to_be_visible()


def test_cant_forge_publication_of_evenement_we_are_not_owner(client, mocked_authentification_user):
    evenement = EvenementFactory(
        createur=Structure.objects.create(libelle="A new structure"), etat=Evenement.Etat.BROUILLON
    )
    response = client.get(evenement.get_absolute_url())

    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("publish"), data=payload)

    assert response.status_code == 302
    evenement.refresh_from_db()
    assert evenement.is_draft is True


def test_detail_synthese_switch(live_server, page):
    evenement = EvenementFactory()
    FicheDetectionFactory(evenement=evenement)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    detail_radio = page.locator("#detail-btn")
    expect(detail_radio).to_be_checked()
    detail_content = page.locator(".detail-content")
    expect(detail_content).to_be_visible()

    synthese_radio = page.locator("#synthese-btn")
    synthese_radio.click(force=True)
    expect(detail_content).to_be_hidden()

    detail_radio.click(force=True)
    expect(detail_content).to_be_visible()


def test_can_delete_evenement(live_server, page):
    evenement = EvenementFactory()
    assert Evenement.objects.count() == 1
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    page.get_by_text("Supprimer l'événement", exact=True).click()
    page.get_by_test_id("submit-delete-modal").click()

    expect(page.get_by_text(f"L'évènement {evenement.numero} a bien été supprimé")).to_be_visible()

    assert Evenement.objects.count() == 0
    assert Evenement._base_manager.get().pk == evenement.pk


def test_cant_forge_deletion_of_evenement_we_cant_see(client, mocked_authentification_user):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("soft-delete"), data=payload)

    assert response.status_code == 302
    evenement.refresh_from_db()
    assert evenement.is_deleted is False


def test_delete_evenement_will_delete_associated_detections(live_server, page):
    evenement = EvenementFactory()
    FicheDetectionFactory.create_batch(3, evenement=evenement)
    fiche_detection = FicheDetectionFactory()
    assert Evenement.objects.count() == 2
    assert FicheDetection.objects.count() == 4
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_role("button", name="Actions").click()
    page.get_by_text("Supprimer l'événement", exact=True).click()
    page.get_by_test_id("submit-delete-modal").click()

    expect(page.get_by_text(f"L'évènement {evenement.numero} a bien été supprimé")).to_be_visible()

    evenement_not_deleted = Evenement.objects.get()
    assert evenement_not_deleted == fiche_detection.evenement
    assert Evenement._base_manager.filter(is_deleted=True).get().pk == evenement.pk

    fiche_not_deleted = FicheDetection.objects.get()
    assert fiche_not_deleted == fiche_detection
    assert FicheDetection._base_manager.filter(evenement=evenement).count() == 3


def test_delete_button_not_visible_if_evenement_cloture(live_server, page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("Actions")).not_to_be_visible()
    expect(page.get_by_text("Supprimer l'événement", exact=True)).not_to_be_visible()


@pytest.mark.django_db
def test_cant_delete_if_evenement_is_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    payload = {
        "content_type_id": ContentType.objects.get_for_model(evenement).id,
        "content_id": evenement.pk,
    }
    response = client.post(reverse("soft-delete"), data=payload)

    evenement.refresh_from_db()
    assert response.status_code == 302
    assert evenement.is_deleted is False


def test_evenement_can_view_basic_data(live_server, page: Page):
    evenement = EvenementFactory(visibilite=Visibilite.NATIONALE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    expect(page.get_by_text(evenement.organisme_nuisible.libelle_court)).to_be_visible()
    expect(page.get_by_text(evenement.organisme_nuisible.code_oepp)).to_be_visible()
    expect(page.get_by_text(evenement.statut_reglementaire.libelle)).to_be_visible()
    expect(page.get_by_text("Dernière mise à jour le ")).to_be_visible()
    expect(page.get_by_text("Visibilité Toutes les structures")).to_be_visible()
    expect(page.get_by_text("Créateur Structure Test")).to_be_visible()


def test_view_mode_default_is_detail(live_server, page):
    fiche_detection = FicheDetectionFactory()
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    expect(page.locator("#detail-btn")).to_be_checked()
    expect(page.locator(".detail-content")).to_be_visible()


def test_view_mode_persistence_per_fiche(live_server, page):
    evenement1 = EvenementFactory()
    evenement2 = EvenementFactory()
    FicheDetectionFactory(evenement=evenement1)
    FicheDetectionFactory(evenement=evenement2)

    # Changer en mode synthèse pour le premier événement
    page.goto(f"{live_server.url}{evenement1.get_absolute_url()}")
    detail_content1 = page.locator(".detail-content")
    synthese_radio1 = page.locator("#synthese-btn")
    synthese_radio1.click(force=True)
    expect(detail_content1).to_be_hidden()

    # Vérifier que le second événement n'est pas impacté
    page.goto(f"{live_server.url}{evenement2.get_absolute_url()}")
    detail_radio2 = page.locator("#detail-btn")
    detail_content2 = page.locator(".detail-content")
    expect(detail_radio2).to_be_checked()
    expect(detail_content2).to_be_visible()

    # Revenir au premier événement et vérifier la persistance
    page.goto(f"{live_server.url}{evenement1.get_absolute_url()}")
    detail_content1 = page.locator(".detail-content")
    synthese_radio1 = page.locator("#synthese-btn")
    expect(synthese_radio1).to_be_checked()
    expect(detail_content1).to_be_hidden()


def test_fiche_detection_is_visible_and_selected_after_creation(live_server, page):
    evenement = EvenementFactory()
    detection_existante = FicheDetectionFactory(evenement=evenement)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("link", name="Ajouter une détection").click()
    page.get_by_role("button", name="Enregistrer").click()

    new_detection = FicheDetection.objects.filter(evenement=evenement).exclude(pk=detection_existante.pk).get()
    expect(page.get_by_role("tab", name=f"{new_detection.numero}")).to_be_visible()
    expect(page.get_by_role("tab", name=f"{new_detection.numero}")).to_have_class(re.compile(r"(^|\s)selected($|\s)"))


def test_fiche_detection_is_visible_and_selected_after_update(live_server, page):
    evenement = EvenementFactory()
    _, detection_2, _ = FicheDetectionFactory.create_batch(3, evenement=evenement)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name=f"{detection_2.numero}").click()

    # Simuler l'événement pour déclencher showOnlyActionsForDetection car le click sur le tab ne déclenche pas automatiquement
    # l'événement DSFR dsfr.conceal dans l'environnement de test, ce qui empêche la mise à jour du lien du bouton "Modifier"
    page.evaluate(f"""
       const panel = document.querySelector('#tabpanel-{detection_2.pk}-panel');
       panel.dispatchEvent(new CustomEvent('dsfr.conceal'));
    """)

    page.get_by_role("button", name="Modifier").click()
    page.get_by_role("button", name="Enregistrer").click()

    expect(page.get_by_role("tab", name=f"{detection_2.numero}")).to_be_visible()
    expect(page.get_by_role("tab", name=f"{detection_2.numero}")).to_have_class(re.compile(r"(^|\s)selected($|\s)"))


def test_fiche_zone_is_visible_after_creation(live_server, page):
    evenement = EvenementFactory()
    FicheDetectionFactory(evenement=evenement)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()
    page.get_by_role("button", name="Ajouter une zone").click()
    page.get_by_role("button", name="Enregistrer").click()

    expect(page.get_by_role("tab", name="Zone")).to_have_count(1)
    expect(page.get_by_text("Zone tampon")).to_be_visible()


def test_fiche_zone_is_visible_after_update(live_server, page):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)
    FicheDetectionFactory(evenement=evenement)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()
    page.get_by_role("button", name="Modifier").click()
    page.get_by_role("button", name="Enregistrer").click()

    expect(page.get_by_role("tab", name="Zone")).to_have_count(1)
    expect(page.get_by_text("Zone tampon")).to_be_visible()


def test_visibilite_locale_display(live_server, page: Page):
    evenement = EvenementFactory(visibilite=Visibilite.LOCALE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    visibilite_element = page.get_by_test_id("evenement-visibilite")
    expect(visibilite_element).to_contain_text(str(evenement.createur))
    expect(visibilite_element).to_contain_text(MUS_STRUCTURE)
    expect(visibilite_element).to_contain_text(BSV_STRUCTURE)
    expect(page.locator("#tooltip-visibilite")).not_to_be_visible()


def test_visibilite_nationale_display(live_server, page: Page):
    evenement = EvenementFactory(visibilite=Visibilite.NATIONALE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_test_id("evenement-visibilite")).to_have_text("Toutes les structures")
    expect(page.locator("#tooltip-visibilite")).not_to_be_visible()


def test_visibilite_limitee_display_short_text(live_server, page: Page):
    """Test l'affichage de la visibilité limitée avec une liste courte de structures."""
    evenement = EvenementFactory()
    structure = StructureFactory()
    evenement.allowed_structures.add(structure)
    evenement.visibilite = Visibilite.LIMITEE
    evenement.save()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    visibilite_element = page.get_by_test_id("evenement-visibilite")
    expect(visibilite_element).to_contain_text(structure.libelle)
    expect(visibilite_element).to_contain_text(MUS_STRUCTURE)
    expect(visibilite_element).to_contain_text(BSV_STRUCTURE)


def test_visibilite_limitee_display_long_text(live_server, page: Page):
    """Test l'affichage de la visibilité limitée avec une longue liste de structures."""
    evenement = EvenementFactory()
    structures = [StructureFactory(libelle=f"Structure Test {i}") for i in range(10)]
    evenement.allowed_structures.add(*structures)
    evenement.visibilite = Visibilite.LIMITEE
    evenement.save()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    # Vérification de la troncature
    texte_affiche = page.get_by_test_id("evenement-visibilite").inner_text().strip()
    assert len(texte_affiche.rstrip("…")) <= 150
    assert texte_affiche.endswith("…")

    # Vérification que chaque structure est présente dans le tooltip
    tooltip = page.locator("#tooltip-visibilite")
    for i in range(10):
        expect(tooltip).to_contain_text(f"Structure Test {i}")


def test_will_edit_correct_fiche_detection(live_server, page: Page):
    evenement = EvenementFactory()
    fiche_1 = FicheDetectionFactory(evenement=evenement)
    fiche_2 = FicheDetectionFactory(evenement=evenement)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name=fiche_1.numero_detection).click()
    page.get_by_role("button", name="Modifier").click()
    assert fiche_1.get_update_url() in page.url

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name=fiche_2.numero_detection).click()
    page.get_by_role("button", name="Modifier").click()
    assert fiche_2.get_update_url() in page.url


@pytest.mark.parametrize("createur", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_visibilite_display_text_when_evenement_locale_and_createur_ac(
    live_server, page: Page, mocked_authentification_user, createur
):
    createur, _ = Structure.objects.get_or_create(libelle=createur)
    Contact.objects.get_or_create(structure=createur)
    evenement_mus = EvenementFactory(createur=createur, visibilite=Visibilite.LOCALE)
    mocked_authentification_user.agent.structure = createur
    mocked_authentification_user.save()
    page.goto(f"{live_server.url}{evenement_mus.get_absolute_url()}")
    visibilite_element = page.get_by_test_id("evenement-visibilite")
    expect(visibilite_element).to_contain_text(MUS_STRUCTURE)
    expect(visibilite_element).to_contain_text(BSV_STRUCTURE)


def test_hide_details_synthese_switch_if_evenement_draft(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("Détail")).not_to_be_visible()
    expect(page.get_by_text("Synthèse")).not_to_be_visible()


@pytest.mark.parametrize("etat", [Etat.EN_COURS, Etat.CLOTURE])
def test_show_details_synthese_switch(live_server, page: Page, etat: Etat):
    evenement = EvenementFactory(etat=etat)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("Détail")).to_be_visible()
    expect(page.get_by_text("Synthèse")).to_be_visible()


def test_first_detection_by_number_is_selected_by_default(live_server, page: Page):
    """Test que la première fiche de détection (par numéro et non par id) est sélectionnée par défaut."""
    evenement = EvenementFactory()

    FicheDetectionFactory(evenement=evenement, numero_detection=f"{evenement.numero}.3")
    FicheDetectionFactory(evenement=evenement, numero_detection=f"{evenement.numero}.2")
    detection_3 = FicheDetectionFactory(evenement=evenement, numero_detection=f"{evenement.numero}.1")

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    expect(page.get_by_role("tab", name=detection_3.numero_detection)).to_have_class(
        re.compile(r"(^|\s)selected($|\s)")
    )


def test_detections_are_order_by_detection_number_not_by_id(live_server, page: Page):
    """Test que les fiches détections sont triées par numéro et non par id."""
    evenement = EvenementFactory()
    detection_10 = FicheDetectionFactory(evenement=evenement, numero_detection=f"{evenement.numero}.10")
    detection_3 = FicheDetectionFactory(evenement=evenement, numero_detection=f"{evenement.numero}.3")
    detection_2 = FicheDetectionFactory(evenement=evenement, numero_detection=f"{evenement.numero}.2")
    detection_1 = FicheDetectionFactory(evenement=evenement, numero_detection=f"{evenement.numero}.1")

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    expect(page.locator("#tabpanel-detection-panel ul > li")).to_contain_text(
        [detection_1.numero, detection_2.numero, detection_3.numero, detection_10.numero]
    )


def test_documents_panel_is_visible_when_clicking_on_documents_link_twice(live_server, page: Page):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone)
    FicheDetectionFactory(evenement=evenement)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_role("tab", name="Zone").click()
    page.get_by_role("link", name="documents").click()
    expect(page.get_by_label("Documents")).to_be_visible()
    page.get_by_test_id("contacts").click()
    page.get_by_role("link", name="documents").click()
    expect(page.get_by_label("Documents")).to_be_visible()


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_evenement_creation(live_server, page: Page):
    evenement = EvenementFactory()
    assert evenement.date_derniere_mise_a_jour is not None
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    last_update_text = f"Dernière mise à jour le {get_date_formated(evenement.date_derniere_mise_a_jour)}"
    expect(page.get_by_test_id("evenement-header").get_by_text(last_update_text)).to_be_visible()


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_evenement_update(live_server, page: Page):
    evenement = EvenementFactory()
    date_derniere_mise_a_jour = evenement.date_derniere_mise_a_jour

    evenement.organisme_nuisible = OrganismeNuisibleFactory()
    evenement.save()

    assert date_derniere_mise_a_jour < evenement.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    last_update_text = f"Dernière mise à jour le {get_date_formated(evenement.date_derniere_mise_a_jour)}"
    expect(page.get_by_test_id("evenement-header").get_by_text(last_update_text)).to_be_visible()


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_fiche_detection_creation(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    evenement = EvenementFactory()
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_fiche_detection_update(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_detection = FicheDetectionFactory()
    date_derniere_mise_a_jour = fiche_detection.date_derniere_mise_a_jour

    fiche_detection.commentaire = "Nouveau commentaire"
    fiche_detection.save()

    fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_detection.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_lieu_creation(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_detection = FicheDetectionFactory()
    date_derniere_mise_a_jour = fiche_detection.date_derniere_mise_a_jour

    LieuFactory(fiche_detection=fiche_detection)

    fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_detection.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_lieu_update(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    lieu = LieuFactory()
    date_derniere_mise_a_jour = lieu.fiche_detection.date_derniere_mise_a_jour

    lieu.nom = "Nouveau nom"
    lieu.save()

    lieu.fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < lieu.fiche_detection.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{lieu.fiche_detection.evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(lieu.fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_lieu_delete(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    lieu = LieuFactory()
    date_derniere_mise_a_jour = lieu.fiche_detection.date_derniere_mise_a_jour

    lieu.delete()

    lieu.fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < lieu.fiche_detection.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{lieu.fiche_detection.evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(lieu.fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_prelevement_creation(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_detection = FicheDetectionFactory()
    date_derniere_mise_a_jour = fiche_detection.date_derniere_mise_a_jour

    PrelevementFactory(lieu__fiche_detection=fiche_detection)

    fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_detection.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_prelevement_update(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    prelevement = PrelevementFactory()
    fiche_detection = prelevement.lieu.fiche_detection
    date_derniere_mise_a_jour = fiche_detection.date_derniere_mise_a_jour
    version = Version.objects.get_for_object(fiche_detection).first()

    prelevement.resultat = Prelevement.Resultat.DETECTE
    prelevement.save()

    fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_detection.date_derniere_mise_a_jour
    assert Version.objects.get_for_object(fiche_detection).first().id == version.id
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_prelevement_delete(
    live_server, page: Page, assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated
):
    prelevement = PrelevementFactory()
    fiche_detection = prelevement.lieu.fiche_detection
    date_derniere_mise_a_jour = fiche_detection.date_derniere_mise_a_jour

    prelevement.delete()

    fiche_detection.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_detection.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    assert_fiche_detection_derniere_mise_a_jour_is_visible_and_updated(fiche_detection)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_fiche_zone_delimitee_creation(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    evenement = EvenementFactory()

    fiche_zone_delimitee = FicheZoneFactory()
    evenement.fiche_zone_delimitee = fiche_zone_delimitee
    evenement.save()

    assert fiche_zone_delimitee.date_derniere_mise_a_jour is not None
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_fiche_zone_delimitee_update(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    date_derniere_mise_a_jour = evenement.fiche_zone_delimitee.date_derniere_mise_a_jour

    fiche_zone_delimitee.commentaire = "Nouveau commentaire"
    fiche_zone_delimitee.save()

    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_fiche_zone_delimitee_delete(live_server, page: Page):
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    date_derniere_mise_a_jour = evenement.fiche_zone_delimitee.date_derniere_mise_a_jour

    evenement.fiche_zone_delimitee.delete()

    evenement.refresh_from_db()
    assert date_derniere_mise_a_jour < evenement.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    last_update_text = f"Dernière mise à jour le {get_date_formated(fiche_zone_delimitee.date_derniere_mise_a_jour)}"
    expect(page.get_by_test_id("evenement-header").get_by_text(last_update_text)).to_be_visible()


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_zone_infestee_creation(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    date_derniere_mise_a_jour = fiche_zone_delimitee.date_derniere_mise_a_jour

    ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)

    fiche_zone_delimitee.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_zone_infestee_update(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    date_derniere_mise_a_jour = fiche_zone_delimitee.date_derniere_mise_a_jour

    zone_infestee.nom = "Nouveau nom"
    zone_infestee.save()

    fiche_zone_delimitee.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_zone_infestee_delete(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    date_derniere_mise_a_jour = fiche_zone_delimitee.date_derniere_mise_a_jour

    zone_infestee.delete()

    fiche_zone_delimitee.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_add_detection_in_hors_zone_delimitee(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    date_derniere_mise_a_jour = fiche_zone_delimitee.date_derniere_mise_a_jour

    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()

    fiche_zone_delimitee.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_delete_detection_in_hors_zone_delimitee(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection = FicheDetectionFactory(evenement=evenement, hors_zone_infestee=fiche_zone_delimitee)
    date_derniere_mise_a_jour = fiche_zone_delimitee.date_derniere_mise_a_jour

    fiche_detection.hors_zone_infestee = None
    fiche_detection.save()

    fiche_zone_delimitee.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_add_detection_in_zone_infestee(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    date_derniere_mise_a_jour = fiche_zone_delimitee.date_derniere_mise_a_jour

    fiche_detection.zone_infestee = zone_infestee
    fiche_detection.save()

    fiche_zone_delimitee.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)


@pytest.mark.django_db
def test_date_derniere_mise_a_jour_after_delete_detection_in_zone_infestee(
    live_server, page: Page, assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated
):
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=evenement.fiche_zone_delimitee)
    fiche_detection = FicheDetectionFactory(evenement=evenement, zone_infestee=zone_infestee)
    date_derniere_mise_a_jour = fiche_zone_delimitee.date_derniere_mise_a_jour

    fiche_detection.zone_infestee = None
    fiche_detection.save()

    fiche_zone_delimitee.refresh_from_db()
    assert date_derniere_mise_a_jour < fiche_zone_delimitee.date_derniere_mise_a_jour
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert_fiche_zone_derniere_mise_a_jour_is_visible_and_updated(fiche_zone_delimitee)
