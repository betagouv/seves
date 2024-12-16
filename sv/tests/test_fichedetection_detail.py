from django.urls import reverse
from core.models import Visibilite
from sv.factories import FicheDetectionFactory, LieuFactory
from sv.models import Lieu, Prelevement, FicheZoneDelimitee, ZoneInfestee, FicheDetection
from model_bakery import baker
from playwright.sync_api import expect, Page


def test_lieu_details(live_server, page, fiche_detection):
    "Test que les détails d'un lieu s'affichent correctement dans la modale"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True, is_etablissement=True)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du lieu {lieu.nom}").click()
    expect(page.get_by_role("heading", name=lieu.nom)).to_be_visible()
    expect(page.locator("#fr-modal-lieu-1").get_by_text("Adresse ou lieu-dit")).to_be_visible()
    expect(page.locator("#fr-modal-lieu-1").get_by_text("Commune")).to_be_visible()
    expect(page.locator("#fr-modal-lieu-1").get_by_text("Code INSEE")).to_be_visible()
    expect(page.locator("#fr-modal-lieu-1").get_by_text("Département")).to_be_visible()
    expect(page.locator("#fr-modal-lieu-1").get_by_text("Région")).to_be_visible()
    expect(page.locator("#fr-modal-lieu-1").get_by_text("Coord. WGS84")).to_be_visible()
    expect(page.get_by_test_id("lieu-1-adresse")).to_contain_text(lieu.adresse_lieu_dit)
    expect(page.get_by_test_id("lieu-1-commune")).to_contain_text(lieu.commune)
    expect(page.get_by_test_id("lieu-1-code-insee")).to_contain_text(lieu.code_insee)
    expect(page.get_by_test_id("lieu-1-departement")).to_contain_text(lieu.departement.nom)
    expect(page.get_by_test_id("lieu-1-region")).to_contain_text(lieu.departement.region.nom)
    expect(page.get_by_test_id("lieu-1-wgs84-latitude")).to_contain_text(str(lieu.wgs84_latitude).replace(".", ","))
    expect(page.get_by_test_id("lieu-1-wgs84-longitude")).to_contain_text(str(lieu.wgs84_longitude).replace(".", ","))
    expect(page.get_by_text("Il s'agit d'un établissement", exact=True)).to_be_visible()
    expect(page.get_by_test_id("lieu-1-nom-etablissement")).to_contain_text(lieu.nom_etablissement)
    expect(page.get_by_test_id("lieu-1-activite-etablissement")).to_contain_text(lieu.activite_etablissement)
    expect(page.get_by_test_id("lieu-1-pays-etablissement")).to_contain_text(lieu.pays_etablissement)
    expect(page.get_by_test_id("lieu-1-raison-sociale-etablissement")).to_contain_text(
        lieu.raison_sociale_etablissement
    )
    expect(page.get_by_test_id("lieu-1-adresse-etablissement")).to_contain_text(lieu.adresse_etablissement)
    expect(page.get_by_test_id("lieu-1-siret-etablissement")).to_contain_text(lieu.siret_etablissement)
    expect(page.get_by_test_id("lieu-1-code-inupp-etablissement")).to_contain_text(lieu.code_inupp_etablissement)
    expect(page.get_by_test_id("lieu-1-position-etablissement")).to_contain_text(
        lieu.position_chaine_distribution_etablissement.libelle
    )


def test_lieu_details_second_lieu(live_server, page, fiche_detection):
    "Test que si je clique sur le bouton 'Consulter le détail du lieu' d'un deuxième lieu, les détails de ce lieu s'affichent correctement dans la modale"
    baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True)
    lieu2 = baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du lieu {lieu2.nom}").click()
    expect(page.get_by_role("heading", name=lieu2.nom)).to_be_visible()
    expect(page.get_by_test_id("lieu-2-adresse")).to_contain_text(lieu2.adresse_lieu_dit)
    expect(page.get_by_test_id("lieu-2-commune")).to_contain_text(lieu2.commune)
    expect(page.get_by_test_id("lieu-2-code-insee")).to_contain_text(lieu2.code_insee)
    expect(page.get_by_test_id("lieu-2-departement")).to_contain_text(lieu2.departement.nom)
    expect(page.get_by_test_id("lieu-2-region")).to_contain_text(lieu2.departement.region.nom)
    expect(page.get_by_test_id("lieu-2-wgs84-latitude")).to_contain_text(str(lieu2.wgs84_latitude).replace(".", ","))
    expect(page.get_by_test_id("lieu-2-wgs84-longitude")).to_contain_text(str(lieu2.wgs84_longitude).replace(".", ","))


