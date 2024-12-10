import pytest
from playwright.sync_api import Page, expect
from model_bakery import baker
from django.utils import timezone
from django.urls import reverse

from core.models import Visibilite, LienLibre
from sv.models import FicheZoneDelimitee, ZoneInfestee, FicheDetection, Etat, OrganismeNuisible, StatutReglementaire
from sv.tests.test_utils import FicheZoneDelimiteeFormPage
from sv.forms import RattachementChoices


@pytest.mark.django_db
def test_cant_create_fiche_zone_delimitee_when_organisme_nuisible_of_fiche_detection_is_none(
    live_server, page: Page, fiche_detection: FicheDetection
):
    fiche_detection.organisme_nuisible = None
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Ajouter une zone").click()
    expect(page.get_by_role("heading", name="Création d'une fiche zone")).to_be_visible()
    expect(
        page.get_by_text(
            "L'organisme nuisible et le statut réglementaire doivent être complétés avant de pouvoir créer une fiche de zone délimitée."
        )
    ).to_be_visible()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


def test_cant_create_fiche_zone_delimitee_when_statut_reglementaire_of_fiche_detection_is_none(
    live_server, page: Page, fiche_detection: FicheDetection
):
    fiche_detection.statut_reglementaire = None
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Ajouter une zone").click()
    expect(page.get_by_role("heading", name="Création d'une fiche zone")).to_be_visible()
    expect(
        page.get_by_text(
            "L'organisme nuisible et le statut réglementaire doivent être complétés avant de pouvoir créer une fiche de zone délimitée."
        )
    ).to_be_visible()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


def test_organisme_nuisible_and_statut_reglementaire_are_autoselect_and_readonly_on_fiche_zone_delimitee_form(
    live_server, page: Page, fiche_detection: FicheDetection, choice_js_fill
):
    """Test que l'organisme nuisible et le statut réglementaire de la fiche de détection sont automatiquement renseignés et désactivés (non modifiables)
    sur le formulaire de création de fiche zone délimitée"""
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.organisme_nuisible_is_autoselect(str(fiche_detection.organisme_nuisible))
    form_page.statut_reglementaire_is_autoselect(str(fiche_detection.statut_reglementaire))
    form_page.organisme_nuisible_is_readonly()
    form_page.statut_reglementaire_is_readonly()


def test_fiche_detection_is_add_in_hors_zone_infestee_field(
    live_server, page: Page, fiche_detection: FicheDetection, choice_js_fill
):
    """Test que la fiche détection est ajouté dans le bloc détections hors zone infestée lors de la création d'une fiche zone délimitée"""
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.check_detections_in_hors_zone_infestee([fiche_detection])


def test_fiche_detection_is_add_in_zone_infestee_field(
    live_server, page: Page, fiche_detection: FicheDetection, choice_js_fill
):
    """Test que la fiche détection est ajouté dans le bloc zones infestées lors de la création d'une fiche zone délimitée"""
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.ZONE_INFESTEE)
    form_page._check_detections_in_zone_infestee([fiche_detection], 0)


@pytest.mark.django_db
def test_fiche_detection_are_filtered_by_organisme_nuisible_of_fiche_detection(client):
    """Test que les fiches détection proposées dans la page de création de la fiche zone délimitée
    ont le même organisme nuisible que la fiche de détection par laquelle on est passé pour créer la fiche zone délimitée"""
    on1, on2 = baker.make("OrganismeNuisible", _quantity=2)
    statut_reglementaire = baker.make("StatutReglementaire")
    fiches_with_on1 = baker.make(
        FicheDetection,
        organisme_nuisible=on1,
        statut_reglementaire=statut_reglementaire,
        _quantity=3,
        visibilite=Visibilite.LOCAL,
    )
    fiches_with_on2 = baker.make(
        FicheDetection,
        organisme_nuisible=on2,
        statut_reglementaire=statut_reglementaire,
        _quantity=3,
        visibilite=Visibilite.LOCAL,
    )

    url = f"{reverse('fiche-zone-delimitee-creation')}?fiche_detection_id={fiches_with_on1[0].pk}&rattachement={RattachementChoices.HORS_ZONE_INFESTEE}"
    response = client.get(url)
    context = response.context
    form = context["form"]
    queryset = form.fields["detections_hors_zone"].queryset

    assert not any(fiche in queryset for fiche in fiches_with_on2)
    assert all(fiche in queryset for fiche in fiches_with_on1)


