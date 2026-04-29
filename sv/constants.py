from enum import auto, property as enum_property

from django.db.models import TextChoices
from django.utils.functional import classproperty

STRUCTURE_EXPLOITANT = "Exploitant"
STRUCTURES_PRELEVEUSES = [
    "SRAL",
    "Délégataire",
    "DSF",
    "SIVEP",
    "SocFrance",
    "FAM",
    "CTIFL",
    STRUCTURE_EXPLOITANT,
    "Salim",
]

STATUTS_EVENEMENT = ["Foyer", "Interception", "Incursion", "Suspicion"]

STATUTS_REGLEMENTAIRES = {
    "OQP": "organisme quarantaine prioritaire",
    "OQ": "organisme quarantaine",
    "OQZP": "organisme quarantaine zone protégée",
    "ORNQ": "organisme réglementé non quarantaine",
    "OTR": "organisme temporairement réglementé",
    "OE": "organisme émergent",
    "NR": "non réglementé",
    "END": "en cours de détermination",
}

CONTEXTES = [
    "enquête officielle relative aux organismes nuisibles",
    "enquête liée à un foyer existant ou éradiqué d’un organisme nuisible",
    "inspections phytosanitaires de tout type",
    "inspection de traçage en amont et en aval liée à la présence spécifique de l’organisme nuisible",
    "inspection officielle à des fins autres que phytosanitaires",
    "informations fournies par des opérateurs professionnels, des laboratoires ou d’autres personnes",
    "informations scientifiques",
    "notification rasff",
    "autre (à préciser dans le fil de suivi)",
]

KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES = {
    "OQ": [
        "POCZSH",
        "HETDPA",
        "RALSSL",
        "HETDRO",
        "MELGCH",
        "MELGFA",
        "PHYP64",
        "CERAFP",
        "RHIOHI",
        "ALECSN",
        "PITOJU",
        "TOLCND",
        "GEOHMO",
        "SCITDO",
        "DACULA",
        "MELGMY",
        "CORBFL",
        "DRAERO",
        "ELSIAU",
        "XYLBAF",
        "XYLBFE",
    ],
    "OQZP": [],
    "OQP": ["GUIGCI", "DACUDO", "POPIJA", "DACUZO", "BURSXY", "ANOLCN", "XYLEFA", "XYLEFM"],
    "OE": ["TOFBV0"],
    "OTR": ["POCZSH", "XYLOCH", "TOUMPA"],
    "NR": ["ALECCA"],
}

KNOWN_OEPPS = [oepp for oepp_list in KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES.values() for oepp in oepp_list]

LABORATOIRES_AGREES = [
    "LDA 02",
    "LDA 13",
    "SEDIA 21",
    "Labocéa",
    "CTI 24",
    "BRET 29",
    "IFV 30",
    "LDA 31",
    "LCA 33",
    "LDA 33b",
    "QUAL 54",
    "COM 62",
    "LOOS 62",
    "LDA 67",
    "LDA 71",
    "CENTRESUD 87",
    "LDA 972 (Martinique)",
    "FDGDON 974 (Réunion)",
]
LABORATOIRES_CONFIRMATION_OFFICIELLE = [
    "ANSES 34",
    "ANSES 49",
    "ANSES 54b",
    "ANSES 35b",
    "ANSES 63",
    "ANSES 974",
    "SNES 49",
]

POSITION_CHAINE_DISTRIBUTION = [
    "Consommateur",
    "Expéditeur",
    "Agriculteur",
    "Destinataire",
    "Importateur",
    "Détaillant",
    "Emballeur",
    "Fabricant",
    "Entreprise de transport",
    "Producteur",
    "Point d'entrée",
    "Grossiste/entrepôt",
    "Stockage",
    "Achat en ligne",
]