def test_lieu_details_with_no_data(live_server, page, fiche_detection):
    "Test que les détails d'un lieu s'affichent correctement dans la modale lorsqu'il n'y a pas de données (sauf pour les champs obligatoires)"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du lieu {lieu.nom}").click()
    expect(page.get_by_test_id("lieu-1-adresse")).to_contain_text("nc.")
    expect(page.get_by_test_id("lieu-1-commune")).to_contain_text(lieu.commune)
    expect(page.get_by_test_id("lieu-1-code-insee")).to_contain_text("nc.")
    expect(page.get_by_test_id("lieu-1-departement")).to_contain_text("nc.")
    expect(page.get_by_test_id("lieu-1-region")).to_contain_text("nc.")
    expect(page.get_by_test_id("lieu-1-wgs84")).to_contain_text("nc.")
    expect(page.get_by_test_id("lieu-1-wgs84")).to_contain_text("nc.")


def test_prelevement_card(live_server, page, fiche_detection):
    lieu = baker.make(Lieu, fiche_detection=fiche_detection)
    prelevement = baker.make(
        Prelevement, lieu=lieu, is_officiel=False, numero_echantillon="12345", resultat=Prelevement.Resultat.DETECTE
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    expect(page.locator(".prelevement").get_by_text(prelevement.numero_echantillon)).to_be_visible()
    expect(page.locator(".prelevement").get_by_text(prelevement.lieu.nom)).to_be_visible()
    expect(page.locator(".prelevement").get_by_text(prelevement.get_resultat_display())).to_be_visible()
    expect(page.locator(".prelevement").get_by_text("Prélèvement non officiel")).to_be_visible()


def test_prelevement_non_officiel_details(live_server, page, fiche_detection):
    "Test que les détails d'un prélèvement non officiel s'affichent correctement dans la modale"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection)
    prelevement = baker.make(
        Prelevement,
        lieu=lieu,
        is_officiel=False,
        numero_rapport_inspection="",
        laboratoire=None,
        _fill_optional=True,
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du prélèvement {prelevement.numero_echantillon}").click()
    expect(page.get_by_role("heading", name=f"Échantillon {prelevement.numero_echantillon}")).to_be_visible()
    expect(page.locator("#fr-modal-prelevement-1").get_by_text("Type de prélèvement")).to_be_visible()
    expect(page.locator("#fr-modal-prelevement-1").get_by_text("Structure")).to_be_visible()
    expect(page.locator("#fr-modal-prelevement-1").get_by_text("Numéro d'échantillon")).to_be_visible()
    expect(page.locator("#fr-modal-prelevement-1").get_by_text("Date de prélèvement")).to_be_visible()
    expect(page.locator("#fr-modal-prelevement-1").get_by_text("Matrice prélevée")).to_be_visible()
    expect(page.locator("#fr-modal-prelevement-1").get_by_text("Espèce de l'échantillon")).to_be_visible()
    expect(page.locator("#fr-modal-prelevement-1").get_by_text("Code OEPP")).to_be_visible()
    expect(page.get_by_test_id("prelevement-1-type")).to_contain_text("Prélèvement non officiel")
    expect(page.get_by_test_id("prelevement-1-structure-preleveuse")).to_contain_text(
        prelevement.structure_preleveuse.nom
    )
    expect(page.get_by_test_id("prelevement-1-numero-echantillon")).to_contain_text(prelevement.numero_echantillon)
    expect(page.get_by_test_id("prelevement-1-date-prelevement")).to_contain_text(
        prelevement.date_prelevement.strftime("%d/%m/%Y")
    )
    expect(page.get_by_test_id("prelevement-1-matrice-prelevee")).to_contain_text(prelevement.matrice_prelevee.libelle)
    expect(page.get_by_test_id("prelevement-1-espece-echantillon")).to_contain_text(
        prelevement.espece_echantillon.libelle
    )
    expect(page.get_by_test_id("prelevement-1-code-oepp")).to_contain_text(prelevement.espece_echantillon.code_oepp)
    expect(page.get_by_test_id("prelevement-1-resultat")).to_contain_text(prelevement.get_resultat_display())
    expect(page.get_by_test_id("prelevement-1-type-analyse")).to_contain_text(prelevement.get_type_analyse_display())


def test_prelevement_non_officiel_details_with_no_data(live_server, page, fiche_detection):
    "Test que les détails d'un prélèvement non officiel s'affichent correctement dans la modale lorsqu'il n'y a pas de données (sauf pour les champs obligatoires)"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection)
    prelevement = baker.make(Prelevement, lieu=lieu)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du prélèvement {prelevement.numero_echantillon}").click()
    expect(page.get_by_test_id("prelevement-1-type")).to_contain_text("Prélèvement non officiel")
    expect(page.get_by_test_id("prelevement-1-structure-preleveuse")).to_contain_text(
        prelevement.structure_preleveuse.nom
    )
    expect(page.get_by_test_id("prelevement-1-numero-echantillon")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-date-prelevement")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-matrice-prelevee")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-espece-echantillon")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-code-oepp")).to_contain_text("nc.")


