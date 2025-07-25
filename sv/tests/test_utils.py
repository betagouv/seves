from typing import Optional, Tuple, Union

from django.urls import reverse
from playwright.sync_api import Page, Locator
from playwright.sync_api import expect

from sv.models import FicheZoneDelimitee, ZoneInfestee, FicheDetection, Prelevement


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
    def save_update_btn(self) -> Locator:
        return self.page.get_by_test_id("fiche-detection-save-btn")

    @property
    def publish_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Enregistrer")

    @property
    def add_lieu_btn(self) -> Locator:
        return self.page.locator("#lieux-header").get_by_role("button", name="Ajouter")

    @property
    def add_prelevement_btn(self) -> Locator:
        return self.page.locator("#prelevements-header").get_by_role("button", name="Ajouter")

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
        return self.page.locator("#id_organisme_nuisible")

    @property
    def statut_reglementaire_label(self) -> Locator:
        return self.page.get_by_text("Statut réglementaire")

    @property
    def statut_reglementaire_input(self) -> Locator:
        return self.page.get_by_label("Statut réglementaire")

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
    def vegetaux_infestes_label(self) -> Locator:
        return self.page.get_by_text("Végétaux infestés")

    @property
    def vegetaux_infestes_input(self) -> Locator:
        return self.page.get_by_label("Végétaux infestés")

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

    def force_adresse(self, element, adresse: str, extra_str: str = ""):
        self.page.route(
            "https://api-adresse.data.gouv.fr/search/?*",
            lambda route: route.fulfill(
                status=200, content_type="application/json", body="""{"type": "FeatureCollection","features": []}"""
            ),
        )
        element.click()
        self.page.wait_for_selector("input:focus", state="visible", timeout=2_000)
        self.page.locator("*:focus").fill(f"{adresse}{extra_str}")
        self.page.get_by_role("option", name=f"{adresse}{extra_str} (Forcer la valeur)", exact=True).click()

    def force_commune(self, config=None):
        if not config:
            config = {
                "search_text": "Lille",
                "option_name": "Lille (59)",
                "response_body": """[{"nom":"Lille","code":"59350","_score":1.8106081554689044,"departement":{"code":"59","nom":"Nord"}}]""",
            }

        url = (
            f"https://geo.api.gouv.fr/communes?nom={config['search_text']}&fields=departement&boost=population&limit=15"
        )

        self.page.route(
            url,
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=config["response_body"],
            ),
        )

        self.page.locator(".fr-modal__content .commune .choices__list--single").locator("visible=true").click()
        self.page.wait_for_selector("input:focus", state="visible", timeout=2000)
        self.page.locator("*:focus").fill(config["search_text"])
        self.page.get_by_role("option", name=config["option_name"], exact=True).click()

    @property
    def close_btn(self) -> Locator:
        return self.page.get_by_role("button", name="Fermer")

    @property
    def cancel_btn(self) -> Locator:
        return self.page.locator('[id^="modal-add-lieu-"][open="true"]').get_by_role("link", name="Annuler")

    @property
    def title(self) -> Locator:
        return self.page.locator('[id^="modal-add-edit-lieu-title-"]').locator("visible=true")

    @property
    def save_btn(self) -> Locator:
        return self.page.locator('[data-testid^="lieu-save-btn-"]').locator("visible=true")

    @property
    def nom_label(self) -> Locator:
        return self.page.get_by_text("Nom du lieu").locator("visible=true")

    @property
    def nom_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="-nom"]').locator("visible=true")

    @property
    def adresse_label(self) -> Locator:
        return self.page.get_by_text("Adresse ou lieu-dit").locator("visible=true")

    @property
    def adresse_input(self) -> Locator:
        return (
            self.page.locator(".fr-modal__content")
            .locator("visible=true")
            .locator('[id^="id_lieux-"][id$="adresse_lieu_dit"]')
        )

    @property
    def adresse_choicesjs(self) -> Locator:
        return self.page.locator(".adresse-lieu .choices__list--single").locator("visible=true").locator("..")

    @property
    def commune_label(self) -> Locator:
        return self.page.get_by_text("Commune", exact=True).locator("visible=true")

    @property
    def commune_input(self) -> Locator:
        return self.page.locator(".fr-modal__content").locator("visible=true").locator('[id^="commune-select-"]')

    @property
    def commune_hidden_input(self) -> Locator:
        return self.page.locator(".fr-modal__content").locator("visible=true").locator('[id$="commune"]')

    @property
    def code_insee_hidden_input(self) -> Locator:
        return self.page.locator(".fr-modal__content").locator("visible=true").locator('[id$="code_insee"]')

    @property
    def departement_hidden_input(self) -> Locator:
        return self.page.locator(".fr-modal__content").locator("visible=true").locator('[id$="departement"]')

    @property
    def coord_gps_wgs84_latitude_label(self) -> Locator:
        return self.page.get_by_text("Coordonnées GPS (WGS84)").locator("visible=true")

    @property
    def coord_gps_wgs84_latitude_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="-wgs84_latitude"]').locator("visible=true")

    @property
    def coord_gps_wgs84_longitude_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="-wgs84_longitude"]').locator("visible=true")

    @property
    def is_etablissement_checkbox(self) -> Locator:
        return self.page.locator(".fr-modal__content").locator("visible=true").locator('[for$="is_etablissement"]')

    @property
    def is_etablissement_checkbox_checked(self) -> bool:
        return self.page.locator('[id^="id_lieux-"][id$="is_etablissement"]').is_checked()

    @property
    def sirene_btn(self) -> Locator:
        return self.page.locator('[id$="-sirene-btn"]').locator("visible=true")

    @property
    def activite_etablissement_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="activite_etablissement"]').locator("visible=true")

    @property
    def pays_etablissement_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="pays_etablissement"]').locator("visible=true")

    @property
    def raison_sociale_etablissement_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="raison_sociale_etablissement"]').locator("visible=true")

    @property
    def adresse_etablissement_hidden_input(self) -> Locator:
        return (
            self.page.locator(".fr-modal__content")
            .locator("visible=true")
            .locator('[id^="id_lieux-"][id$="adresse_etablissement"]')
        )

    @property
    def adresse_etablissement_input(self) -> Locator:
        return self.page.locator(".adresse-etablissement .choices__list--single").locator("visible=true").locator("..")

    @property
    def siret_etablissement_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="siret_etablissement"]').locator("visible=true")

    @property
    def code_inupp_etablissement_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="inupp_etablissement"]').locator("visible=true")

    @property
    def lieu_site_inspection_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="site_inspection"]').locator("visible=true")

    @property
    def position_etablissement_input(self) -> Locator:
        return self.page.locator('[id^="id_lieux-"][id$="distribution_etablissement"]').locator("visible=true")