@pytest.mark.django_db
def test_can_create_fiche_zone_delimitee_without_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    fiche_detection.organisme_nuisible = baker.make("OrganismeNuisible")
    fiche_detection.statut_reglementaire = baker.make("StatutReglementaire")
    fiche_detection.save()
    fiche = baker.prepare(
        FicheZoneDelimitee,
        _fill_optional=True,
        etat=Etat.objects.get(id=Etat.get_etat_initial()),
        rayon_zone_tampon=10,
        surface_tampon_totale=15,
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.fill_form(fiche)
    form_page.publish()

    form_page.check_message_succes()
    assert ZoneInfestee.objects.count() == 0
    assert FicheZoneDelimitee.objects.count() == 1
    fiche_from_db = FicheZoneDelimitee.objects.get()
    assert fiche_from_db.organisme_nuisible == fiche_detection.organisme_nuisible
    assert fiche_from_db.visibilite == Visibilite.LOCAL
    assert fiche_from_db.statut_reglementaire == fiche_detection.statut_reglementaire
    assert fiche_from_db.date_creation.date() == timezone.now().date()
    assert fiche_from_db.commentaire == fiche.commentaire
    assert fiche_from_db.rayon_zone_tampon == fiche.rayon_zone_tampon
    assert fiche_from_db.unite_rayon_zone_tampon == fiche.unite_rayon_zone_tampon
    assert fiche_from_db.surface_tampon_totale == fiche.surface_tampon_totale
    assert fiche_from_db.unite_surface_tampon_totale == fiche.unite_surface_tampon_totale
    # Vérification de la détection liée dans hors zone infestée
    fiches_detection_linked = fiche_from_db.fichedetection_set.all()
    assert fiche_detection in fiches_detection_linked


@pytest.mark.django_db
def test_can_create_fiche_zone_delimitee_in_draft(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    fiche_detection.organisme_nuisible = baker.make("OrganismeNuisible")
    fiche_detection.statut_reglementaire = baker.make("StatutReglementaire")
    fiche_detection.save()
    fiche = baker.prepare(FicheZoneDelimitee, etat=Etat.objects.get(id=Etat.get_etat_initial()))
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.fill_form(fiche)
    page.get_by_role("button", name="Enregistrer le brouillon", exact=True).click()

    form_page.check_message_succes()
    assert FicheZoneDelimitee.objects.count() == 1
    fiche_from_db = FicheZoneDelimitee.objects.get()
    assert fiche_from_db.visibilite == Visibilite.BROUILLON


@pytest.mark.django_db
def test_fiche_zone_delimitee_numero_is_null_when_save_with_visibilite_brouillon(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    fiche_detection.organisme_nuisible = baker.make("OrganismeNuisible")
    fiche_detection.statut_reglementaire = baker.make("StatutReglementaire")
    fiche_detection.save()
    fiche = baker.prepare(FicheZoneDelimitee, etat=Etat.objects.get(id=Etat.get_etat_initial()))
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.fill_form(fiche)
    page.get_by_role("button", name="Enregistrer le brouillon", exact=True).click()

    form_page.check_message_succes()
    assert FicheZoneDelimitee.objects.count() == 1
    fiche_from_db = FicheZoneDelimitee.objects.get()
    assert fiche_from_db.visibilite == Visibilite.BROUILLON
    assert fiche_from_db.numero is None


@pytest.mark.django_db
def test_can_create_fiche_zone_delimitee_with_2_zones_infestees(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    detections_hors_zone_infestee, detections_zone_infestee1, detections_zone_infestee2 = (
        baker.make(
            FicheDetection,
            organisme_nuisible=fiche_detection.organisme_nuisible,
            visibilite=Visibilite.LOCAL,
            _quantity=2,
        )
        for _ in range(3)
    )
    fiche = baker.prepare(
        FicheZoneDelimitee,
        _fill_optional=True,
        etat=Etat.objects.get(id=Etat.get_etat_initial()),
        rayon_zone_tampon=10,
        surface_tampon_totale=15,
    )
    zone_infestee1, zone_infestee2 = baker.prepare(
        ZoneInfestee, fiche_zone_delimitee=fiche, _fill_optional=True, _quantity=2, surface_infestee_totale=10, rayon=15
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.fill_form(fiche, zone_infestee1, detections_hors_zone_infestee, detections_zone_infestee1)
    form_page.add_new_zone_infestee(zone_infestee2, detections_zone_infestee2)
    form_page.publish()

    form_page.check_message_succes()
    # Vérification des attributs de FicheZoneDelimitee
    assert FicheZoneDelimitee.objects.count() == 1
    fiche_from_db = FicheZoneDelimitee.objects.get()
    assert fiche_from_db.organisme_nuisible == fiche_detection.organisme_nuisible
    assert fiche_from_db.statut_reglementaire == fiche_detection.statut_reglementaire
    assert fiche_from_db.date_creation.date() == timezone.now().date()
    assert fiche_from_db.commentaire == fiche.commentaire
    assert fiche_from_db.rayon_zone_tampon == fiche.rayon_zone_tampon
    assert fiche_from_db.unite_rayon_zone_tampon == fiche.unite_rayon_zone_tampon
    assert fiche_from_db.surface_tampon_totale == fiche.surface_tampon_totale
    assert fiche_from_db.unite_surface_tampon_totale == fiche.unite_surface_tampon_totale

    # Vérification des détections hors zone infestée
    detections_hors_zone_infestee.append(fiche_detection)
    assert all(detection in detections_hors_zone_infestee for detection in fiche_from_db.fichedetection_set.all())

    # Vérification des zones infestées
    zones_infestees_from_db = fiche_from_db.zoneinfestee_set.all()
    assert zones_infestees_from_db.count() == 2
    for zone_infestee, detections_zone_infestee, zone_infestee_from_db in zip(
        [zone_infestee1, zone_infestee2],
        [detections_zone_infestee1, detections_zone_infestee2],
        zones_infestees_from_db,
    ):
        assert zone_infestee_from_db.nom == zone_infestee.nom
        assert zone_infestee_from_db.caracteristique_principale == zone_infestee.caracteristique_principale
        assert zone_infestee_from_db.surface_infestee_totale == zone_infestee.surface_infestee_totale
        assert zone_infestee_from_db.unite_surface_infestee_totale == zone_infestee.unite_surface_infestee_totale
        assert all(
            detection in detections_zone_infestee for detection in zone_infestee_from_db.fichedetection_set.all()
        )


def test_cant_have_same_detection_in_hors_zone_infestee_and_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
) -> None:
    fiche_zone_delimitee = baker.prepare(FicheZoneDelimitee, etat=Etat.objects.get(id=Etat.get_etat_initial()))
    zone_infestee = baker.prepare(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.fill_form(fiche_zone_delimitee, zone_infestee, (), (fiche_detection,))
    form_page.publish()

    expect(
        page.get_by_text(
            f"La fiche détection {str(fiche_detection.numero)} ne peut pas être sélectionnée à la fois dans les zones infestées et dans hors zone infestée."
        )
    ).to_be_visible()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


def test_cant_have_same_detection_in_zone_infestee_forms(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    fiche_zone_delimitee = baker.prepare(FicheZoneDelimitee, etat=Etat.objects.get(id=Etat.get_etat_initial()))
    zone_infestee1, zone_infestee2 = baker.prepare(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee, _quantity=2)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.fill_form(fiche_zone_delimitee, zone_infestee1, (), (fiche_detection,))
    form_page.add_new_zone_infestee(zone_infestee2, (fiche_detection,))
    form_page.publish()

    expect(page.get_by_text("Erreurs dans le(s) formulaire(s) Zones infestées")).to_be_visible()
    expect(
        page.get_by_text(
            f"Les fiches détection suivantes sont dupliquées dans les zones infestées : {str(fiche_detection.numero)}."
        )
    ).to_be_visible()
    assert FicheZoneDelimitee.objects.count() == 0
    assert ZoneInfestee.objects.count() == 0


@pytest.mark.django_db
def test_cant_see_add_zone_link_when_fiche_detection_is_already_linked(
    live_server, page: Page, fiche_detection: FicheDetection
):
    """Test qu'une fiche détection déjà rattachée à une fiche zone délimitée ne permet pas de voir le lien dans le menu Action
    pour accéder au formulaire de création d'une fiche zone délimitée"""
    fiche_zone_delimitee = baker.make(FicheZoneDelimitee)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("button", name="Ajouter une zone")).to_be_disabled()


@pytest.mark.django_db
def test_cant_access_create_fiche_zone_delimitee_form_when_fiche_detection_is_already_linked(
    live_server, page: Page, fiche_detection: FicheDetection
):
    """Test que l'accès direct au formulaire de création (via l'URL) d'une fiche zone délimitée avec une fiche détection déjà rattachée affiche un message d'erreur"""
    fiche_zone_delimitee = baker.make(FicheZoneDelimitee)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()
    page.goto(f"{live_server.url}{reverse('fiche-zone-delimitee-creation')}?fiche_detection_id={fiche_detection.pk}")
    expect(page.get_by_text("La fiche de détection est déjà rattachée à une fiche zone délimitée.")).to_be_visible()


def test_cant_link_fiche_detection_to_fiche_zone_delimitee_if_fiche_detection_is_already_linked(
    live_server, page: Page, fiche_detection: FicheDetection, choice_js_fill
):
    """Test qu'une fiche détection déjà rattachée à une fiche zone délimitée ne permet pas d'être liée à une autre fiche zone délimitée.
    Je ne dois pas voir la fiche détection dans la liste des détections hors zone infestée ou zone infestée dans le formulaire de création d'une fiche zone délimitée"""
    fiche_zone_delimitee = baker.make(FicheZoneDelimitee)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()
    fiche_detection2 = baker.make(
        FicheDetection,
        organisme_nuisible=fiche_detection.organisme_nuisible,
        statut_reglementaire=fiche_detection.statut_reglementaire,
        visibilite=Visibilite.LOCAL,
    )
    zone_infestee = baker.make(ZoneInfestee, _fill_optional=True)
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection2.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.fill_form(
        baker.prepare(FicheZoneDelimitee, _fill_optional=True, etat=Etat.objects.get(id=Etat.get_etat_initial())),
        zone_infestee,
        (),
        (fiche_detection2,),
    )
    form_page.add_new_zone_infestee(zone_infestee, (fiche_detection2,))
    page.locator(".choices > div").first.click()
    expect(page.get_by_role("listbox").get_by_text("Aucune fiche détection à sélectionner")).to_be_visible()
    page.get_by_text("Rattacher des détections").nth(1).click()
    expect(page.get_by_text("Aucune fiche détection à sélectionner").nth(1)).to_be_visible()
    page.get_by_text("Rattacher des détections").nth(2).click()
    expect(page.get_by_text("Aucune fiche détection à sélectionner").nth(2)).to_be_visible()


@pytest.mark.django_db
def test_can_create_fiche_zone_with_free_links(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection, fiche_zone_bakery
):
    other_fiche = fiche_zone_bakery()
    other_fiche.visibilite = Visibilite.NATIONAL
    other_fiche.save()
    fiche_detection.organisme_nuisible = baker.make("OrganismeNuisible")
    fiche_detection.statut_reglementaire = baker.make("StatutReglementaire")
    fiche_detection.save()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    fiche_input = "Fiche zone délimitée : " + str(other_fiche.numero)
    choice_js_fill(page, "#liens-libre .choices", str(other_fiche.numero), fiche_input)
    form_page.publish()

    form_page.check_message_succes()
    assert FicheZoneDelimitee.objects.count() == 2
    fiche_from_db = FicheZoneDelimitee.objects.last()

    assert LienLibre.objects.count() == 1
    lien_libre = LienLibre.objects.get()

    assert lien_libre.related_object_1 == fiche_from_db
    assert lien_libre.related_object_2 == other_fiche


def test_cant_add_fiche_detection_brouillon_in_hors_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    FicheDetection.objects.create(
        visibilite=Visibilite.BROUILLON,
        createur=fiche_detection.createur,
        organisme_nuisible=fiche_detection.organisme_nuisible,
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.ZONE_INFESTEE)
    select_options = page.locator(
        ".fichezoneform__detections-hors-zone-infestee .choices__list--dropdown .choices__item"
    )
    expect(select_options).to_have_count(1)
    expect(select_options).to_have_text(str(fiche_detection.numero))


def test_cant_add_fiche_detection_brouillon_in_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    FicheDetection.objects.create(
        visibilite=Visibilite.BROUILLON,
        createur=fiche_detection.createur,
        organisme_nuisible=fiche_detection.organisme_nuisible,
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    select_options = (
        page.locator(".zone-infestees__zone-infestee-form").nth(0).locator(".choices__list--dropdown .choices__item")
    )
    expect(select_options).to_have_count(1)
    expect(select_options).to_have_text(str(fiche_detection.numero))


def test_free_links_are_ordered_in_form(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection, fiche_detection_bakery
):
    for i in range(1, 3):
        other_fiche = fiche_detection_bakery()
        other_fiche.visibilite = Visibilite.NATIONAL
        other_fiche.save()
        numero = other_fiche.numero
        numero.annee = 2024
        numero.numero = 3 - i
        numero.save()

    fiche_detection.organisme_nuisible = baker.make("OrganismeNuisible")
    fiche_detection.statut_reglementaire = baker.make("StatutReglementaire")
    fiche_detection.save()
    numero = fiche_detection.numero
    numero.annee = 2000
    numero.numero = 1
    numero.save()
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)

    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    page.query_selector("#liens-libre .choices").click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill("Fiche Détection")
    expect(page.locator("#liens-libre .choices .choices__item--selectable:nth-of-type(1)")).to_contain_text(
        "Fiche Détection : 2024.2"
    )
    expect(page.locator("#liens-libre .choices .choices__item--selectable:nth-of-type(2)")).to_contain_text(
        "Fiche Détection : 2024.1"
    )


@pytest.mark.django_db
def test_cant_see_fiches_brouillon_in_liens_libres(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    FicheDetection.objects.create(visibilite=Visibilite.BROUILLON, createur=fiche_detection.createur)
    FicheZoneDelimitee.objects.create(
        visibilite=Visibilite.BROUILLON,
        createur=fiche_detection.createur,
        organisme_nuisible=baker.make(OrganismeNuisible),
        statut_reglementaire=baker.make(StatutReglementaire),
    )
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    select_options = page.locator("#liens-libre .choices__list--dropdown .choices__item")
    expect(select_options).to_have_count(1)
    expect(select_options).to_have_text(f"Fiche Détection : {str(fiche_detection.numero)}")


@pytest.mark.django_db
def test_can_publish_fiche_zone_delimitee(live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection):
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    form_page.publish()
    fiche_zone = FicheZoneDelimitee.objects.get()
    assert fiche_zone.visibilite == Visibilite.LOCAL


def test_cant_fill_negative_value_for_surface_and_rayon(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.ZONE_INFESTEE)
    assert form_page.rayon_zone_tampon.get_attribute("min") == "0"
    assert form_page.surface_tampon_totale.get_attribute("min") == "0"
    assert (
        form_page.page.locator(form_page.zone_infestee_surface_infestee_totale_base_locator.format(0)).get_attribute(
            "min"
        )
        == "0"
    )
    assert (
        form_page.page.locator(form_page.zone_infestee_surface_infestee_totale_base_locator.format(0)).get_attribute(
            "min"
        )
        == "0"
    )


def test_has_same_surface_units_order_for_zone_tampon_and_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    assert form_page.has_same_surface_units_order_for_zone_tampon_and_zone_infestee() is True


def test_has_same_rayon_units_order_for_zone_tampon_and_zone_infestee(
    live_server, page: Page, choice_js_fill, fiche_detection: FicheDetection
):
    form_page = FicheZoneDelimiteeFormPage(page, choice_js_fill)
    form_page.goto_create_form_page(live_server, fiche_detection.pk, RattachementChoices.HORS_ZONE_INFESTEE)
    assert form_page.has_same_rayon_units_order_for_zone_tampon_and_zone_infestee() is True