def test_prelevement_non_officiel_details_second_prelevement(live_server, page, fiche_detection):
    "Test que si je clique sur le bouton 'Consulter le détail du prélèvement' d'un deuxième prélèvement, les détails de ce prélèvement s'affichent correctement dans la modale"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection)
    baker.make(
        Prelevement,
        lieu=lieu,
        is_officiel=False,
        _fill_optional=True,
        numero_rapport_inspection="",
        laboratoire=None,
    )
    prelevement2 = baker.make(
        Prelevement,
        lieu=lieu,
        is_officiel=False,
        _fill_optional=True,
        numero_rapport_inspection="",
        laboratoire=None,
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du prélèvement {prelevement2.numero_echantillon}").click()
    expect(page.get_by_role("heading", name=f"Échantillon {prelevement2.numero_echantillon}")).to_be_visible()
    expect(page.get_by_test_id("prelevement-2-type")).to_contain_text("Prélèvement non officiel")
    expect(page.get_by_test_id("prelevement-2-structure-preleveuse")).to_contain_text(
        prelevement2.structure_preleveuse.nom
    )
    expect(page.get_by_test_id("prelevement-2-numero-echantillon")).to_contain_text(prelevement2.numero_echantillon)
    expect(page.get_by_test_id("prelevement-2-date-prelevement")).to_contain_text(
        prelevement2.date_prelevement.strftime("%d/%m/%Y")
    )
    expect(page.get_by_test_id("prelevement-2-matrice-prelevee")).to_contain_text(prelevement2.matrice_prelevee.libelle)
    expect(page.get_by_test_id("prelevement-2-espece-echantillon")).to_contain_text(
        prelevement2.espece_echantillon.libelle
    )
    expect(page.get_by_test_id("prelevement-2-code-oepp")).to_contain_text(prelevement2.espece_echantillon.code_oepp)
    expect(page.get_by_test_id("prelevement-2-resultat")).to_contain_text(prelevement2.get_resultat_display())


def test_prelevement_officiel_details(live_server, page, fiche_detection):
    "Test que les détails d'un prélèvement officiel s'affichent correctement dans la modale"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection)
    prelevement = baker.make(Prelevement, lieu=lieu, is_officiel=True, _fill_optional=True)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du prélèvement {prelevement.numero_echantillon}").click()
    expect(page.get_by_test_id("prelevement-1-type")).to_contain_text("Prélèvement officiel")
    expect(page.get_by_test_id("prelevement-1-laboratoire")).to_contain_text(prelevement.laboratoire.nom)


