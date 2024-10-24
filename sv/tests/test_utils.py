from playwright.sync_api import Page, Locator


class FicheDetectionFormDomElements:
    """Classe contenant les éléments du DOM de la page de création/modification d'une fiche de détection
    Les formulaires pour les lieux et les prélèvements sont gérés dans des autres classes"""

    def __init__(self, page: Page):
        self.page = page

    @property
    def title(self) -> Locator:
        return self.page.locator("#fiche-detection-form-header")

    @property
    def informations_title(self) -> Locator:
        return self.page.get_by_role("heading", name="Informations")

    @property
    def objet_evenement_title(self) -> Locator:
        return self.page.get_by_role("heading", name="Objet de l'évènement")

    @property
    def lieux_title(self) -> Locator:
        return self.page.get_by_role("heading", name="Lieux")

    @property
    def prelevements_title(self) -> Locator:
        return self.page.get_by_role("heading", name="Prélèvements")

    @property
    def mesures_gestion_title(self) -> Locator:
        return self.page.get_by_role("heading", name="Mesures de gestion")

    @property
    def save_btn(self) -> Locator:
        return self.page.get_by_test_id("fiche-detection-save-btn")

    @property
    def add_lieu_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Ajouter un lieu")

    @property
    def add_prelevement_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Ajouter un prélèvement")

    @property
    def date_creation_label(self) -> Locator:
        return self.page.get_by_text("Date de création")

    @property
    def date_creation_input(self) -> Locator:
        return self.page.get_by_label("Date de création")

    @property
    def statut_evenement_label(self) -> Locator:
        return self.page.get_by_text("Statut évènement")

    @property
    def statut_evenement_input(self) -> Locator:
        return self.page.get_by_label("Statut évènement")

    @property
    def organisme_nuisible_label(self) -> Locator:
        return self.page.get_by_text("Organisme nuisible", exact=True)

    @property
    def organisme_nuisible_input(self) -> Locator:
        return self.page.locator("#organisme-nuisible-input")

    @property
    def statut_reglementaire_label(self) -> Locator:
        return self.page.get_by_text("Statut règlementaire")

    @property
    def statut_reglementaire_input(self) -> Locator:
        return self.page.get_by_label("Statut règlementaire")

    @property
    def contexte_label(self) -> Locator:
        return self.page.get_by_text("Contexte")

    @property
    def contexte_input(self) -> Locator:
        return self.page.get_by_label("Contexte")

    @property
    def date_1er_signalement_label(self) -> Locator:
        return self.page.get_by_text("Date 1er signalement")

    @property
    def date_1er_signalement_input(self) -> Locator:
        return self.page.get_by_label("Date 1er signalement")

    @property
    def commentaire_label(self) -> Locator:
        return self.page.get_by_text("Commentaire")

    @property
    def commentaire_input(self) -> Locator:
        return self.page.get_by_label("Commentaire")

    @property
    def mesures_conservatoires_immediates_label(self) -> Locator:
        return self.page.get_by_text("Mesures conservatoires immédiates")

    @property
    def mesures_conservatoires_immediates_input(self) -> Locator:
        return self.page.get_by_label("Mesures conservatoires immédiates")

    @property
    def mesures_consignation_label(self) -> Locator:
        return self.page.get_by_text("Mesures de consignation")

    @property
    def mesures_consignation_input(self) -> Locator:
        return self.page.get_by_label("Mesures de consignation")

    @property
    def mesures_phytosanitaires_label(self) -> Locator:
        return self.page.get_by_text("Mesures phytosanitaires")

    @property
    def mesures_phytosanitaires_input(self) -> Locator:
        return self.page.get_by_label("Mesures phytosanitaires")

    @property
    def mesures_surveillance_specifique_label(self) -> Locator:
        return self.page.get_by_text("Mesures de surveillance spécifique")

    @property
    def mesures_surveillance_specifique_input(self) -> Locator:
        return self.page.get_by_label("Mesures de surveillance spécifique")


