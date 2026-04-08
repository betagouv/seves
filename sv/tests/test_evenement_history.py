from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from sv.factories import FicheZoneFactory, OrganismeNuisibleFactory
from sv.models import Evenement, FicheZoneDelimitee, StatutReglementaire
from sv.tests.test_utils import FicheDetectionFormDomElements, FicheZoneDelimiteeFormPage


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
    lieu_form_elements.save_btn.click()
    form_elements.save_update_btn.click()

    page.goto(f"{live_server.url}{detection.get_update_url()}")
    page.get_by_test_id("lieu-edit-btn").click()
    lieu_form_elements.nom_input.fill("Mon lieu 2")
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
