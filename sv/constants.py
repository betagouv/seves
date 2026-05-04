from enum import auto

from django.db.models import TextChoices

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
    JARDINS_PRIVES = auto(), "Jardins privés (plein air)"
    SITES_PUBLICS = auto(), "Sites publics (plein air)"
    ZONE_PROTEGEE = auto(), "Espaces réglementés pour la préservation de l'environnement (plein air)"
    PLANTES_SAUVAGES_HORS_ZONES_PROTEGEES = auto(), "Plantes sauvages dans des aires non protégées (plein air)"
    PLATEFORME_LOGISTIQUE_TRANSIT_STOCKAGE_OU_REVENTE_BOIS = (
        auto(),
        "Plateforme logistique de transit, stockage ou revente de bois d'emballage (plein air)",
    )
    JARDINERIE_PLEIN_AIR = auto(), "Jardinerie (plein air)"
    RESEAU_IRRIGATION_DRAINAGE = auto(), "Réseau d'irrigation ou de drainage"
    ZONE_HUMIDE = auto(), "Zone humide"
    INDUSTRIE_BOIS_PLEIN_AIR = auto(), "Industrie du bois (plein air)"
    POINTS_ENTREE_PLEIN_AIR = auto(), "Points d'entrée (plein air)"
    ZONES_RISQUE_PLEIN_AIR = auto(), "Zones à risque (plein air)"
    AEROPORT_PORT_ROUTE_VOIE_FERREE = auto(), "Aéroport, port, route, voie ferrée (plein air)"
    MARCHES_REVENDEURS_MAGASINS_GROSSISTES = auto(), "Marchés, détaillants, magasins, grossistes (plein air)"
    ZONES_URBAINES = auto(), "Zones urbaines (plein air)"
    BOIS_EMBALLAGE_PALETTES_EN_BOIS = auto(), "Emballages en bois, palettes en bois (plein air)"
    CONTROLES_DES_MOUVEMENTS = auto(), "Contrôles en circulation (plein air)"
    AUTRE_PLEIN_AIR = auto(), "Autre (plein air)"

    # Environnement fermé
    SERRE = auto(), "Serre"
    SITE_PRIVE_AUTRE_QUE_SERRE = auto(), "Site privé (environnement fermé) autre qu'une serre"
    SITE_PUBLIC_AUTRE_QUE_SERRE = auto(), "Site public (environnement fermé) autre qu'une serre"
    SITE_COMMERCIAL_UTILISANT_BOIS_EMBALLAGE = (
        auto(),
        "Installations couvertes et closes de transit, stockage ou revente de bois d'emballage",
    )
    JARDINERIE_ENVIRONNEMENT_FERME = auto(), "Jardinerie (environnement fermé)"
    INDUSTRIE_BOIS_ENVIRONNEMENT_FERME = auto(), "Industrie du bois (environnement fermé)"
    AEROPORT_PORT_GARE = auto(), "Aéroport, port, gare (environnement fermé)"
    ZONES_RISQUE_ENVIRONNEMENT_FERME = auto(), "Zones à risque (environnement fermé)"
    ACTIVITES_CONDITIONNEMENT_ENTREPOT = auto(), "Usine d'emballage, entrepôt (environnement fermé)"
    GROSSISTES_MARCHES_DETAILLANTS = auto(), "Grossistes, marchés, détaillants (environnement fermé)"
    AUTRE_ENVIRONNEMENT_FERME = auto(), "Autre (environnement fermé)"

    # Inconnu
    INCONNU = auto(), "Inconnu - préciser dans les commentaires"