def test_have_link_to_fiche_zone_delimitee_if_hors_zone_infestee(live_server, page, fiche_detection):
    "Si une fiche détection est liée à une hors zone infestée d'une fiche zone délimitée, un lien vers cette fiche zone délimitée doit être présent"
    fiche_zone_delimitee = baker.make(FicheZoneDelimitee)
    fiche_detection.hors_zone_infestee = fiche_zone_delimitee
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    link = page.get_by_role("link", name=f"zone {fiche_zone_delimitee.numero}")
    expect(link).to_be_visible()
    expect(link).to_have_attribute("href", fiche_zone_delimitee.get_absolute_url())


def test_have_link_to_fiche_zone_delimitee_if_zone_infestee(live_server, page, fiche_detection):
    "Si une fiche détection est liée à une zone infestée d'une fiche zone délimitée, un lien vers cette fiche zone délimitée doit être présent"
    fiche_zone_delimitee = baker.make(FicheZoneDelimitee)
    zone_infestee = baker.make(ZoneInfestee, fiche_zone_delimitee=fiche_zone_delimitee)
    fiche_detection.zone_infestee = zone_infestee
    fiche_detection.save()
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    link = page.get_by_role("link", name=f"zone {fiche_zone_delimitee.numero}")
    expect(link).to_be_visible()
    expect(link).to_have_attribute("href", fiche_zone_delimitee.get_absolute_url())


def test_fiche_detection_brouillon_cannot_add_zone(live_server, page, mocked_authentification_user):
    fiche_detection = FicheDetection.objects.create(
        visibilite=Visibilite.BROUILLON, createur=mocked_authentification_user.agent.structure
    )

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_role("button", name="Ajouter une zone")).not_to_be_visible()

    # simule le fait d'effectuer la requete GET directement pour ajouter une zone
    page.goto(f"{live_server.url}{reverse('rattachement-fiche-zone-delimitee', args=[fiche_detection.id])}")
    expect(page.get_by_text("Action impossible car la fiche est en brouillon")).to_be_visible()


def test_synthese_shows_multiple_communes_with_tooltip(live_server, page: Page):
    """Test l'affichage du descripteur Commune avec tooltip dans la vue synthèse de la fiche détection
    lorsqu'il y a plusieurs communes renseignées dans les lieux"""
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="Marseille")

    page.goto(f"{live_server}{fiche.get_absolute_url()}")
    page.get_by_text("Synthèse").click()

    expect(page.locator("#synthese-communes-list")).to_contain_text("Paris +2")
    counter = page.locator('[aria-describedby="tooltip-additional-communes"]')
    counter.hover()
    tooltip = page.locator("#tooltip-additional-communes")
    expect(tooltip).to_be_visible()
    expect(tooltip).to_contain_text("Lyon, Marseille")


def test_synthese_single_commune(live_server, page: Page):
    """Test l'affichage du descripteur Commune dans la vue synthèse de la fiche détection
    lorsqu'il y a qu'une commune renseignée dans les lieux"""
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{fiche.get_absolute_url()}")
    page.get_by_text("Synthèse").click()

    expect(page.locator("#synthese-communes-list")).to_contain_text("Paris")
    counter = page.locator('[aria-describedby="tooltip-additional-communes"]')
    expect(counter).to_have_count(0)


def test_synthese_no_commune(live_server, page: Page):
    """Test l'affichage du descripteur Commune dans la vue synthèse de la fiche détection lorsqu'il y a aucun lieu"""
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{fiche.get_absolute_url()}")
    page.get_by_text("Synthèse").click()

    expect(page.locator("#synthese-communes-list")).to_contain_text("nc.")
    counter = page.locator('[aria-describedby="tooltip-additional-communes"]')
    expect(counter).to_have_count(0)
