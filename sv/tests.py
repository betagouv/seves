import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright, expect
import time


from .models import (
    FicheDetection,
    OrganismeNuisible,
    NumeroFiche,
    Unite,
    Administration,
    StatutEvenement,
    StatutReglementaire,
    Contexte,
)


class HomePageTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def test_seves_in_title(self):
        page = self.browser.new_page()
        page.goto(self.live_server_url)
        self.assertIn("Sèves", page.inner_text("h1"))
        page.close()


class FicheDetectionListViewTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def test_url(self):
        page = self.browser.new_page()
        page.goto(f"{self.live_server_url}/sv/fiches-detection/")
        self.assertEqual(page.url, f"{self.live_server_url}/sv/fiches-detection/")
        page.close()

    def test_no_fiches(self):
        page = self.browser.new_page()
        page.goto(f"{self.live_server_url}/sv/fiches-detection/")
        # Liste des fiches détection en h1
        self.assertIn("Liste des fiches détection", page.inner_text("h1"))
        self.assertIn("Aucune fiche de détection", page.inner_text("body"))
        page.close()


class FicheDetectionUpdateViewTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        self.unite_mus = Unite.objects.create(nom="MUS", type=Administration.objects.create(nom="AC"))
        self.statut_evenement_enqu = StatutEvenement.objects.create(code="ENQU")
        self.organisme_nuisible_xf = OrganismeNuisible.objects.create(nom="Xylella fastidiosa", libelle_court="Xf")
        self.statut_reglementaire_ornq = StatutReglementaire.objects.create(code="ORNQ")
        self.contexte_is = Contexte.objects.create(nom="informations scientifiques")

        self.fiche_detection = FicheDetection.objects.create(
            numero=NumeroFiche.get_next_numero(),
            createur=self.unite_mus,
            numero_europhyt="1234",
            numero_rasff="54321",
            statut_evenement=self.statut_evenement_enqu,
            organisme_nuisible=self.organisme_nuisible_xf,
            statut_reglementaire=self.statut_reglementaire_ornq,
            contexte=self.contexte_is,
            date_premier_signalement="2021-01-01",
            commentaire="un commentaire",
            mesures_conservatoires_immediates="des mesures conservatoires immediates",
            mesures_consignation="des mesures de consignation",
            mesures_phytosanitaires="des mesures phytosanitaires",
            mesures_surveillance_specifique="des mesures de surveillance specifique",
        )
        self.fiche_detection.save()
        self.edit_fiche_detection_url = (
            f"{self.live_server_url}/sv/fiches-detection/{self.fiche_detection.id}/modification/"
        )

    def test_url(self):
        page = self.browser.new_page()
        page.goto(self.edit_fiche_detection_url)
        self.assertEqual(page.url, self.edit_fiche_detection_url)
        page.close()

    def test_page_title(self):
        """Test que le titre de la page est bien "Modification de la fiche détection n°2024.1"""
        page = self.browser.new_page()
        page.goto(self.edit_fiche_detection_url)
        expect(page.locator("#fiche-detection-form-header")).to_contain_text(
            "Modification de la fiche détection n°2024.1"
        )
        page.close()

    def test_fiche_detection_update_page_content(self):
        """Test que toutes les données de la fiche de détection sont affichées sur la page de modification de la fiche de détection."""
        context = self.browser.new_context()
        page = context.new_page()
        page.goto(self.edit_fiche_detection_url)
        expect(page.locator("#createur-input")).to_contain_text(self.fiche_detection.createur.nom)
        expect(page.get_by_label("Statut évènement")).to_contain_text(self.fiche_detection.statut_evenement.libelle)
        expect(page.locator("#organisme-nuisible")).to_contain_text(
            self.fiche_detection.organisme_nuisible.libelle_court
        )
        expect(page.get_by_label("Statut règlementaire")).to_contain_text(
            self.fiche_detection.statut_reglementaire.libelle
        )
        expect(page.get_by_label("Contexte")).to_contain_text(self.fiche_detection.contexte.nom)
        expect(page.get_by_label("Date 1er signalement")).to_have_value(self.fiche_detection.date_premier_signalement)
        expect(page.get_by_label("Commentaire")).to_have_value(self.fiche_detection.commentaire)
        expect(page.get_by_label("Mesures conservatoires immédiates")).to_have_value(
            self.fiche_detection.mesures_conservatoires_immediates
        )
        expect(page.get_by_label("Mesures de consignation")).to_have_value(self.fiche_detection.mesures_consignation)
        expect(page.get_by_label("Mesures phytosanitaires")).to_have_value(self.fiche_detection.mesures_phytosanitaires)
        expect(page.get_by_label("Mesures de surveillance spécifique")).to_have_value(
            self.fiche_detection.mesures_surveillance_specifique
        )
        context.close()
        page.close()

    def test_fiche_detection_update_with_createur_only(self):
        """Test que la page de modification de la fiche de détection affiche uniquement le créateur pour une fiche détection contenant uniquement le créateur."""
        fiche_detection = FicheDetection.objects.create(
            numero=NumeroFiche.get_next_numero(),
            createur=Unite.objects.create(
                nom="Mission des urgences sanitaires",
                type=Administration.objects.create(nom="AC"),
            ),
        )
        fiche_detection.save()
        edit_fiche_detection_url = f"{self.live_server_url}/sv/fiches-detection/{fiche_detection.id}/modification/"

        context = self.browser.new_context()
        page = context.new_page()
        page.goto(edit_fiche_detection_url)

        expect(page.locator("#createur-input")).to_contain_text(fiche_detection.createur.nom)
        expect(page.get_by_label("Statut évènement")).to_contain_text("----")
        expect(page.locator("#organisme-nuisible")).to_contain_text("----")
        expect(page.get_by_label("Statut règlementaire")).to_contain_text("----")
        expect(page.get_by_label("Contexte")).to_contain_text("----")
        expect(page.get_by_label("Date 1er signalement")).to_have_value("")
        expect(page.get_by_label("Commentaire")).to_have_value("")
        expect(page.get_by_label("Mesures conservatoires immédiates")).to_have_value("")
        expect(page.get_by_label("Mesures de consignation")).to_have_value("")
        expect(page.get_by_label("Mesures phytosanitaires")).to_have_value("")
        expect(page.get_by_label("Mesures de surveillance spécifique")).to_have_value("")

        context.close()
        page.close()

    def test_fiche_detection_update_without_lieux_and_prelevement(self):
        """Test que les modifications des informations, objet de l'évènement et mesures de gestion sont bien enregistrées apès modification."""
        new_unite = Unite.objects.create(nom="BSV", type=Administration.objects.create(nom="AC"))
        new_statut_evenement = StatutEvenement.objects.create(code="TERR")
        new_organisme_nuisible = OrganismeNuisible.objects.create(nom="un ON", libelle_court="UON")
        new_statut_reglementaire = StatutReglementaire.objects.create(code="AZER")
        new_contexte = Contexte.objects.create(nom="alerte européenne")
        new_date_premier_signalement = "2024-04-25"
        new_commentaire = "nouveau commentaire"
        new_mesures_conservatoires_immediates = "nouvelles mesures conservatoires immediates"
        new_mesures_consignation = "nouvelles mesures de consignation"
        new_mesures_phytosanitaires = "nouvelles mesures phytosanitaires"
        new_mesures_surveillance_specifique = "nouvelles mesures de surveillance specifique"

        context = self.browser.new_context()
        page = context.new_page()
        page.goto(self.edit_fiche_detection_url)

        page.locator("#createur-input").select_option(str(new_unite.id))
        page.get_by_label("Statut évènement").select_option(str(new_statut_evenement.id))
        page.locator("#organisme-nuisible").select_option(str(new_organisme_nuisible.id))
        page.get_by_label("Statut règlementaire").select_option(str(new_statut_reglementaire.id))
        page.get_by_label("Contexte").select_option(str(new_contexte.id))
        page.get_by_label("Date 1er signalement").fill(new_date_premier_signalement)
        page.get_by_label("Commentaire").fill(new_commentaire)
        page.get_by_label("Mesures conservatoires immédiates").fill(new_mesures_conservatoires_immediates)
        page.get_by_label("Mesures de consignation").fill(new_mesures_consignation)
        page.get_by_label("Mesures phytosanitaires").fill(new_mesures_phytosanitaires)
        page.get_by_label("Mesures de surveillance spécifique").fill(new_mesures_surveillance_specifique)
        page.click("text=Enregistrer")
        time.sleep(1)

        fiche_detection = FicheDetection.objects.get(id=self.fiche_detection.id)
        self.assertEqual(fiche_detection.createur, new_unite)
        self.assertEqual(fiche_detection.statut_evenement, new_statut_evenement)
        self.assertEqual(fiche_detection.organisme_nuisible, new_organisme_nuisible)
        self.assertEqual(fiche_detection.statut_reglementaire, new_statut_reglementaire)
        self.assertEqual(fiche_detection.contexte, new_contexte)
        self.assertEqual(fiche_detection.commentaire, new_commentaire)
        self.assertEqual(
            fiche_detection.mesures_conservatoires_immediates,
            new_mesures_conservatoires_immediates,
        )
        self.assertEqual(fiche_detection.mesures_consignation, new_mesures_consignation)
        self.assertEqual(fiche_detection.mesures_phytosanitaires, new_mesures_phytosanitaires)
        self.assertEqual(
            fiche_detection.mesures_surveillance_specifique,
            new_mesures_surveillance_specifique,
        )
        context.close()
        page.close()
