from model_bakery import baker
from playwright.sync_api import expect

from sv.factories import LieuFactory, EvenementFactory, FicheDetectionFactory, PrelevementFactory
from sv.models import Lieu, Prelevement


def test_lieu_details(live_server, page, fiche_detection):
    "Test que les détails d'un lieu s'affichent correctement dans la modale"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection, _fill_optional=True, is_etablissement=True)
    evenement = fiche_detection.evenement
    evenement.createur = fiche_detection.createur
    evenement.save()
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
    evenement = fiche_detection.evenement
    evenement.createur = fiche_detection.createur
    evenement.save()
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
    evenement = fiche_detection.evenement
    evenement.createur = fiche_detection.createur
    evenement.save()
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
    evenement = fiche_detection.evenement
    evenement.createur = fiche_detection.createur
    evenement.save()
    prelevement = baker.make(
        Prelevement, lieu=lieu, is_officiel=False, numero_echantillon="12345", resultat=Prelevement.Resultat.DETECTE
    )
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    expect(page.locator(".prelevement").get_by_text(prelevement.numero_echantillon)).to_be_visible()
    expect(page.locator(".prelevement").get_by_text(prelevement.lieu.nom)).to_be_visible()
    expect(page.locator(".prelevement").get_by_text(prelevement.get_resultat_display())).to_be_visible()
    expect(page.locator(".prelevement").get_by_text("Prélèvement non officiel")).to_be_visible()


def test_prelevement_non_officiel_details_with_no_data(live_server, page, fiche_detection):
    "Test que les détails d'un prélèvement non officiel s'affichent correctement dans la modale lorsqu'il n'y a pas de données (sauf pour les champs obligatoires)"
    lieu = baker.make(Lieu, fiche_detection=fiche_detection)
    evenement = fiche_detection.evenement
    evenement.createur = fiche_detection.createur
    evenement.save()
    prelevement = baker.make(Prelevement, lieu=lieu)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du prélèvement {prelevement.numero_echantillon}").click()
    expect(page.get_by_test_id("prelevement-1-is-officiel")).to_contain_text(
        "oui" if prelevement.is_officiel else "non"
    )
    expect(page.get_by_test_id("prelevement-1-structure-preleveuse")).to_contain_text(
        prelevement.structure_preleveuse.nom
    )
    expect(page.get_by_test_id("prelevement-1-numero-echantillon")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-date-prelevement")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-matrice-prelevee")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-espece-echantillon")).to_contain_text("nc.")
    expect(page.get_by_test_id("prelevement-1-code-oepp")).to_contain_text("nc.")


def test_prelevement_non_officiel_details_second_prelevement(live_server, page):
    "Test que si je clique sur le bouton 'Consulter le détail du prélèvement' d'un deuxième prélèvement, les détails de ce prélèvement s'affichent correctement dans la modale"
    fiche_detection = FicheDetectionFactory()
    lieu = LieuFactory(fiche_detection=fiche_detection)
    evenement = fiche_detection.evenement
    evenement.createur = fiche_detection.createur
    evenement.save()
    PrelevementFactory(lieu=lieu, is_officiel=False)
    prelevement2 = PrelevementFactory(lieu=lieu, is_officiel=False)

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du prélèvement {prelevement2.numero_echantillon}").click()

    expect(page.get_by_role("heading", name=f"Échantillon {prelevement2.numero_echantillon}")).to_be_visible()
    expect(page.get_by_test_id("prelevement-2-type-analyse")).to_contain_text(prelevement2.get_type_analyse_display())
    expect(page.get_by_test_id("prelevement-2-is-officiel")).to_contain_text("non")
    expect(page.get_by_test_id("prelevement-2-numero-rapport-inspection")).to_contain_text(
        prelevement2.numero_rapport_inspection
    )
    expect(page.get_by_test_id("prelevement-2-laboratoire")).to_contain_text(prelevement2.laboratoire.nom)
    expect(page.get_by_test_id("prelevement-2-numero-echantillon")).to_contain_text(prelevement2.numero_echantillon)
    expect(page.get_by_test_id("prelevement-2-lieu")).to_contain_text(prelevement2.lieu.nom)
    expect(page.get_by_test_id("prelevement-2-structure-preleveuse")).to_contain_text(
        prelevement2.structure_preleveuse.nom
    )
    expect(page.get_by_test_id("prelevement-2-date-prelevement")).to_contain_text(
        prelevement2.date_prelevement.strftime("%d/%m/%Y")
    )
    expect(page.get_by_test_id("prelevement-2-matrice-prelevee")).to_contain_text(prelevement2.matrice_prelevee.libelle)
    expect(page.get_by_test_id("prelevement-2-espece-echantillon")).to_contain_text(
        prelevement2.espece_echantillon.libelle
    )
    expect(page.get_by_test_id("prelevement-2-code-oepp")).to_contain_text(prelevement2.espece_echantillon.code_oepp)
    expect(page.get_by_test_id("prelevement-2-resultat")).to_contain_text(prelevement2.get_resultat_display())


def test_prelevement_details(live_server, page):
    "Test que les détails d'un prélèvement s'affichent correctement dans la modale"
    evenement = EvenementFactory()
    fiche_detection = FicheDetectionFactory(evenement=evenement)
    lieu = LieuFactory(fiche_detection=fiche_detection)
    prelevement = PrelevementFactory(lieu=lieu)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name=f"Consulter le détail du prélèvement {prelevement.numero_echantillon}").click()
    expect(page.get_by_test_id("prelevement-1-type-analyse")).to_contain_text(prelevement.get_type_analyse_display())
    expect(page.get_by_test_id("prelevement-1-is-officiel")).to_contain_text(
        "oui" if prelevement.is_officiel else "non"
    )
    expect(page.get_by_test_id("prelevement-1-numero-rapport-inspection")).to_contain_text(
        prelevement.numero_rapport_inspection
    )
    expect(page.get_by_test_id("prelevement-1-laboratoire")).to_contain_text(prelevement.laboratoire.nom)
    expect(page.get_by_test_id("prelevement-1-numero-echantillon")).to_contain_text(prelevement.numero_echantillon)
    expect(page.get_by_test_id("prelevement-1-lieu")).to_contain_text(prelevement.lieu.nom)
    expect(page.get_by_test_id("prelevement-1-structure-preleveuse")).to_contain_text(
        prelevement.structure_preleveuse.nom
    )
    expect(page.get_by_test_id("prelevement-1-date-prelevement")).to_contain_text(
        prelevement.date_prelevement.strftime("%d/%m/%Y")
    )
    expect(page.get_by_test_id("prelevement-1-matrice-prelevee")).to_contain_text(prelevement.matrice_prelevee.libelle)
    expect(page.get_by_test_id("prelevement-1-espece-echantillon")).to_contain_text(
        prelevement.espece_echantillon.libelle
    )
    expect(page.get_by_test_id("prelevement-1-code-oepp")).to_contain_text(prelevement.espece_echantillon.code_oepp)
    expect(page.get_by_test_id("prelevement-1-resultat")).to_contain_text(prelevement.get_resultat_display())
