from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest

from core.factories import StructureFactory
from core.models import Structure
from sv.factories import EvenementFactory, FicheDetectionFactory, FicheZoneFactory, ZoneInfesteeFactory
from sv.models import Evenement, FicheDetection, FicheZoneDelimitee, ZoneInfestee
from sv.tests.test_utils import FicheZoneDelimiteeFormPage


def test_fichezonedelimitee_update_form_content(live_server, page: Page, choice_js_fill):
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)

    for _ in range(3):
        FicheDetectionFactory(hors_zone_infestee=fiche_zone_delimitee, evenement=evenement)

    for zone_infestee in ZoneInfesteeFactory.create_batch(2, fiche_zone_delimitee=fiche_zone_delimitee):
        for _ in range(2):
            FicheDetectionFactory(zone_infestee=zone_infestee, evenement=evenement)

    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.check_update_form_content(fiche_zone_delimitee)


def test_fichezonedelimitee_update_without_zone_infestee_form_submit(live_server, page: Page, choice_js_fill):
    fiche_zone_delimitee = FicheZoneFactory()
    EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    new_fiche_zone_delimitee = FicheZoneFactory.build()

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.fill_form(new_fiche_zone_delimitee)
    form_page.submit_update_form()
    fiche_zone_delimitee_updated = FicheZoneDelimitee.objects.get(id=fiche_zone_delimitee.id)
    assert fiche_zone_delimitee_updated.date_creation.replace(
        microsecond=0
    ) == fiche_zone_delimitee.date_creation.replace(microsecond=0)
    assert fiche_zone_delimitee_updated.evenement == fiche_zone_delimitee.evenement
    assert fiche_zone_delimitee_updated.createur == fiche_zone_delimitee.createur
    assert fiche_zone_delimitee_updated.commentaire == new_fiche_zone_delimitee.commentaire
    assert fiche_zone_delimitee_updated.rayon_zone_tampon == new_fiche_zone_delimitee.rayon_zone_tampon
    assert fiche_zone_delimitee_updated.unite_rayon_zone_tampon == new_fiche_zone_delimitee.unite_rayon_zone_tampon
    assert fiche_zone_delimitee_updated.surface_tampon_totale == new_fiche_zone_delimitee.surface_tampon_totale
    assert (
        fiche_zone_delimitee_updated.unite_surface_tampon_totale == new_fiche_zone_delimitee.unite_surface_tampon_totale
    )


def test_update_zone_infestee(live_server, page: Page, choice_js_fill):
    zone_infestee = ZoneInfesteeFactory()
    fiche_detection = FicheDetectionFactory(evenement__fiche_zone_delimitee=zone_infestee.fiche_zone_delimitee)
    new_zone_infestee = ZoneInfesteeFactory.build()

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{zone_infestee.fiche_zone_delimitee.get_update_url()}")
    form_page.fill_zone_infestee_form(0, new_zone_infestee, (fiche_detection,))
    form_page.submit_update_form()
    zone_infestee_updated = ZoneInfestee.objects.get(id=zone_infestee.id)
    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert zone_infestee_updated.nom == new_zone_infestee.nom
    assert zone_infestee_updated.caracteristique_principale == new_zone_infestee.caracteristique_principale
    assert zone_infestee_updated.surface_infestee_totale == new_zone_infestee.surface_infestee_totale
    assert zone_infestee_updated.unite_surface_infestee_totale == new_zone_infestee.unite_surface_infestee_totale
    assert zone_infestee_updated.rayon == new_zone_infestee.rayon
    assert zone_infestee_updated.unite_rayon == new_zone_infestee.unite_rayon
    assert fiche_detection_updated.zone_infestee == zone_infestee_updated