class PrelevementFormDomElements:
    """Classe contenant les éléments du DOM de la modal de création/modification d'un prélèvement"""

    def __init__(self, page: Page):
        self.page = page

    @property
    def close_btn(self) -> Locator:
        return self.page.get_by_role("link", name="Fermer")

    @property
    def cancel_btn(self) -> Locator:
        return self.page.locator('[id^="modal-add-edit-prelevement-"][open="true"]').get_by_role("link", name="Annuler")

    @property
    def save_btn(self) -> Locator:
        return self.page.locator(".prelevement-save-btn").locator("visible=true")

    @property
    def title(self) -> Locator:
        return self.page.get_by_role("heading", name="Ajouter un prelevement")

    @property
    def lieu_input(self) -> Locator:
        return self.page.locator('[id^="id_prelevements-"][id$="lieu"]').locator("visible=true")

    @property
    def structure_input(self) -> Locator:
        return self.page.locator('[id^="id_prelevements-"][id$="structure_preleveuse"]').locator("visible=true")

    @property
    def numero_echantillon_input(self) -> Locator:
        return self.page.locator("#numero-echantillon").get_by_role("textbox")

    @property
    def date_prelevement_input(self) -> Locator:
        return self.page.get_by_label("Date prélèvement").locator("visible=true")

    @property
    def matrice_prelevee_input(self) -> Locator:
        return self.page.locator('[id^="id_prelevements-"][id$="matrice_prelevee"]').locator("visible=true")

    @property
    def espece_echantillon_choices(self) -> Locator:
        return (
            self.page.locator(".fr-modal__content")
            .locator("visible=true")
            .locator("#espece-echantillon .choices__list--single")
        )

    @property
    def espece_echantillon_input(self) -> Locator:
        return self.page.locator(".fr-modal__content").locator("visible=true").locator('[name$="espece_echantillon"]')

    def resultat_input(self, resultat_value: Union[str, Prelevement.Resultat]) -> Locator | None:
        modal = self.page.locator(".fr-modal__content").locator("visible=true")
        if isinstance(resultat_value, str):
            resultat_value = Prelevement.Resultat(resultat_value)
        match resultat_value:
            case Prelevement.Resultat.DETECTE:
                return modal.get_by_text("Détecté", exact=True)
            case Prelevement.Resultat.NON_DETECTE:
                return modal.get_by_text("Non détecté", exact=True)
            case Prelevement.Resultat.NON_CONCLUSIF:
                return modal.get_by_text("Non conclusif", exact=True)
            case Prelevement.Resultat.EN_ATTENTE:
                return modal.get_by_text("En attente", exact=True)

    def type_analyse_input(self, resultat_value) -> Locator:
        modal = self.page.locator(".fr-modal__content").locator("visible=true")
        if resultat_value == "confirmation":
            return modal.get_by_text("Confirmation", exact=True)
        return modal.get_by_text("1ère intention", exact=True)

    @property
    def prelevement_officiel_checkbox(self) -> Locator:
        return self.page.locator('[for^="id_prelevements-"][for$="is_officiel"]').locator("visible=true")

    @property
    def numero_rapport_inspection_input(self) -> Locator:
        return self.page.locator("#numero-rapport-inspection").get_by_role("textbox")

    @property
    def laboratoire_input(self) -> Locator:
        return self.page.locator('[id^="id_prelevements-"][id$="laboratoire"]').locator("visible=true")

    @property
    def laboratoire_label(self) -> Locator:
        return self.page.get_by_text("Laboratoire")

    @property
    def date_rapport_analyse_input(self) -> Locator:
        return self.page.get_by_label("Date rapport d'analyse").locator("visible=true")


