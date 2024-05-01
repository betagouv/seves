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
        return self.page.get_by_role("button", name="Ajouter une localisation")

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
    def createur_label(self) -> Locator:
        return self.page.get_by_text("Créateur")

    @property
    def createur_input(self) -> Locator:
        return self.page.get_by_label("Créateur")

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
        return self.page.get_by_test_id("lieu-add-btn")

    @property
    def title(self) -> Locator:
        return self.page.get_by_role("heading", name="Ajouter une localisation")

    @property
    def nom_label(self) -> Locator:
        return self.page.get_by_text("Nom de la localisation")

    @property
    def nom_input(self) -> Locator:
        return self.page.get_by_label("Nom de la localisation")

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
    def commune_input(self) -> Locator:
        return self.page.get_by_label("Commune")

    @property
    def code_insee_label(self) -> Locator:
        return self.page.get_by_text("Code INSEE")

    @property
    def code_insee_input(self) -> Locator:
        return self.page.get_by_label("Code INSEE")

    @property
    def departement_label(self) -> Locator:
        return self.page.get_by_text("Département")

    @property
    def departement_input(self) -> Locator:
        return self.page.get_by_label("Département")

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
