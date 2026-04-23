from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from sv.factories import FicheZoneFactory, OrganismeNuisibleFactory, StructurePreleveuseFactory, ZoneInfesteeFactory
from sv.models import Evenement, FicheZoneDelimitee, Lieu, Prelevement, StatutReglementaire, StructurePreleveuse
from sv.tests.test_utils import FicheDetectionFormDomElements, FicheZoneDelimiteeFormPage, PrelevementFormDomElements


def test_evenement_history_content(
    live_server, page, form_elements: FicheDetectionFormDomElements, lieu_form_elements, choice_js_fill
):
    statut, _ = StatutReglementaire.objects.get_or_create(libelle="organisme quarantaine prioritaire")
    organisme_nuisible = OrganismeNuisibleFactory()
    page.goto(f"{live_server.url}{reverse('sv:fiche-detection-creation')}")
    choice_js_fill(
        page,
        "#organisme-nuisible .choices__list--single",
        organisme_nuisible.libelle_court,
        organisme_nuisible.libelle_court,
    )
    page.get_by_label("Statut réglementaire").select_option(value=str(statut.id))
    page.get_by_test_id("bottom-action-btns").get_by_role("button", name="Enregistrer").click()

    evenement = Evenement.objects.get()
    detection = evenement.detections.get()

    page.goto(f"{live_server.url}{evenement.get_update_url()}")
    page.get_by_label("Statut réglementaire").select_option("organisme émergent")
    page.get_by_role("button", name="Enregistrer").click()

    page.goto(f"{live_server.url}{detection.get_update_url()}")
    form_elements.commentaire_input.fill("My test comment")
    form_elements.save_update_btn.click()

    page.goto(f"{live_server.url}{detection.get_update_url()}")
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill("Mon lieu")
    lieu_form_elements.lieu_site_inspection_input.select_option("INCONNU")
    lieu_form_elements.save_btn.click()
    form_elements.save_update_btn.click()

    page.goto(f"{live_server.url}{detection.get_update_url()}")
    page.get_by_test_id("lieu-edit-btn").click()
    lieu_form_elements.nom_input.fill("Mon lieu 2")
    lieu_form_elements.lieu_site_inspection_input.select_option("INCONNU")
    lieu_form_elements.save_btn.click()
    form_elements.save_update_btn.click()

    initial_fiche_zone = FicheZoneFactory.build()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, evenement)
    form_page.fill_form(initial_fiche_zone)
    form_page.save()

    fiche_zone = FicheZoneDelimitee.objects.get()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone.get_update_url()}")
    form_page.commentaire.fill("Test")
    form_page.submit_update_form()

    content_type = ContentType.objects.get_for_model(Evenement)
    url = reverse("revision-list", kwargs={"content_type": content_type.pk, "pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    expected_rows = [
        [
            "Doe John",
            "Structure Test",
            mock.ANY,
            f"Fiche Zone Délimitée ({evenement.numero}) - Commentaire",
            initial_fiche_zone.commentaire,
            "Test",
            "Vide",
        ],
        [
            "Doe John",
            "Structure Test",
            mock.ANY,
            f"Fiche Détection ({detection.numero}) - Lieu (Mon Lieu) - Nom",
            "Mon lieu",
            "Mon lieu 2",
            "Vide",
        ],
        [
            "Doe John",
            "Structure Test",
            mock.ANY,
            f"Fiche Détection ({detection.numero}) - Lieu",
            "Vide",
            "Objet ajouté : Lieu Mon lieu",
            "Vide",
        ],
        [
            "Doe John",
            "Structure Test",
            mock.ANY,
            f"Fiche Détection ({detection.numero}) - Commentaire",
            "Vide",
            "My test comment",
            "Vide",
        ],
        [
            "Doe John",
            "Structure Test",
            mock.ANY,
            "Fiche Zone Delimitée",
            "Vide",
            mock.ANY,
            "Vide",
        ],
        [
            "Doe John",
            "Structure Test",
            mock.ANY,
            "Statut Règlementaire De L'Organisme",
            "<StatutReglementaire: organisme quarantaine prioritaire>",
            "<StatutReglementaire: organisme émergent>",
            "Vide",
        ],
        ["Doe John", "Structure Test", mock.ANY, "Statut", "Vide", "Brouillon", "Vide"],
        [],  # Header
    ]

    texts = []
    for row in page.locator("table tr").all():
        texts.append([t.strip() for t in row.locator("td").all_text_contents()])

    assert len(texts) == len(expected_rows)
    for expected in expected_rows:
        assert expected in texts, f"{expected} not found in {texts}"


def test_evenement_history_content_prelevement_shows_even_when_no_modification_on_lieu(
    live_server, page, form_elements: FicheDetectionFormDomElements, lieu_form_elements, choice_js_fill
):
    statut, _ = StatutReglementaire.objects.get_or_create(libelle="organisme quarantaine prioritaire")
    StructurePreleveuseFactory()
    organisme_nuisible = OrganismeNuisibleFactory()
    page.goto(f"{live_server.url}{reverse('sv:fiche-detection-creation')}")
    choice_js_fill(
        page,
        "#organisme-nuisible .choices__list--single",
        organisme_nuisible.libelle_court,
        organisme_nuisible.libelle_court,
    )
    page.get_by_label("Statut réglementaire").select_option(value=str(statut.id))
    form_elements.add_lieu_btn.click()
    lieu_form_elements.nom_input.fill("Mon lieu")
    lieu_form_elements.lieu_site_inspection_input.select_option("INCONNU")
    lieu_form_elements.save_btn.click()
    page.get_by_test_id("bottom-action-btns").get_by_role("button", name="Enregistrer").click()

    evenement = Evenement.objects.get()
    detection = evenement.detections.get()
    Lieu.objects.get()

    page.goto(f"{live_server.url}{detection.get_update_url()}")
    form_elements.add_prelevement_btn.click()
    prelevement_form_elements = PrelevementFormDomElements(page)
    prelevement_form_elements.date_prelevement_input.click()
    prelevement_form_elements.structure_input.select_option(value=str(StructurePreleveuse.objects.first().id))
    prelevement_form_elements.date_prelevement_input.fill("2021-01-01")
    prelevement_form_elements.resultat_input(Prelevement.Resultat.DETECTE).click()
    prelevement_form_elements.type_analyse_input("première intention").click()
    prelevement_form_elements.save_btn.click()
    page.get_by_test_id("bottom-action-btns").get_by_role("button", name="Enregistrer").click()

    prelevement = Prelevement.objects.get()
    page.goto(f"{live_server.url}{detection.get_update_url()}")
    prelevement_form_elements = PrelevementFormDomElements(page)
    page.locator(".prelevement-edit-btn").click()
    page.locator(f"#id_prelevements-{prelevement.id}-numero_echantillon").fill("Test")
    prelevement_form_elements.save_btn.click()
    page.get_by_test_id("bottom-action-btns").get_by_role("button", name="Enregistrer").click()

    content_type = ContentType.objects.get_for_model(Evenement)
    url = reverse("revision-list", kwargs={"content_type": content_type.pk, "pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    creation_text = f"Objet ajouté : Prelevement Prélèvement n° {prelevement.id}"
    update_text = f"Fiche Détection ({detection.numero}) - Lieu (Mon Lieu) - Prélèvement (Prélèvement N° {prelevement.id}) - N° D'Échantillon"

    expect(page.get_by_text(creation_text, exact=True)).to_be_visible()
    expect(page.get_by_text(update_text, exact=True)).to_be_visible()


def test_evenement_history_content_add_and_edit_zone_infestee(
    live_server, page, form_elements: FicheDetectionFormDomElements, lieu_form_elements, choice_js_fill
):
    statut, _ = StatutReglementaire.objects.get_or_create(libelle="organisme quarantaine prioritaire")
    organisme_nuisible = OrganismeNuisibleFactory()
    page.goto(f"{live_server.url}{reverse('sv:fiche-detection-creation')}")
    choice_js_fill(
        page,
        "#organisme-nuisible .choices__list--single",
        organisme_nuisible.libelle_court,
        organisme_nuisible.libelle_court,
    )
    page.get_by_label("Statut réglementaire").select_option(value=str(statut.id))
    page.get_by_test_id("bottom-action-btns").get_by_role("button", name="Enregistrer").click()

    evenement = Evenement.objects.get()

    page.get_by_role("tab", name="Zone").click()
    page.get_by_role("button", name="Ajouter une zone").click()
    page.get_by_test_id("bottom-action-btns").get_by_role("button", name="Enregistrer").click()

    fiche_zone = FicheZoneDelimitee.objects.get()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    page.goto(f"{live_server.url}{fiche_zone.get_update_url()}")
    form_page.add_new_zone_infestee(ZoneInfesteeFactory.build(nom="Old value"), ())
    form_page.submit_update_form()

    form_page.page.goto(f"{live_server.url}{fiche_zone.get_update_url()}")
    form_page.page.locator("#id_zones_infestees-0-nom").fill("New value")
    form_page.submit_update_form()

    content_type = ContentType.objects.get_for_model(Evenement)
    url = reverse("revision-list", kwargs={"content_type": content_type.pk, "pk": evenement.pk})
    page.goto(f"{live_server.url}{url}")

    creation_text = "Objet ajouté : FicheZoneDelimitee"
    update_text = f"Fiche Zone Délimitée ({evenement.numero}) - Zone Infestée (Old Value) - Nom De La Zone Infestée"
    expect(page.get_by_text(creation_text, exact=True)).to_be_visible()
    expect(page.get_by_text(update_text, exact=True)).to_be_visible()