def test_add_zone_infestee(live_server, page: Page, choice_js_fill):
    zone_infestee = ZoneInfesteeFactory()
    fiche_zone = zone_infestee.fiche_zone_delimitee
    new_zone_infestee = ZoneInfesteeFactory.build()
    fiche_detection = FicheDetectionFactory(evenement__fiche_zone_delimitee=fiche_zone)

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone.get_update_url()}")
    form_page.add_new_zone_infestee(new_zone_infestee, (fiche_detection,))
    form_page.submit_update_form()
    zone_infestee_created = ZoneInfestee.objects.get(fiche_zone_delimitee=fiche_zone, nom=new_zone_infestee.nom)
    fiche_detection_updated = FicheDetection.objects.get(id=fiche_detection.id)
    assert zone_infestee_created.nom == new_zone_infestee.nom
    assert zone_infestee_created.caracteristique_principale == new_zone_infestee.caracteristique_principale
    assert zone_infestee_created.surface_infestee_totale == new_zone_infestee.surface_infestee_totale
    assert zone_infestee_created.unite_surface_infestee_totale == new_zone_infestee.unite_surface_infestee_totale
    assert zone_infestee_created.rayon == new_zone_infestee.rayon
    assert zone_infestee_created.unite_rayon == new_zone_infestee.unite_rayon
    assert fiche_detection_updated.zone_infestee == zone_infestee_created


def test_update_can_delete_zone_infestee(live_server, page: Page, choice_js_fill):
    to_keep = ZoneInfesteeFactory(nom="To keep")
    FicheDetectionFactory(evenement__fiche_zone_delimitee=to_keep.fiche_zone_delimitee)
    to_delete = ZoneInfesteeFactory(nom="To delete", fiche_zone_delimitee=to_keep.fiche_zone_delimitee)

    page.goto(f"{live_server.url}{to_keep.fiche_zone_delimitee.get_update_url()}")

    page.get_by_role("button", name="Supprimer la zone infestée").nth(1).click()
    page.get_by_role("alertdialog", name="Supprimer").get_by_role("button", name="Supprimer").click()
    page.get_by_role("button", name="Enregistrer les modifications", exact=True).click()

    assert ZoneInfestee.objects.get(id=to_keep.id).nom == "To keep"
    with pytest.raises(ZoneInfestee.DoesNotExist):
        ZoneInfestee.objects.get(id=to_delete.id)


def test_update_can_add_and_delete_zone_infestee(live_server, page: Page, choice_js_fill):
    fiche_zone = FicheZoneFactory()
    FicheDetectionFactory(evenement__fiche_zone_delimitee=fiche_zone)
    new_zone_infestee_1 = ZoneInfesteeFactory.build(nom="To keep")
    new_zone_infestee_2 = ZoneInfesteeFactory.build(nom="To delete")

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone.get_update_url()}")
    form_page.add_new_zone_infestee(new_zone_infestee_1, ())
    form_page.add_new_zone_infestee(new_zone_infestee_2, ())

    page.get_by_role("button", name="Supprimer la zone infestée").nth(1).click()
    page.get_by_role("alertdialog", name="Supprimer").get_by_role("button", name="Supprimer").click()
    page.get_by_role("button", name="Enregistrer les modifications", exact=True).click()

    ZoneInfestee.objects.get(nom="To keep")
    with pytest.raises(ZoneInfestee.DoesNotExist):
        ZoneInfestee.objects.get(id=new_zone_infestee_2.id)


def test_update_form_cant_have_same_detection_in_hors_zone_infestee_and_zone_infestee(
    live_server,
    page: Page,
    choice_js_fill,
) -> None:
    fiche_detection = FicheDetectionFactory()
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = fiche_detection.evenement
    evenement.fiche_zone_delimitee = fiche_zone_delimitee
    evenement.save()
    ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.force_add_zone_infestee(
        page.locator("#zones-infestees .fr-col-4:nth-of-type(1) [data-test-locator='form-detections-select']"),
        fiche_detection,
    )
    form_page.save()
    expect(
        page.get_by_text(
            f"La fiche détection {str(fiche_detection.numero)} ne peut pas être sélectionnée à la fois dans les zones infestées et dans hors zone infestée."
        )
    ).to_be_visible()
    fiche_detection.refresh_from_db()
    assert fiche_detection.zone_infestee is None


