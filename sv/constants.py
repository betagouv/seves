REGIONS = [
    "Auvergne-Rhône-Alpes",
    "Bourgogne-Franche-Comté",
    "Bretagne",
    "Centre-Val de Loire",
    "Corse",
    "Grand Est",
    "Hauts-de-France",
    "Île-de-France",
    "Normandie",
    "Nouvelle-Aquitaine",
    "Occitanie",
    "Pays de la Loire",
    "Provence-Alpes-Côte d'Azur",
    "Guadeloupe",
    "Martinique",
    "Guyane",
    "La Réunion",
    "Mayotte",
]

DEPARTEMENTS = [
    ("01", "Ain", "Auvergne-Rhône-Alpes"),
    ("03", "Allier", "Auvergne-Rhône-Alpes"),
    ("07", "Ardèche", "Auvergne-Rhône-Alpes"),
    ("15", "Cantal", "Auvergne-Rhône-Alpes"),
    ("26", "Drôme", "Auvergne-Rhône-Alpes"),
    ("38", "Isère", "Auvergne-Rhône-Alpes"),
    ("42", "Loire", "Auvergne-Rhône-Alpes"),
    ("43", "Haute-Loire", "Auvergne-Rhône-Alpes"),
    ("63", "Puy-de-Dôme", "Auvergne-Rhône-Alpes"),
    ("69", "Rhône", "Auvergne-Rhône-Alpes"),
    ("73", "Savoie", "Auvergne-Rhône-Alpes"),
    ("74", "Haute-Savoie", "Auvergne-Rhône-Alpes"),
    ("21", "Côte-d'Or", "Bourgogne-Franche-Comté"),
    ("25", "Doubs", "Bourgogne-Franche-Comté"),
    ("39", "Jura", "Bourgogne-Franche-Comté"),
    ("58", "Nièvre", "Bourgogne-Franche-Comté"),
    ("70", "Haute-Saône", "Bourgogne-Franche-Comté"),
    ("71", "Saône-et-Loire", "Bourgogne-Franche-Comté"),
    ("89", "Yonne", "Bourgogne-Franche-Comté"),
    ("90", "Territoire de Belfort", "Bourgogne-Franche-Comté"),
    ("22", "Côtes-d'Armor", "Bretagne"),
    ("29", "Finistère", "Bretagne"),
    ("35", "Ille-et-Vilaine", "Bretagne"),
    ("56", "Morbihan", "Bretagne"),
    ("18", "Cher", "Centre-Val de Loire"),
    ("28", "Eure-et-Loir", "Centre-Val de Loire"),
    ("36", "Indre", "Centre-Val de Loire"),
    ("37", "Indre-et-Loire", "Centre-Val de Loire"),
    ("41", "Loir-et-Cher", "Centre-Val de Loire"),
    ("45", "Loiret", "Centre-Val de Loire"),
    ("2A", "Corse-du-Sud", "Corse"),
    ("2B", "Haute-Corse", "Corse"),
    ("08", "Ardennes", "Grand Est"),
    ("10", "Aube", "Grand Est"),
    ("51", "Marne", "Grand Est"),
    ("52", "Haute-Marne", "Grand Est"),
    ("54", "Meurthe-et-Moselle", "Grand Est"),
    ("55", "Meuse", "Grand Est"),
    ("57", "Moselle", "Grand Est"),
    ("67", "Bas-Rhin", "Grand Est"),
    ("68", "Haut-Rhin", "Grand Est"),
    ("88", "Vosges", "Grand Est"),
    ("02", "Aisne", "Hauts-de-France"),
    ("59", "Nord", "Hauts-de-France"),
    ("60", "Oise", "Hauts-de-France"),
    ("62", "Pas-de-Calais", "Hauts-de-France"),
    ("80", "Somme", "Hauts-de-France"),
    ("75", "Paris", "Île-de-France"),
    ("77", "Seine-et-Marne", "Île-de-France"),
    ("78", "Yvelines", "Île-de-France"),
    ("91", "Essonne", "Île-de-France"),
    ("92", "Hauts-de-Seine", "Île-de-France"),
    ("93", "Seine-Saint-Denis", "Île-de-France"),
    ("94", "Val-de-Marne", "Île-de-France"),
    ("95", "Val-d'Oise", "Île-de-France"),
    ("14", "Calvados", "Normandie"),
    ("27", "Eure", "Normandie"),
    ("50", "Manche", "Normandie"),
    ("61", "Orne", "Normandie"),
    ("76", "Seine-Maritime", "Normandie"),
    ("16", "Charente", "Nouvelle-Aquitaine"),
    ("17", "Charente-Maritime", "Nouvelle-Aquitaine"),
    ("19", "Corrèze", "Nouvelle-Aquitaine"),
    ("23", "Creuse", "Nouvelle-Aquitaine"),
    ("24", "Dordogne", "Nouvelle-Aquitaine"),
    ("33", "Gironde", "Nouvelle-Aquitaine"),
    ("40", "Landes", "Nouvelle-Aquitaine"),
    ("47", "Lot-et-Garonne", "Nouvelle-Aquitaine"),
    ("64", "Pyrénées-Atlantiques", "Nouvelle-Aquitaine"),
    ("79", "Deux-Sèvres", "Nouvelle-Aquitaine"),
    ("86", "Vienne", "Nouvelle-Aquitaine"),
    ("87", "Haute-Vienne", "Nouvelle-Aquitaine"),
    ("09", "Ariège", "Occitanie"),
    ("11", "Aude", "Occitanie"),
    ("12", "Aveyron", "Occitanie"),
    ("30", "Gard", "Occitanie"),
    ("31", "Haute-Garonne", "Occitanie"),
    ("32", "Gers", "Occitanie"),
    ("34", "Hérault", "Occitanie"),
    ("46", "Lot", "Occitanie"),
    ("48", "Lozère", "Occitanie"),
    ("65", "Hautes-Pyrénées", "Occitanie"),
    ("66", "Pyrénées-Orientales", "Occitanie"),
    ("81", "Tarn", "Occitanie"),
    ("82", "Tarn-et-Garonne", "Occitanie"),
    ("44", "Loire-Atlantique", "Pays de la Loire"),
    ("49", "Maine-et-Loire", "Pays de la Loire"),
    ("53", "Mayenne", "Pays de la Loire"),
    ("72", "Sarthe", "Pays de la Loire"),
    ("85", "Vendée", "Pays de la Loire"),
    ("04", "Alpes-de-Haute-Provence", "Provence-Alpes-Côte d'Azur"),
    ("05", "Hautes-Alpes", "Provence-Alpes-Côte d'Azur"),
    ("06", "Alpes-Maritimes", "Provence-Alpes-Côte d'Azur"),
    ("13", "Bouches-du-Rhône", "Provence-Alpes-Côte d'Azur"),
    ("83", "Var", "Provence-Alpes-Côte d'Azur"),
    ("84", "Vaucluse", "Provence-Alpes-Côte d'Azur"),
    ("971", "Guadeloupe", "Guadeloupe"),
    ("972", "Martinique", "Martinique"),
    ("973", "Guyane", "Guyane"),
    ("974", "La Réunion", "La Réunion"),
    ("976", "Mayotte", "Mayotte"),
]