class FicheZoneDelimiteeFormPage:
    """Classe permettant de manipuler la page de création/modification d'une fiche zone délimitée"""

    def __init__(self, page: Page, choice_js_fill):
        self.page = page
        self.choice_js_fill = choice_js_fill

        # Risques
        self.organisme_nuisible = page.get_by_label("Organisme nuisible")
        self.statut_reglementaire = page.get_by_label("Statut réglementaire")

        # Détails
        self.commentaire = page.get_by_label("Commentaire")

        # Zone tampon
        self.rayon_zone_tampon = page.get_by_label("Rayon tampon réglementaire ou arbitré")
        self.rayon_zone_tampon_unite_m = page.locator("input[name='unite_rayon_zone_tampon'][value='m']")
        self.rayon_zone_tampon_unite_km = page.locator("input[name='unite_rayon_zone_tampon'][value='km']")
        self.surface_tampon_totale = page.get_by_label("Surface tampon totale")
        self.surface_tampon_totale_unite_m2 = page.locator("input[name='unite_surface_tampon_totale'][value='m2']")
        self.surface_tampon_totale_unite_km2 = page.locator("input[name='unite_surface_tampon_totale'][value='km2']")
        self.surface_tampon_totale_unite_ha = page.locator("input[name='unite_surface_tampon_totale'][value='ha']")

        # Détections hors zone infestée
        self.detections_hors_zone_infestee = page.locator(
            ".fichezoneform__detections-hors-zone-infestee .choices__list--multiple"
        )

        # Zones infestées
        self.zone_infestee_nom_base_locator = "#id_zoneinfestee_set-{}-nom"
        self.zone_infestee_caracteristique_principale_base_locator = (
            "#id_zoneinfestee_set-{}-caracteristique_principale"
        )
        self.zone_infestee_rayon_base_locator = "#id_zoneinfestee_set-{}-rayon"
        self.zone_infestee_rayon_unite_base_locator = "input[name='zoneinfestee_set-{}-unite_rayon'][value='{}']"
        self.zone_infestee_surface_infestee_totale_base_locator = "#id_zoneinfestee_set-{}-surface_infestee_totale"
        self.zone_infestee_surface_infestee_totale_unite_base_locator = (
            "input[name='zoneinfestee_set-{}-unite_surface_infestee_totale'][value='{}']"
        )
        self.zone_infestee_total_forms = self.page.locator('input[name="zoneinfestee_set-TOTAL_FORMS"]')

        # Boutons
        self.add_zone_infestee_btn = page.get_by_role("button", name="Ajouter une zone infestée")
        self.publish_btn = page.get_by_role("button", name="Publier", exact=True)
        self.save_changes_btn = page.get_by_role("button", name="Enregistrer les modifications", exact=True)

    def _select_unite_rayon_zone_tampon(self, unite: FicheZoneDelimitee.UnitesRayon):
        match unite:
            case FicheZoneDelimitee.UnitesRayon.KILOMETRE:
                self.rayon_zone_tampon_unite_km.click(force=True)
            case FicheZoneDelimitee.UnitesRayon.METRE:
                self.rayon_zone_tampon_unite_m.click(force=True)

    def _select_unite_surface_tampon_totale(self, unite: FicheZoneDelimitee.UnitesSurfaceTamponTolale):
        match unite:
            case FicheZoneDelimitee.UnitesSurfaceTamponTolale.METRE_CARRE:
                self.surface_tampon_totale_unite_m2.click(force=True)
            case FicheZoneDelimitee.UnitesSurfaceTamponTolale.KILOMETRE_CARRE:
                self.surface_tampon_totale_unite_km2.click(force=True)
            case FicheZoneDelimitee.UnitesSurfaceTamponTolale.HECTARE:
                self.surface_tampon_totale_unite_ha.click(force=True)

    def _select_unite_surface_infestee_totale(self, unite: ZoneInfestee.UnitesSurfaceInfesteeTotale, index: int):
        match unite:
            case ZoneInfestee.UnitesSurfaceInfesteeTotale.HECTARE:
                self.page.locator(
                    self.zone_infestee_surface_infestee_totale_unite_base_locator.format(index, "ha")
                ).click(force=True)
            case ZoneInfestee.UnitesSurfaceInfesteeTotale.METRE_CARRE:
                self.page.locator(
                    self.zone_infestee_surface_infestee_totale_unite_base_locator.format(index, "m2")
                ).click(force=True)
            case ZoneInfestee.UnitesSurfaceInfesteeTotale.KILOMETRE_CARRE:
                self.page.locator(
                    self.zone_infestee_surface_infestee_totale_unite_base_locator.format(index, "km2")
                ).click(force=True)

    def _select_unite_rayon_zone_infestee(self, unite: ZoneInfestee.UnitesRayon, index: int):
        match unite:
            case ZoneInfestee.UnitesRayon.METRE:
                self.page.locator(self.zone_infestee_rayon_unite_base_locator.format(index, "m")).click(force=True)
            case ZoneInfestee.UnitesRayon.KILOMETRE:
                self.page.locator(self.zone_infestee_rayon_unite_base_locator.format(index, "km")).click(force=True)

    def _select_detections_in_hors_zone_infestee(
        self, detections_hors_zone_infestee: Optional[Tuple[FicheDetection, ...]] = None
    ):
        detections_hors_zone_infestee = detections_hors_zone_infestee or ()
        for detection in detections_hors_zone_infestee:
            self.choice_js_fill(
                self.page,
                ".fichezoneform__detections-hors-zone-infestee .choices__input--cloned:first-of-type",
                str(detection.numero),
                str(detection.numero),
            )

    def _check_unite_rayon_zone_tampon_checked(self, unite_rayon_zone_tampon: FicheZoneDelimitee.UnitesRayon):
        match unite_rayon_zone_tampon:
            case FicheZoneDelimitee.UnitesRayon.KILOMETRE:
                expect(self.rayon_zone_tampon_unite_km).to_be_checked()
            case FicheZoneDelimitee.UnitesRayon.METRE:
                expect(self.rayon_zone_tampon_unite_m).to_be_checked()

    def _check_unite_surface_tampon_totale_checked(
        self, unite_surface_tampon_totale: FicheZoneDelimitee.UnitesSurfaceTamponTolale
    ):
        match unite_surface_tampon_totale:
            case FicheZoneDelimitee.UnitesSurfaceTamponTolale.METRE_CARRE:
                expect(self.surface_tampon_totale_unite_m2).to_be_checked()
            case FicheZoneDelimitee.UnitesSurfaceTamponTolale.KILOMETRE_CARRE:
                expect(self.surface_tampon_totale_unite_km2).to_be_checked()

    def _check_unite_rayon_zone_infestee_checked(self, unite_rayon_zone_infestee: ZoneInfestee.UnitesRayon, index: int):
        match unite_rayon_zone_infestee:
            case ZoneInfestee.UnitesRayon.METRE:
                expect(
                    self.page.locator(self.zone_infestee_rayon_unite_base_locator.format(index, "m"))
                ).to_be_checked()
            case ZoneInfestee.UnitesRayon.KILOMETRE:
                expect(
                    self.page.locator(self.zone_infestee_rayon_unite_base_locator.format(index, "km"))
                ).to_be_checked()

    def _check_unite_surface_infestee_totale_checked(
        self, unite_surface_infestee_totale: ZoneInfestee.UnitesSurfaceInfesteeTotale, index: int
    ):
        match unite_surface_infestee_totale:
            case ZoneInfestee.UnitesSurfaceInfesteeTotale.HECTARE:
                expect(
                    self.page.locator(self.zone_infestee_surface_infestee_totale_unite_base_locator.format(index, "ha"))
                ).to_be_checked()
            case ZoneInfestee.UnitesSurfaceInfesteeTotale.METRE_CARRE:
                expect(
                    self.page.locator(self.zone_infestee_surface_infestee_totale_unite_base_locator.format(index, "m2"))
                ).to_be_checked()
            case ZoneInfestee.UnitesSurfaceInfesteeTotale.KILOMETRE_CARRE:
                expect(
                    self.page.locator(
                        self.zone_infestee_surface_infestee_totale_unite_base_locator.format(index, "km2")
                    )
                ).to_be_checked()

    def _check_detections_in_zone_infestee(self, detections: list[FicheDetection], index: int):
        for detection in detections:
            expect(
                self.page.locator(".zone-infestees__zone-infestee-form")
                .nth(index)
                .locator(".choices__list--multiple")
                .get_by_text(str(detection.numero))
            ).to_be_visible()

    def _check_zones_infestees(self, zones_infestees: list[ZoneInfestee]):
        for index, zone_infestee in enumerate(zones_infestees):
            expect(self.page.locator(self.zone_infestee_nom_base_locator.format(index))).to_have_value(
                zone_infestee.nom
            )
            expect(
                self.page.locator(self.zone_infestee_caracteristique_principale_base_locator.format(index))
            ).to_have_value(zone_infestee.caracteristique_principale)
            expect(self.page.locator(self.zone_infestee_rayon_base_locator.format(index))).to_have_value(
                str(zone_infestee.rayon)
            )
            self._check_unite_rayon_zone_infestee_checked(zone_infestee.unite_rayon, index)
            expect(
                self.page.locator(self.zone_infestee_surface_infestee_totale_base_locator.format(index))
            ).to_have_value(str(zone_infestee.surface_infestee_totale))
            self._check_unite_surface_infestee_totale_checked(zone_infestee.unite_surface_infestee_totale, index)
            self._check_detections_in_zone_infestee(zone_infestee.fichedetection_set.all(), index)

    def check_detections_in_hors_zone_infestee(self, detections: list[FicheDetection]):
        for detection in detections:
            expect(self.detections_hors_zone_infestee.get_by_text(str(detection.numero))).to_be_visible()

    def goto_create_form_page(self, live_server, evenement):
        self.page.goto(f"{live_server.url}{reverse('sv:fiche-zone-delimitee-creation')}?evenement={evenement.pk}")

    def fill_zone_infestee_form(
        self, index, zoneinfestee: ZoneInfestee, detections_zone_infestee: Optional[Tuple[FicheDetection, ...]] = None
    ):
        detections_zone_infestee = detections_zone_infestee or ()
        field_actions = [
            {
                "value": zoneinfestee.nom,
                "action": lambda: self.page.locator(self.zone_infestee_nom_base_locator.format(index)).fill(
                    zoneinfestee.nom
                ),
            },
            {
                "value": zoneinfestee.caracteristique_principale,
                "action": lambda: self.page.locator(
                    self.zone_infestee_caracteristique_principale_base_locator.format(index)
                ).select_option(zoneinfestee.caracteristique_principale),
            },
            {
                "value": zoneinfestee.rayon,
                "action": lambda: self.page.locator(self.zone_infestee_rayon_base_locator.format(index)).fill(
                    str(zoneinfestee.rayon)
                ),
            },
            {
                "value": zoneinfestee.rayon and zoneinfestee.unite_rayon,
                "action": lambda: self._select_unite_rayon_zone_infestee(zoneinfestee.unite_rayon, index),
            },
            {
                "value": zoneinfestee.surface_infestee_totale,
                "action": lambda: self.page.locator(
                    self.zone_infestee_surface_infestee_totale_base_locator.format(index)
                ).fill(str(zoneinfestee.surface_infestee_totale)),
            },
            {
                "value": zoneinfestee.surface_infestee_totale and zoneinfestee.unite_surface_infestee_totale,
                "action": lambda: self._select_unite_surface_infestee_totale(
                    zoneinfestee.unite_surface_infestee_totale, index
                ),
            },
            {
                "value": detections_zone_infestee,
                "action": lambda: self.select_detections_in_zone_infestee(index, detections_zone_infestee),
            },
        ]
        for field in field_actions:
            if field["value"] is not None:
                field["action"]()

    def fill_form(
        self,
        fiche_zone_delimitee: FicheZoneDelimitee,
        zone_infestee: Optional[ZoneInfestee] = None,
        detections_hors_zone_infestee: Optional[Tuple[FicheDetection, ...]] = None,
        detections_zone_infestee: Optional[Tuple[FicheDetection, ...]] = None,
    ):
        detections_zone_infestee = detections_zone_infestee or ()
        field_actions = [
            {
                "value": fiche_zone_delimitee.commentaire,
                "action": lambda: self.commentaire.fill(fiche_zone_delimitee.commentaire),
            },
            {
                "value": fiche_zone_delimitee.rayon_zone_tampon,
                "action": lambda: self.rayon_zone_tampon.fill(str(fiche_zone_delimitee.rayon_zone_tampon)),
            },
            {
                "value": fiche_zone_delimitee.unite_rayon_zone_tampon,
                "action": lambda: self._select_unite_rayon_zone_tampon(fiche_zone_delimitee.unite_rayon_zone_tampon),
            },
            {
                "value": fiche_zone_delimitee.surface_tampon_totale,
                "action": lambda: self.surface_tampon_totale.fill(str(fiche_zone_delimitee.surface_tampon_totale)),
            },
            {
                "value": fiche_zone_delimitee.unite_surface_tampon_totale,
                "action": lambda: self._select_unite_surface_tampon_totale(
                    fiche_zone_delimitee.unite_surface_tampon_totale
                ),
            },
            {
                "value": detections_hors_zone_infestee,
                "action": lambda: self._select_detections_in_hors_zone_infestee(detections_hors_zone_infestee),
            },
            {
                "value": zone_infestee,
                "action": lambda: self.fill_zone_infestee_form(0, zone_infestee, detections_zone_infestee),
            },
        ]
        for field in field_actions:
            if field["value"] is not None:
                field["action"]()

    def add_new_zone_infestee(
        self, zoneinfestee: ZoneInfestee, detections: Optional[Tuple[FicheDetection, ...]] = None
    ):
        detections = detections or ()
        self.add_zone_infestee_btn.click()
        index = max(int(self.zone_infestee_total_forms.get_attribute("value")) - 1, 0)
        self.fill_zone_infestee_form(index, zoneinfestee, detections)

    def save(self):
        self.save_changes_btn.click()

    def submit_update_form(self):
        self.save_changes_btn.click()

    def check_message_succes(self):
        expect(self.page.get_by_text("La fiche zone délimitée a été créée avec succès.")).to_be_visible()

    def check_update_form_content(self, fiche_zone_delimitee: FicheZoneDelimitee):
        expect(self.commentaire).to_have_value(fiche_zone_delimitee.commentaire)
        expect(self.rayon_zone_tampon).to_have_value(str(fiche_zone_delimitee.rayon_zone_tampon))
        self._check_unite_rayon_zone_tampon_checked(fiche_zone_delimitee.unite_rayon_zone_tampon)
        expect(self.surface_tampon_totale).to_have_value(str(fiche_zone_delimitee.surface_tampon_totale))
        self._check_unite_surface_tampon_totale_checked(fiche_zone_delimitee.unite_surface_tampon_totale)
        self.check_detections_in_hors_zone_infestee(fiche_zone_delimitee.fichedetection_set.all())
        self._check_zones_infestees(fiche_zone_delimitee.zoneinfestee_set.all())

    def organisme_nuisible_is_autoselect(self, organisme_nuisible_libelle_expected: str):
        expect(self.organisme_nuisible).to_have_value(organisme_nuisible_libelle_expected)

    def statut_reglementaire_is_autoselect(self, statut_reglementaire_libelle_expected: str):
        expect(self.statut_reglementaire).to_have_value(statut_reglementaire_libelle_expected)

    def organisme_nuisible_is_readonly(self):
        expect(self.organisme_nuisible).to_have_attribute("readonly", "")

    def statut_reglementaire_is_readonly(self):
        expect(self.statut_reglementaire).to_have_attribute("readonly", "")

    def select_detections_in_zone_infestee(
        self, index, detections_zone_infestee: Optional[Tuple[FicheDetection, ...]] = None
    ):
        detections_zone_infestee = detections_zone_infestee or ()
        for detection in detections_zone_infestee:
            self.choice_js_fill(
                self.page,
                f"#zones-infestees .fr-col-4:nth-of-type({index + 1}) .choices__input--cloned:first-of-type",
                str(detection.numero),
                str(detection.numero),
            )

    def has_same_surface_units_order_for_zone_tampon_and_zone_infestee(self) -> bool:
        locator = 'input[name="unite_surface_tampon_totale"]'
        unites_surface_tampon_totale = [btn.get_attribute("value") for btn in self.page.locator(locator).all()]

        locator = 'input[name="zoneinfestee_set-0-unite_surface_infestee_totale"]'
        unites_surface_infestee_totale = [btn.get_attribute("value") for btn in self.page.locator(locator).all()]

        return unites_surface_tampon_totale == unites_surface_infestee_totale

    def has_same_rayon_units_order_for_zone_tampon_and_zone_infestee(self) -> bool:
        locator = 'input[name="unite_rayon_zone_tampon"]'
        unites_rayon_zone_tampon = [btn.get_attribute("value") for btn in self.page.locator(locator).all()]

        locator = 'input[name="zoneinfestee_set-0-unite_rayon"]'
        unites_unite_rayon_zoneinfestee = [btn.get_attribute("value") for btn in self.page.locator(locator).all()]

        return unites_rayon_zone_tampon == unites_unite_rayon_zoneinfestee