def test_update_form_cant_have_same_detection_in_two_zone_infestee(live_server, page: Page, choice_js_fill) -> None:
    fiche_zone_delimitee = FicheZoneFactory()
    fiche_detection = FicheDetectionFactory(evenement__fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection.zone_infestee = ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection.save()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.add_new_zone_infestee(ZoneInfesteeFactory(), (fiche_detection,), bypass_front=True)
    form_page.save()
    expect(
        page.get_by_text(
            f"Les fiches détection suivantes sont dupliquées dans les zones infestées : {str(fiche_detection.numero)}."
        )
    ).to_be_visible()


def test_has_same_surface_units_order_for_zone_tampon_and_zone_infestee(live_server, page: Page, choice_js_fill):
    zone_infestee = ZoneInfesteeFactory()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{zone_infestee.fiche_zone_delimitee.get_update_url()}")
    assert form_page.has_same_surface_units_order_for_zone_tampon_and_zone_infestee() is True


def test_has_same_rayon_units_order_for_zone_tampon_and_zone_infestee(live_server, page: Page, choice_js_fill):
    zone_infestee = ZoneInfesteeFactory()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{zone_infestee.fiche_zone_delimitee.get_update_url()}")
    assert form_page.has_same_rayon_units_order_for_zone_tampon_and_zone_infestee() is True


def test_fichezonedelimitee_update_adds_agent_and_structure_contacts(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    """Test que la modification d'une fiche zone délimitée ajoute l'agent et sa structure comme contacts"""
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    new_fiche_zone_delimitee = FicheZoneFactory.build()

    # Modification de la fiche
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.fill_form(new_fiche_zone_delimitee)
    form_page.submit_update_form()

    # Vérification que la modification a bien eu lieu
    fiche_zone_delimitee_updated = FicheZoneDelimitee.objects.get(id=fiche_zone_delimitee.id)
    assert fiche_zone_delimitee_updated.commentaire == new_fiche_zone_delimitee.commentaire

    # Vérification des contacts
    evenement.refresh_from_db()
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).exists()
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).exists()

    # Vérification de l'interface
    page.get_by_test_id("contacts").click()
    expect(
        page.locator("[data-testid='contacts-agents']").get_by_text(str(mocked_authentification_user.agent), exact=True)
    ).to_be_visible()
    expect(
        page.locator("[data-testid='contacts-structures']").get_by_text(
            str(mocked_authentification_user.agent.structure), exact=True
        )
    ).to_be_visible()


def test_fichezonedelimitee_update_multiple_times_adds_contacts_once(
    live_server, page: Page, choice_js_fill, mocked_authentification_user
):
    """Test que plusieurs modifications d'une fiche zone délimitée n'ajoutent qu'une fois les contacts"""
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    new_fiche_zone1 = FicheZoneFactory.build()
    new_fiche_zone2 = FicheZoneFactory.build()

    # Première modification
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.fill_form(new_fiche_zone1)
    form_page.submit_update_form()

    # Seconde modification
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    form_page.fill_form(new_fiche_zone2)
    form_page.submit_update_form()

    # Vérification que la dernière modification a bien eu lieu
    fiche_zone_delimitee_updated = FicheZoneDelimitee.objects.get(id=fiche_zone_delimitee.id)
    assert fiche_zone_delimitee_updated.commentaire == new_fiche_zone2.commentaire

    # Vérification des contacts
    evenement.refresh_from_db()
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).count() == 1
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).count() == 1

    # Vérification de l'interface
    page.get_by_test_id("contacts").click()
    expect(
        page.locator("[data-testid='contacts-agents']").get_by_text(str(mocked_authentification_user.agent), exact=True)
    ).to_be_visible()
    expect(
        page.locator("[data-testid='contacts-structures']").get_by_text(
            str(mocked_authentification_user.agent.structure), exact=True
        )
    ).to_be_visible()