STRUCTURES_PRELEVEUSES = [
    "SRAL",
    "Délégataire",
    "DSF",
    "SIVEP",
    "SEMAE",
    "FAM",
    "CTIFL",
    "Exploitant",
    "Salim",
]

STATUTS_EVENEMENT = ["Foyer", "Interception", "Incursion", "Suspicion"]

STATUTS_REGLEMENTAIRES = {
    "OQP": "organisme quarantaine prioritaire",
    "OQ": "organisme quarantaine",
    "OQZP": "organisme quarantaine zone protégée",
    "ORNQ": "organisme réglementée non quarantaine",
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
        "XYLEFM",
        "POCZSH",
        "XYLOCH",
        "PSDMS2",
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
        "XIPHRI",
        "1BCTRG",
        "CORBFL",
        "PHYPAE",
        "PHYTRA",
        "1BEGOG",
        "ALECCT",
        "LIBEAM",
    ],
    "OQZP": ["BNYVV0", "RHYCFE"],
    "OQP": [
        "GUIGCI",
        "DACUDO",
        "POPIJA",
        "DACUZO",
        "BURSXY",
        "ANOLCN",
        "XYLEFA",
        "TOBRFV",
        "1POMAG",
    ],
    "OE": [
        "TOUMPA",
        "XYLBAF",
        "XYLBFE",
        "SCITGI",
    ],
}

KNOWN_OEPPS = [oepp for oepp_list in KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES.values() for oepp in oepp_list]