class SiteInspection(TextChoices):
    # Plein air - zone de production
    CHAMP_CULTURE_PATURAGE = auto(), "Champ (culture, pâturage)"
    VERGER_VIGNE = auto(), "Verger/vigne"
    PEPINIERE = auto(), "Pépinière"
    FORET = auto(), "Forêt"

    # Plein air - autre
    JARDINS_PRIVES = auto(), "Jardins privés"
    SITES_PUBLICS = auto(), "Sites publics"
    ZONE_PROTEGEE = auto(), "Zone protégée"
    PLANTES_SAUVAGES_HORS_ZONES_PROTEGEES = auto(), "Plantes sauvages en dehors des zones protégées"
    PLATEFORME_LOGISTIQUE_TRANSIT_STOCKAGE_OU_REVENTE_BOIS = auto(), "Site commercial qui utilise du bois d'emballage"
    JARDINERIE_PLEIN_AIR = auto(), "Jardinerie"
    RESEAU_IRRIGATION_DRAINAGE = auto(), "Réseau d'irrigation ou de drainage"
    ZONE_HUMIDE = auto(), "Zone humide"
    INDUSTRIE_BOIS_PLEIN_AIR = auto(), "Industrie du bois"
    POINTS_ENTREE_PLEIN_AIR = auto(), "Points d'entrée"
    ZONES_RISQUE_PLEIN_AIR = auto(), "Zones à risque"
    AEROPORT_PORT_ROUTE_VOIE_FERREE = auto(), "Aéroport, port, route, voie ferrée"
    MARCHES_REVENDEURS_MAGASINS_GROSSISTES = auto(), "Marchés, revendeurs, magasins, grossistes"
    ZONES_URBAINES = auto(), "Zones urbaines"
    BOIS_EMBALLAGE_PALETTES_EN_BOIS = auto(), "Bois d'emballage, palettes en bois"
    CONTROLES_DES_MOUVEMENTS = auto(), "Contrôles des mouvements"
    AUTRE_PLEIN_AIR = auto(), "Autre (plein air) - préciser dans les commentaires"

    # Environnement fermé
    SERRE = auto(), "Serre"
    SITE_PRIVE_AUTRE_QUE_SERRE = auto(), "Site privé autre qu'une serre"
    SITE_PUBLIC_AUTRE_QUE_SERRE = auto(), "Site public autre qu'une serre"
    SITE_COMMERCIAL_UTILISANT_BOIS_EMBALLAGE = auto(), "Site commercial qui utilise du bois d'emballage"
    JARDINERIE_ENVIRONNEMENT_FERME = auto(), "Jardinerie"
    INDUSTRIE_BOIS_ENVIRONNEMENT_FERME = auto(), "Industrie du bois"
    AEROPORT_PORT_GARE = auto(), "Aéroport, port, gare"
    ZONES_RISQUE_ENVIRONNEMENT_FERME = auto(), "Zones à risque"
    ACTIVITES_CONDITIONNEMENT_ENTREPOT = auto(), "Activités de conditionnement, entrepôt"
    GROSSISTES_MARCHES_DETAILLANTS = auto(), "Grossistes, marchés, détaillants"
    AUTRE_ENVIRONNEMENT_FERME = auto(), "Autre (environnement fermé) - préciser dans les commentaires"

    # Inconnu
    INCONNU = auto(), "Inconnu - préciser dans les commentaires"

    @classmethod
    def create_named_groups(cls):
        return {
            "Plein air - zone de production": (
                cls.CHAMP_CULTURE_PATURAGE,
                cls.VERGER_VIGNE,
                cls.PEPINIERE,
                cls.FORET,
            ),
            "Plein air - autre": (
                cls.JARDINS_PRIVES,
                cls.SITES_PUBLICS,
                cls.ZONE_PROTEGEE,
                cls.PLANTES_SAUVAGES_HORS_ZONES_PROTEGEES,
                cls.PLATEFORME_LOGISTIQUE_TRANSIT_STOCKAGE_OU_REVENTE_BOIS,
                cls.JARDINERIE_PLEIN_AIR,
                cls.RESEAU_IRRIGATION_DRAINAGE,
                cls.ZONE_HUMIDE,
                cls.INDUSTRIE_BOIS_PLEIN_AIR,
                cls.POINTS_ENTREE_PLEIN_AIR,
                cls.ZONES_RISQUE_PLEIN_AIR,
                cls.AEROPORT_PORT_ROUTE_VOIE_FERREE,
                cls.MARCHES_REVENDEURS_MAGASINS_GROSSISTES,
                cls.ZONES_URBAINES,
                cls.BOIS_EMBALLAGE_PALETTES_EN_BOIS,
                cls.CONTROLES_DES_MOUVEMENTS,
                cls.AUTRE_PLEIN_AIR,
            ),
            "Environnement fermé": (
                cls.SERRE,
                cls.SITE_PRIVE_AUTRE_QUE_SERRE,
                cls.SITE_PUBLIC_AUTRE_QUE_SERRE,
                cls.SITE_COMMERCIAL_UTILISANT_BOIS_EMBALLAGE,
                cls.JARDINERIE_ENVIRONNEMENT_FERME,
                cls.INDUSTRIE_BOIS_ENVIRONNEMENT_FERME,
                cls.AEROPORT_PORT_GARE,
                cls.ZONES_RISQUE_ENVIRONNEMENT_FERME,
                cls.ACTIVITES_CONDITIONNEMENT_ENTREPOT,
                cls.GROSSISTES_MARCHES_DETAILLANTS,
                cls.AUTRE_ENVIRONNEMENT_FERME,
            ),
            "Inconnu": (cls.INCONNU,),
        }

    @classproperty
    def named_groups(cls):
        if not hasattr(cls, "_named_groups_"):
            cls._named_groups_ = {
                named_group: tuple((enum.value, enum.label) for enum in values)
                for named_group, values in cls.create_named_groups().items()
            }

        return cls._named_groups_

    @enum_property
    def named_group(self):
        if not hasattr(self, "_named_group_"):
            for named_group, values in self.named_groups.items():
                for name, _ in values:
                    SiteInspection[name]._named_group_ = named_group

        return self._named_group_

    @enum_property
    def label_with_group(self):
        return f"{self.named_group} > {self.label}"


class ElementInfesteType(TextChoices):
    VEGETAUX_A_REPLANTER = auto(), "Végétaux destinés à être (re)plantés ou reproduits"
    VEGETAUX_DEJA_PLANTES = auto(), "Végétaux déjà plantés, ne devant pas être reproduits ni déplacés"
    AUTRES_VEGETAUX = auto(), "Autres végétaux, parties de végétaux ou produits végétaux"
    VEGETAUX_NON_SPECIFIES = auto(), "Végétaux : non spécifiés"
    PIEGE = auto(), "Objet : piège"
    SOL = auto(), "Objet : sol"
    EAU = auto(), "Objet : eau"
    AUTRES_OBJETS = auto(), "Autres objets"
    AUCUN = auto(), "Aucun"
    INCONNU = auto(), "Inconnu"


class ElementInfesteQuantiteUnite(TextChoices):
    METRE_CARRE = auto(), "m²"
    KILOMETRE_CARRE = auto(), "km²"
    HECTAR = auto(), "ha"
    METRE_CUBE = auto(), "m³"
    KILOGRAMME = auto(), "kg"
    PARTIE_POUR_CENT = auto(), "pce"