def test_can_update_fiche_zone_if_evenement_brouillon(live_server, page: Page, choice_js_fill):
    fiche_zone = FicheZoneFactory()
    EvenementFactory(fiche_zone_delimitee=fiche_zone, etat=Evenement.Etat.BROUILLON)
    new_fiche_zone = FicheZoneFactory.build()

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone.get_update_url()}")
    form_page.fill_form(new_fiche_zone)
    form_page.submit_update_form()

    fiche_zone_updated = FicheZoneDelimitee.objects.get(id=fiche_zone.id)
    assert fiche_zone_updated.commentaire == new_fiche_zone.commentaire
    assert fiche_zone_updated.rayon_zone_tampon == new_fiche_zone.rayon_zone_tampon
    assert fiche_zone_updated.unite_rayon_zone_tampon == new_fiche_zone.unite_rayon_zone_tampon
    assert fiche_zone_updated.surface_tampon_totale == new_fiche_zone.surface_tampon_totale
    assert fiche_zone_updated.unite_surface_tampon_totale == new_fiche_zone.unite_surface_tampon_totale


def test_fiche_zone_update_has_locking_protection(
    live_server,
    page: Page,
    mocked_authentification_user,
):
    fiche_zone = FicheZoneFactory(commentaire="AAA")
    EvenementFactory(fiche_zone_delimitee=fiche_zone)
    page.goto(f"{live_server.url}{fiche_zone.get_update_url()}")
    page.get_by_label("Commentaire").fill("BBB")

    fiche_zone.commentaire = "CCC"
    fiche_zone.save()

    page.get_by_role("button", name="Enregistrer les modifications", exact=True).click()
    page.wait_for_timeout(600)

    fiche_zone.refresh_from_db()
    assert fiche_zone.commentaire == "CCC"
    initial_timestamp = page.evaluate("performance.timing.navigationStart")
    expect(
        page.get_by_text(
            "Vos modifications n'ont pas été enregistrées. Un autre utilisateur a modifié cet objet. Fermer cette modale pour charger la dernière version."
        )
    ).to_be_visible()
    page.keyboard.press("Escape")
    page.wait_for_function(f"performance.timing.navigationStart > {initial_timestamp}")


def test_cant_access_update_zone_delimitee_form_of_evenement_i_cant_see(client):
    fiche_zone = FicheZoneFactory()
    evenement = EvenementFactory(fiche_zone_delimitee=fiche_zone, createur=StructureFactory())
    assert client.get(evenement.get_absolute_url()).status_code == 403

    assert client.get(fiche_zone.get_update_url()).status_code == 403


def test_cant_forge_update_of_zone_delimitee_i_cant_see(client):
    fiche_zone = FicheZoneFactory()
    EvenementFactory(fiche_zone_delimitee=fiche_zone, createur=Structure.objects.create(libelle="A new structure"))

    response = client.get(fiche_zone.get_absolute_url())
    assert response.status_code == 403

    payload = {
        "evenement": [""],
        "organisme_nuisible": ["Abaca bunchy top virus"],
        "statut_reglementaire": ["organisme quarantaine prioritaire"],
        "commentaire": ["AAA"],
        "rayon_zone_tampon": [""],
        "unite_rayon_zone_tampon": ["km"],
        "surface_tampon_totale": [""],
        "unite_surface_tampon_totale": ["m2"],
        "zoneinfestee_set-TOTAL_FORMS": ["0"],
        "zoneinfestee_set-INITIAL_FORMS": ["0"],
        "zoneinfestee_set-MIN_NUM_FORMS": ["0"],
        "zoneinfestee_set-MAX_NUM_FORMS": ["1000"],
    }
    response = client.post(reverse("sv:fiche-zone-delimitee-update", kwargs={"pk": fiche_zone.pk}), data=payload)

    assert response.status_code == 403
    fiche_zone.refresh_from_db()
    assert fiche_zone.commentaire != "AAAA"


def test_shows_correct_organisme_and_statut(live_server, page: Page):
    evenement = EvenementFactory(fiche_zone_delimitee=FicheZoneFactory())

    page.goto(f"{live_server.url}{evenement.fiche_zone_delimitee.get_update_url()}")

    expect(page.get_by_text(str(evenement.organisme_nuisible))).to_be_visible()
    expect(page.get_by_text(str(evenement.statut_reglementaire))).to_be_visible()