class LieuFormDomElements:
    """Classe contenant les éléments du DOM de la modal de création/modification d'un lieu"""

    def __init__(self, page: Page):
        self.page = page

    @property
    def close_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Fermer")

    @property
    def cancel_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Annuler")

    @property
    def save_btn(self) -> Locator:
        return self.page.get_by_test_id("lieu-save-btn")

    @property
    def title(self) -> Locator:
        return self.page.get_by_role("heading", name="Ajouter un lieu")

    @property
    def nom_label(self) -> Locator:
        return self.page.get_by_text("Nom du lieu")

    @property
    def nom_input(self) -> Locator:
        return self.page.get_by_label("Nom du lieu")

    @property
    def adresse_label(self) -> Locator:
        return self.page.get_by_text("Adresse ou lieu-dit")

    @property
    def adresse_input(self) -> Locator:
        return self.page.get_by_label("Adresse ou lieu-dit")

    @property
    def commune_label(self) -> Locator:
        return self.page.get_by_text("Commune", exact=True)

    @property
    def commune_choice_input(self) -> Locator:
        return self.page.locator(".fr-modal__content .choices__item--selectable")

    @property
    def commune_input(self) -> Locator:
        return self.page.locator("#commune-select")

    @property
    def commune_hidden_input(self) -> Locator:
        return self.page.locator("#commune")

    @property
    def code_insee_label(self) -> Locator:
        return self.page.get_by_text("Code INSEE")

    @property
    def code_insee_input(self) -> Locator:
        return self.page.get_by_label("Code INSEE")

    @property
    def code_insee_hidden_input(self) -> Locator:
        return self.page.locator("#code-insee")

    @property
    def departement_label(self) -> Locator:
        return self.page.get_by_text("Département")

    @property
    def departement_input(self) -> Locator:
        return self.page.get_by_label("Département")

    @property
    def departement_hidden_input(self) -> Locator:
        return self.page.locator("#departement")

    @property
    def coord_gps_lamber93_latitude_label(self) -> Locator:
        return self.page.get_by_text("Coordonnées GPS (Lambert 93)")

    @property
    def coord_gps_lamber93_latitude_input(self) -> Locator:
        return self.page.get_by_label("Coordonnées GPS (Lambert 93)")

    @property
    def coord_gps_lamber93_longitude_input(self) -> Locator:
        return self.page.locator("#coordonnees-gps-lambert-93-longitude")

    @property
    def coord_gps_wgs84_latitude_label(self) -> Locator:
        return self.page.get_by_text("Coordonnées GPS (WGS84)")

    @property
    def coord_gps_wgs84_latitude_input(self) -> Locator:
        return self.page.get_by_label("Coordonnées GPS (WGS84)")

    @property
    def coord_gps_wgs84_longitude_input(self) -> Locator:
        return self.page.locator("#coordonnees-gps-wgs84-longitude")

    @property
    def is_etablissement_checkbox(self) -> Locator:
        return self.page.get_by_text("Il s'agit d'un établissement")

    @property
    def nom_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Nom")

    @property
    def nom_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Nom", exact=True)

    @property
    def activite_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Activité")

    @property
    def activite_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Activité")

    @property
    def pays_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Pays")

    @property
    def pays_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Pays")

    @property
    def raison_sociale_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Raison sociale")

    @property
    def raison_sociale_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Raison sociale")

    @property
    def adresse_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Adresse")

    @property
    def adresse_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Adresse", exact=True)

    @property
    def siret_etablissement_label(self) -> Locator:
        return self.page.get_by_text("N° SIRET")

    @property
    def siret_etablissement_input(self) -> Locator:
        return self.page.get_by_label("N° SIRET")

    @property
    def code_inpp_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Code INPP")

    @property
    def code_inpp_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Code INPP")

    @property
    def type_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Type")

    @property
    def type_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Type")

    @property
    def position_etablissement_label(self) -> Locator:
        return self.page.get_by_text("Position")

    @property
    def position_etablissement_input(self) -> Locator:
        return self.page.get_by_label("Position")


class PrelevementFormDomElements:
    """Classe contenant les éléments du DOM de la modal de création/modification d'un prélèvement"""

    def __init__(self, page: Page):
        self.page = page

    @property
    def close_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Fermer")

    @property
    def cancel_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Annuler")

    @property
    def save_btn(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-save-btn")

    @property
    def title(self) -> Locator:
        return self.page.get_by_role("heading", name="Ajouter un prelevement")

    @property
    def lieu_label(self) -> Locator:
        return self.page.get_by_text("Lieu", exact=True)

    @property
    def lieu_input(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-lieu")

    @property
    def structure_label(self) -> Locator:
        return self.page.get_by_text("Structure")

    @property
    def structure_input(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-structure")

    @property
    def numero_echantillon_label(self) -> Locator:
        return self.page.get_by_text("N° d'échantillon")

    @property
    def numero_echantillon_input(self) -> Locator:
        return self.page.locator("#numero-echantillon").get_by_role("textbox")

    @property
    def date_prelevement_label(self) -> Locator:
        return self.page.get_by_text("Date de prélèvement")

    @property
    def date_prelevement_input(self) -> Locator:
        return self.page.get_by_label("Date prélèvement")

    @property
    def site_inspection_label(self) -> Locator:
        return self.page.get_by_text("Site d'inspection")

    @property
    def site_inspection_input(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-site-inspection")

    @property
    def matrice_prelevee_label(self) -> Locator:
        return self.page.get_by_text("Matrice prélevée")

    @property
    def matrice_prelevee_input(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-matrice-prelevee")

    @property
    def espece_echantillon_label(self) -> Locator:
        return self.page.get_by_text("Espèce de l'échantillon")

    @property
    def espece_echantillon_input(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-espece-echantillon")

    @property
    def resultat_label(self) -> Locator:
        return self.page.get_by_text("Résultat")

    def resultat_input(self, resultat_value) -> Locator:
        return self.page.get_by_test_id("prelevement-form-resultat-" + resultat_value)

    @property
    def prelevement_officiel_checkbox(self) -> Locator:
        return self.page.get_by_text("Prélèvement officiel")

    @property
    def numero_phytopass_label(self) -> Locator:
        return self.page.get_by_text("N° Phytopass")

    @property
    def numero_phytopass_input(self) -> Locator:
        return self.page.locator("#numero-phytopass").get_by_role("textbox")

    @property
    def numero_resytal_input(self) -> Locator:
        return self.page.locator("#numero-resytal").get_by_role("textbox")

    @property
    def laboratoire_agree_label(self) -> Locator:
        return self.page.get_by_text("Laboratoire agréé")

    @property
    def laboratoire_agree_input(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-laboratoire-agree")

    @property
    def laboratoire_confirmation_label(self) -> Locator:
        return self.page.get_by_text("Laboratoire de confirmation")

    @property
    def laboratoire_confirmation_input(self) -> Locator:
        return self.page.get_by_test_id("prelevement-form-laboratoire-confirmation")