def test_update_form_cant_have_same_detection_in_hors_zone_infestee_and_zone_infestee_check_ui(
    live_server,
    page: Page,
    choice_js_fill,
    choice_js_option_disabled,
):
    fiche_detection = FicheDetectionFactory()
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = fiche_detection.evenement
    evenement.fiche_zone_delimitee = fiche_zone_delimitee
    evenement.save()
    ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()

    FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    choice_js_option_disabled(
        page,
        "#zones-infestees .fr-col-4:nth-of-type(1) .choices__input--cloned:first-of-type",
        str(fiche_detection.numero),
    )


def test_update_form_cant_have_same_detection_in_hors_zone_infestee_and_in_new_zone_infestee_check_ui(
    live_server,
    page: Page,
    choice_js_fill,
    choice_js_option_disabled,
):
    fiche_detection = FicheDetectionFactory()
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = fiche_detection.evenement
    evenement.fiche_zone_delimitee = fiche_zone_delimitee
    evenement.save()
    ZoneInfesteeFactory(fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()
    other_detection = FicheDetectionFactory(evenement=evenement)

    FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")

    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.add_new_zone_infestee(ZoneInfesteeFactory.build(), ())
    choice_js_option_disabled(
        page,
        "#zones-infestees .fr-col-4:nth-of-type(2) .choices__input--cloned:first-of-type",
        str(fiche_detection.numero),
    )

    choice_js_fill(
        page,
        "#zones-infestees .fr-col-4:nth-of-type(2) .choices__input--cloned:first-of-type",
        str(other_detection.numero),
        str(other_detection.numero),
    )
    choice_js_option_disabled(
        page,
        ".fichezoneform__detections-hors-zone-infestee .choices__list--multiple",
        str(other_detection.numero),
    )


def test_update_form_remove_from_detections_list_refresh_choices_for_other_lists(
    live_server,
    page: Page,
    choice_js_fill,
):
    fiche_detection = FicheDetectionFactory()
    fiche_zone_delimitee = FicheZoneFactory()
    evenement = fiche_detection.evenement
    evenement.fiche_zone_delimitee = fiche_zone_delimitee
    evenement.save()

    detection_1 = FicheDetectionFactory(
        evenement=evenement, zone_infestee=ZoneInfesteeFactory(nom="Test 1", fiche_zone_delimitee=fiche_zone_delimitee)
    )

    FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone_delimitee.get_update_url()}")
    page.locator(f"button[aria-label='Remove item: {detection_1.id}']").click(force=True)
    choice_js_fill(
        page,
        ".fichezoneform__detections-hors-zone-infestee .choices__input--cloned:first-of-type",
        str(detection_1.numero),
        str(detection_1.numero),
    )
    page.locator("#save-btn").click()

    detection_1.refresh_from_db()
    assert detection_1.zone_infestee is None
    assert detection_1.hors_zone_infestee == fiche_zone_delimitee


def test_cant_see_update_fiche_zone_delimitee_btn_if_evenement_is_cloture(live_server, page: Page):
    evenement = EvenementFactory(fiche_zone_delimitee=FicheZoneFactory(), etat=Evenement.Etat.CLOTURE)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Zone").click()

    expect(page.get_by_role("button", name="Modifier")).not_to_be_visible()


def test_cant_access_update_fiche_zone_delimitee_form_if_evenement_is_cloture(client):
    fiche_zone = FicheZoneFactory()
    EvenementFactory(fiche_zone_delimitee=fiche_zone, etat=Evenement.Etat.CLOTURE)

    response = client.get(fiche_zone.get_update_url())

    assert response.status_code == 403


@pytest.mark.django_db
def test_cant_update_fiche_zone_delimitee_form_if_evenement_is_cloture(client):
    fiche_zone = FicheZoneFactory()
    EvenementFactory(fiche_zone_delimitee=fiche_zone, etat=Evenement.Etat.CLOTURE)

    response = client.post(fiche_zone.get_update_url(), data={"commentaire": "AAAA"})

    assert response.status_code == 403
    fiche_zone.refresh_from_db()
    assert fiche_zone.commentaire != "AAAA"
