from django.db import models
from .mixins import WithChoicesToJS


class CategorieDanger(WithChoicesToJS, models.TextChoices):
    BACILLUS = "Bacillus", "Bactérie > Bacillus"
    BACILLUS_ANTHRACIS = "Bacillus anthracis", "Bactérie > Bacillus > Bacillus anthracis"
    BACILLUS_CEREUS = "Bacillus cereus", "Bactérie > Bacillus > Bacillus cereus"
    BACILLUS_THURIGIENSIS = "Bacillus thurigiensis", "Bactérie > Bacillus > Bacillus thurigiensis"

    BRUCELLA = "Brucella", "Bactérie > Brucella"
    BRUCELLA_MELITENSIS = "Brucella melitensis", "Bactérie > Brucella > Brucella melitensis"
    BRUCELLA_SUIS = "Brucella suis", "Bactérie > Brucella > Brucella suis"
    BRUCELLA_ABORTUS = "Brucella abortus", "Bactérie > Brucella > Brucella abortus"

    CAMPYLOBACTER = "Campylobacter", "Bactérie > Campylobacter"
    CAMPYLOBACTER_JEJUNI = "Campylobacter jejuni", "Bactérie > Campylobacter > Campylobacter jejuni"
    CAMPYLOBACTER_COLI = "Campylobacter coli", "Bactérie > Campylobacter > Campylobacter coli"

    CLOSTRIDIUM = "Clostridium", "Bactérie > Clostridium"
    CLOSTRIDIUM_BOTULINUM = "Clostridium botulinum", "Bactérie > Clostridium > Clostridium botulinum"
    CLOSTRIDIUM_PERFRINGENS = "Clostridium perfringens", "Bactérie > Clostridium > Clostridium perfringens"

    COXIELLA = "Coxiella", "Bactérie > Coxiella"
    COXIELLA_BURNETII = "Coxiella burnetii (fièvre Q)", "Bactérie > Coxiella > Coxiella burnetii (fièvre Q)"

    CRONOBACTER = "Cronobacter", "Bactérie > Cronobacter"
    CRONOBACTER_SAKAZAKII = "Cronobacter sakazakii", "Bactérie > Cronobacter > Cronobacter sakazakii"
    CRONOBACTER_MALONATICUS = "Cronobacter malonaticus", "Bactérie > Cronobacter > Cronobacter malonaticus"

    E_COLI = "Escherichia coli", "Bactérie > Escherichia Coli"
    E_COLI_NON_STEC = (
        "Escherichia coli (non STEC - EHEC)",
        "Bactérie > Escherichia Coli > Escherichia coli (non STEC - EHEC)",
    )
    E_COLI_STEC = (
        "Escherichia coli shigatoxinogène (STEC - EHEC)",
        "Bactérie > Escherichia Coli > Escherichia coli shigatoxinogène (STEC - EHEC)",
    )

    LISTERIA = "Listeria", "Bactérie > Listeria"
    LISTERIA_MONOCYTOGENES = "Listeria monocytogenes", "Bactérie > Listeria > Listeria monocytogenes"

    MYCOBACTERIUM = "Mycobacterium", "Bactérie > Mycobacterium"
    MYCOBACTERIUM_TUBERCULOSIS = "Mycobacterium tuberculosis", "Bactérie > Mycobacterium > Mycobacterium tuberculosis"
    MYCOBACTERIUM_BOVIS = "Mycobacterium bovis", "Bactérie > Mycobacterium > Mycobacterium bovis"
    MYCOBACTERIUM_SUIS = "Mycobacterium suis", "Bactérie > Mycobacterium > Mycobacterium suis"

    SALMONELLA = "Salmonella", "Bactérie > Salmonella"
    SALMONELLA_AUTRE = "Salmonella, autre (à préciser)", "Bactérie > Salmonella > Salmonella, autre (à préciser)"
    SALMONELLA_DUBLIN = "Salmonella dublin", "Bactérie > Salmonella > Salmonella dublin"
    SALMONELLA_ENTERITIDIS = "Salmonella enteritidis", "Bactérie > Salmonella > Salmonella enteritidis"
    SALMONELLA_HADAR = "Salmonella hadar", "Bactérie > Salmonella > Salmonella hadar"
    SALMONELLA_INFANTIS = "Salmonella infantis", "Bactérie > Salmonella > Salmonella infantis"
    SALMONELLA_KENTUCKY = "Salmonella kentucky", "Bactérie > Salmonella > Salmonella kentucky"
    SALMONELLA_MAMBAKA = "Salmonella mambaka", "Bactérie > Salmonella > Salmonella mambaka"
    SALMONELLA_TYPHIMURIUM = "Salmonella typhimurium", "Bactérie > Salmonella > Salmonella typhimurium"
    SALMONELLA_VIRCHOW = "Salmonella virchow", "Bactérie > Salmonella > Salmonella virchow"

    STAPHYLOCOCCUS = "Staphylococcus", "Bactérie > Staphylococcus"
    STAPHYLOCOCCUS_AUREUS = (
        "Staphylococcus aureus et/ou sa toxine",
        "Bactérie > Staphylococcus > Staphylococcus aureus et/ou sa toxine",
    )

    VIBRIO = "Vibrio", "Bactérie > Vibrio"
    VIBRIO_VULNIFICUS = "Vibrio vulnificus", "Bactérie > Vibrio > Vibrio vulnificus"
    VIBRIO_PARAEAHEMOLYTICUS = "Vibrio parahaemolyticus", "Bactérie > Vibrio > Vibrio parahaemolyticus"
    VIBRIO_CHOLERAE = "Vibrio cholerae", "Bactérie > Vibrio > Vibrio cholerae"
    YERSINIA = "Yersinia", "Bactérie > Yersinia"
    YERSINIA_ENTEROCOLITICA = "Yersinia enterocolitica", "Bactérie > Yersinia > Yersinia enterocolitica"
    AUTRE = "Bactérie (autre ou indéterminée)", "Bactérie > Bactérie (autre ou indéterminée)"

    LEVURE_MOISISSURE = "Levure Moisissure", "Levure Moisissure > Levure Moisissure"

    VIRUS_TBEV = "Virus de l'encéphalite à tique (TBEV)", "Virus > Virus de l'encéphalite à tique (TBEV)"
    VIRUS_HEPATITE_A = "Virus de l'hépatite A", "Virus > Virus de l'hépatite A"
    VIRUS_HEPATITE_E = "Virus de l'hépatite E", "Virus > Virus de l'hépatite E"
    VIRUS_GEA = "Virus de la gastroentérite aigüe (GEA)", "Virus > Virus de la gastroentérite aigüe (GEA)"
    VIRUS_GEA_DETAILS = (
        "Virus de la gastroentérite aigüe (GEA) details",
        "Virus > Virus de la gastroentérite aigüe (GEA) > Calivirus, Norovirus, Sapovirus, Rotavirus, Astrovirus, Adénovirus",
    )
    VIRUS_NIPAH = "Virus Nipah", "Virus > Virus Nipah"
    VIRUS_ENTEROVIRUS = "Entérovirus", "Virus > Entérovirus"
    VIRUS_INFLUENZA_ZOONOTIQUE = (
        "Virus influenza zoonotique par voie alimentaire",
        "Virus > Virus influenza zoonotique par voie alimentaire",
    )
    VIRUS_AUTRE = "Virus alimentaire (autre ou indéterminé)", "Virus > Virus alimentaire (autre ou indéterminé)"

    PRION_ESB = "Encéphalopathie spongiforme bovine", "Prion > Encéphalopathie spongiforme bovine"
    PRION_TREMBLANTE = "Tremblante", "Prion > Tremblante"
    PRION_AUTRE = "Prion (autre ou indéterminé)", "Prion > Prion (autre ou indéterminé)"

    PARASITE_ECHINOCOCCUS = "Echinococcus", "Parasite > Echinococcus"
    PARASITE_ANISAKIS = "Anisakis", "Parasite > Anisakis"
    PARASITE_PSEUDOTERRANOVA = "Pseudoterranova", "Parasite > Pseudoterranova"
    PARASITE_DIPHYLLOBOTHRIUM = "Diphyllobothrium", "Parasite > Diphyllobothrium"
    PARASITE_CLINOSTOMUM = "Clinostomum complanatum", "Parasite > Clinostomum complanatum"
    PARASITE_TOXACARA = "Toxacara", "Parasite > Toxacara"
    PARASITE_TOXOPLASMA = "Toxoplasma", "Parasite > Toxoplasma"
    PARASITE_TRICHINE = "Trichine", "Parasite > Trichine"
    PARASITE_ALARIA = "Alaria alata", "Parasite > Alaria alata"
    PARASITE_AUTRE = "Parasite (autre ou indéterminé)", "Parasite > Parasite (autre ou indéterminé)"

    CORPS_ETRANGER_INSECTE = (
        "Insecte - vers - rongeur - autre indésirable",
        "Corps étranger > Insecte - vers - rongeur - autre indésirable",
    )
    CORPS_ETRANGER_VERRE = "Verre - cailloux - autre blessant", "Corps étranger > Verre - cailloux - autre blessant"
    CORPS_ETRANGER_AUTRE = (
        "Corps étranger (autre ou indéterminé)",
        "Corps étranger > Corps étranger (autre ou indéterminé)",
    )

    MYCOTOXINE = "Mycotoxine", "Toxine > Mycotoxine"
    MYCOTOXINE_AFLATOXINE = "Aflatoxine", "Toxine > Mycotoxine > Aflatoxine"
    MYCOTOXINE_OCHRATOXINE = "Ochratoxine A", "Toxine > Mycotoxine > Ochratoxine A"
    MYCOTOXINE_PATULINE = "Patuline", "Toxine > Mycotoxine > Patuline"
    MYCOTOXINE_ERGOT = (
        "Sclérotes d'ergot - Alcaloïdes de l'ergot",
        "Toxine > Mycotoxine > Sclérotes d'ergot - Alcaloïdes de l'ergot",
    )
    MYCOTOXINE_DON = "Déoxynivalénol (DON)", "Toxine > Mycotoxine > Déoxynivalénol (DON)"
    MYCOTOXINE_ZEARALENONE = "Zéaralénone", "Toxine > Mycotoxine > Zéaralénone"
    MYCOTOXINE_FUMONISINES = "Fumonisines", "Toxine > Mycotoxine > Fumonisines"
    MYCOTOXINE_CITRININE = "Citrinine", "Toxine > Mycotoxine > Citrinine"
    MYCOTOXINE_T2_HT2 = "Toxine T2 HT2", "Toxine > Mycotoxine > Toxine T2 HT2"
    MYCOTOXINE_ALTERNARIOL = (
        "Alternariol (AOH) Alternariol monométhyl éther (AME) Acide ténuazonique (TeA)",
        "Toxine > Mycotoxine > Alternariol (AOH) Alternariol monométhyl éther (AME) Acide ténuazonique (TeA)",
    )
    MYCOTOXINE_AUTRE = "Mycotoxine (autre ou indéterminée)", "Toxine > Mycotoxine > Mycotoxine (autre ou indéterminée)"

    PHYCOTOXINE = "Toxine DSP", "Toxine > Phycotoxine et cyanotoxine"
    PHYCOTOXINE_DSP = (
        "Toxine DSP (toxines lipophiles)",
        "Toxine > Phycotoxine et cyanotoxine > Toxine DSP (toxines lipophiles)",
    )
    PHYCOTOXINE_HISTAMINE = "Histamine", "Toxine > Phycotoxine et cyanotoxine > Histamine"
    PHYCOTOXINE_ASP = "Toxine ASP", "Toxine > Phycotoxine et cyanotoxine > Toxine ASP"
    PHYCOTOXINE_PSP = "Toxine PSP", "Toxine > Phycotoxine et cyanotoxine > Toxine PSP"
    PHYCOTOXINE_CIGUATOXINE = "Ciguatoxine", "Toxine > Phycotoxine et cyanotoxine > Ciguatoxine"
    PHYCOTOXINE_AUTRE = (
        "Phycotoxine et cyanotoxine (autre ou indéterminée)",
        "Toxine > Phycotoxine et cyanotoxine > Phycotoxine et cyanotoxine (autre ou indéterminée)",
    )

    PHYTOTOXINE = "Phytotoxine et phyto-estrogène", "Toxine > Phytotoxine et phyto-estrogène"
    PHYTOTOXINE_DATURA = (
        "Datura (alcaloïdes tropaniques)",
        "Toxine > Phytotoxine et phyto-estrogène > Datura (alcaloïdes tropaniques)",
    )
    PHYTOTOXINE_CUCURBITACINE = (
        "Cucurbitacine et autres toxines de courges",
        "Toxine > Phytotoxine et phyto-estrogène > Cucurbitacine et autres toxines de courges",
    )
    PHYTOTOXINE_BETTERAVE = (
        "Betterave crue : toxine indéterminée",
        "Toxine > Phytotoxine et phyto-estrogène > Betterave crue : toxine indéterminée",
    )
    PHYTOTOXINE_PIGNON = (
        "Pignon de pin amer (dysgueusie)",
        "Toxine > Phytotoxine et phyto-estrogène > Pignon de pin amer (dysgueusie)",
    )
    PHYTOTOXINE_CHAMPIGNONS = (
        "Champignons toxiques (divers)",
        "Toxine > Phytotoxine et phyto-estrogène > Champignons toxiques (divers)",
    )
    PHYTOTOXINE_ACIDE_CYANHYDRIQUE = (
        "Acide cyanhydrique",
        "Toxine > Phytotoxine et phyto-estrogène > Acide cyanhydrique",
    )
    PHYTOTOXINE_ACIDE_ERUCIQUE = "Acide érucique", "Toxine > Phytotoxine et phyto-estrogène > Acide érucique"
    PHYTOTOXINE_PYRROLIZIDINIQUES = (
        "Alcaloïdes pyrrolizidiniques",
        "Toxine > Phytotoxine et phyto-estrogène > Alcaloïdes pyrrolizidiniques",
    )
    PHYTOTOXINE_OPIOIDES = "Alcaloïdes opioïdes", "Toxine > Phytotoxine et phyto-estrogène > Alcaloïdes opioïdes"
    PHYTOTOXINE_PHYTOESTROGENE = "Phyto-estrogène", "Toxine > Phytotoxine et phyto-estrogène > Phyto-estrogène"
    PHYTOTOXINE_AUTRE = "Autres toxines végétales", "Toxine > Phytotoxine et phyto-estrogène > Autres toxines végétales"

    ALLERGENE_AUTRE = (
        "Allergène (autre ou indéterminé)",
        "Allergène - composition ou étiquetage > Allergène (autre ou indéterminé)",
    )
    ALLERGENE_ARACHIDE = "Allergène - Arachide", "Allergène - composition ou étiquetage > Allergène - Arachide"
    ALLERGENE_CELERI = "Allergène - Céleri", "Allergène - composition ou étiquetage > Allergène - Céleri"
    ALLERGENE_CRUSTACES = "Allergène - Crustacés", "Allergène - composition ou étiquetage > Allergène - Crustacés"
    ALLERGENE_FRUITS_COQUES = (
        "Allergène - Fruits à coques",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques",
    )
    ALLERGENE_GLUTEN = "Allergène - Gluten", "Allergène - composition ou étiquetage > Allergène - Gluten"
    ALLERGENE_LAIT = "Allergène - Lait", "Allergène - composition ou étiquetage > Allergène - Lait"
    ALLERGENE_LUPIN = "Allergène - Lupin", "Allergène - composition ou étiquetage > Allergène - Lupin"
    ALLERGENE_MOLLUSQUES = "Allergène - Mollusques", "Allergène - composition ou étiquetage > Allergène - Mollusques"
    ALLERGENE_MOUTARDE = "Allergène - Moutarde", "Allergène - composition ou étiquetage > Allergène - Moutarde"
    ALLERGENE_OEUFS = "Allergène - Oeufs", "Allergène - composition ou étiquetage > Allergène - Oeufs"
    ALLERGENE_POISSON = "Allergène - Poisson", "Allergène - composition ou étiquetage > Allergène - Poisson"
    ALLERGENE_SESAME = "Allergène - Sésame", "Allergène - composition ou étiquetage > Allergène - Sésame"
    ALLERGENE_SOJA = "Allergène - Soja", "Allergène - composition ou étiquetage > Allergène - Soja"
    ALLERGENE_SULFITES = "Allergène - Sulfites", "Allergène - composition ou étiquetage > Allergène - Sulfites"

    SA_PPA = "SA - Peste porcine africaine", "Santé animale > SA - Peste porcine africaine"
    SA_PPC = "SA - Peste porcine classique", "Santé animale > SA - Peste porcine classique"
    SA_FIEVRE_APHTEUSE = "SA - Fièvre aphteuse", "Santé animale > SA - Fièvre aphteuse"
    SA_INFLUENZA = (
        "SA - Influenza aviaire hautement pathogène",
        "Santé animale > SA - Influenza aviaire hautement pathogène",
    )
    SA_AUTRE = "SA - Santé animale (autre)", "Santé animale > SA - Santé animale (autre)"

    ETIQUETAGE_DLC = "Etiquetage / DLC", "Etiquetage > Etiquetage / DLC"
    ETIQUETAGE_TEMP = (
        "Etiquetage / température de conservation",
        "Etiquetage > Etiquetage / température de conservation",
    )
    ETIQUETAGE_COMPO = (
        "Etiquetage / composition (sauf allergène)",
        "Etiquetage > Etiquetage / composition (sauf allergène)",
    )
    ETIQUETAGE_USAGE = "Etiquetage / mention de bon usage", "Etiquetage > Etiquetage / mention de bon usage"
    ETIQUETAGE_ALLEGATION = "Etiquetage / allégation", "Etiquetage > Etiquetage / allégation"
    ETIQUETAGE_IONISATION = "Etiquetage / ionisation", "Etiquetage > Etiquetage / ionisation"

    ACTIVITE_INTERDITE = (
        "Activité interdite (mesure administrative)",
        "Activité établissement non autorisée > Activité interdite (mesure administrative)",
    )
    ACTIVITE_IRRADIATION = "Irradiation", "Activité établissement non autorisée > Irradiation"
    ACTIVITE_NON_AGREEE = (
        "Activité non agréée (défaut d'agrément)",
        "Activité établissement non autorisée > Activité non agréée (défaut d'agrément)",
    )
    ACTIVITE_NON_AUTORISEE = (
        "Activité non autorisée (autre autorisation)",
        "Activité établissement non autorisée > Activité non autorisée (autre autorisation)",
    )

    DEFAUT_AUTRE = "Perte de maîtrise autre procédé", "Perte de maîtrise procédé > Perte de maîtrise autre procédé"
    DEFAUT_STERILISATION = "Défaut de stérilisation", "Perte de maîtrise procédé > Défaut de stérilisation"
    DEFAUT_PASTEURISATION = "Défaut de pasteurisation", "Perte de maîtrise procédé > Défaut de pasteurisation"
    DEFAUT_CONDITIONNEMENT = "Défaut du conditionnement", "Perte de maîtrise procédé > Défaut du conditionnement"
    DEFAUT_COMPOSITION = (
        "Défaut de composition (sauf allergène)",
        "Perte de maîtrise procédé > Défaut de composition (sauf allergène)",
    )
    IONISATION_NON_CONFORME = (
        "Ionisation non conforme (hors étiquetage)",
        "Perte de maîtrise procédé > Ionisation non conforme (hors étiquetage)",
    )
    DEFAUT_ORGANOLEPTIQUE = (
        "Défaut organoleptique (toute cause)",
        "Perte de maîtrise procédé > Défaut organoleptique (toute cause)",
    )
    RUPTURE_FROID = "Rupture de la chaîne du froid", "Perte de maîtrise procédé > Rupture de la chaîne du froid"
    CONDITIONS_HYGIENE = "Mauvaises conditions d'hygiène", "Perte de maîtrise procédé > Mauvaises conditions d'hygiène"
    DEFAUT_TRACABILITE = "Défaut de traçabilité", "Perte de maîtrise procédé > Défaut de traçabilité"

    METAL_PLOMB = "Plomb (Pb)", "Elément trace métallique / inorganique > Plomb (Pb)"
    METAL_CADMIUM = "Cadmium (Cd)", "Elément trace métallique / inorganique > Cadmium (Cd)"
    METAL_ARSENIC = "Arsenic (As)", "Elément trace métallique / inorganique > Arsenic (As)"
    METAL_MERCURE = "Mercure (Hg)", "Elément trace métallique / inorganique > Mercure (Hg)"
    METAL_NICKEL = "Nickel (Ni)", "Elément trace métallique / inorganique > Nickel (Ni)"
    METAL_AUTRE = (
        "Elément trace métallique ou composé inorganique (autre)",
        "Elément trace métallique / inorganique > Elément trace métallique ou composé inorganique (autre)",
    )

    POLLUANT_DIOXINES_PCB = "Dioxines et PCB", "Polluant organique persistant > Dioxines et PCB"
    POLLUANT_PFAS = (
        "Substances perfluoroalkylées (PFAS)",
        "Polluant organique persistant > Substances perfluoroalkylées (PFAS)",
    )
    POLLUANT_AUTRE = (
        "Polluant organique persistant (autre)",
        "Polluant organique persistant > Polluant organique persistant (autre)",
    )

    RADIONUCLEIDES = "Radionucléides", "Contaminant physique > Radionucléides"

    MEDICAMENT_INTERDIT = (
        "Résidu médicament - Groupe A - substance interdite ou non autorisée, traitement illégal",
        "Médicament vétérinaire > Résidu médicament - Groupe A - substance interdite ou non autorisée, traitement illégal",
    )
    MEDICAMENT_AUTORISE = (
        "Résidu médicament - Groupe B - substance autorisée",
        "Médicament vétérinaire > Résidu médicament - Groupe B - substance autorisée",
    )
    MEDICAMENT_AUTRE = (
        "Résidu de médicament vétérinaire (autre ou indéterminé)",
        "Médicament vétérinaire > Résidu de médicament vétérinaire (autre ou indéterminé)",
    )

    PESTICIDE_RESIDU = "Résidu de Pesticide Biocide", "Pesticide Biocide > Résidu de Pesticide Biocide"

    NOVEL_FOOD = "Novel food", "Denrée ou ingrédient non autorisé ou dangereux > Novel food"
    NOVEL_FOOD_CBD = (
        "Novel food - CBD/autres cannabinoïdes",
        "Denrée ou ingrédient non autorisé ou dangereux > Novel food > CBD/autres cannabinoïdes",
    )
    NOVEL_FOOD_SURDOSAGE = (
        "Novel food - Surdosage / AMM",
        "Denrée ou ingrédient non autorisé ou dangereux > Novel food > Surdosage / AMM",
    )
    NOVEL_FOOD_CATEGORIE = (
        "Novel food - Non-respect catégorie denrée / AMM",
        "Denrée ou ingrédient non autorisé ou dangereux > Novel food > Non-respect catégorie denrée / AMM",
    )
    NOVEL_FOOD_POPULATION = (
        "Novel food - Non-respect population cible / AMM",
        "Denrée ou ingrédient non autorisé ou dangereux > Novel food > Non-respect population cible / AMM",
    )

    OGM = "OGM", "Denrée ou ingrédient non autorisé ou dangereux > OGM"
    OGM_PLANTES = "OGM - Plantes GM", "Denrée ou ingrédient non autorisé ou dangereux > OGM > Plantes GM"
    OGM_MICROORGANISMES = (
        "OGM - Microorganismes GM",
        "Denrée ou ingrédient non autorisé ou dangereux > OGM > Microorganismes GM",
    )
    OGM_ANIMAUX = "OGM - Animaux GM", "Denrée ou ingrédient non autorisé ou dangereux > OGM > Animaux GM"

    SILDENAFIL = "Sildénafil", "Denrée ou ingrédient non autorisé ou dangereux > Sildénafil"
    SIBUTRAMINE = "Sibutramine", "Denrée ou ingrédient non autorisé ou dangereux > Sibutramine"
    SUBSTANCE_MEDICAMENTEUSE_AUTRE = (
        "Substance médicamenteuse (autre)",
        "Denrée ou ingrédient non autorisé ou dangereux > Substance médicamenteuse (autre)",
    )

    STUPEFIANT = "Stupéfiant", "Denrée ou ingrédient non autorisé ou dangereux > Stupéfiant"
    PSYCHOACTIF = "Psychoactif", "Denrée ou ingrédient non autorisé ou dangereux > Psychoactif"
    PSYCHOACTIF_MUSCIMOL = (
        "Psychoactif - Muscimol",
        "Denrée ou ingrédient non autorisé ou dangereux > Psychoactif > Muscimol (ou autre non médicament non stupéfiant non novel food)",
    )

    SUBSTANCE_INTERDITE = (
        "Substances interdites ou restriction (denrées enrichies)",
        "Denrée ou ingrédient non autorisé ou dangereux > Substances interdites ou restriction (denrées enrichies)",
    )
    SURDOSAGE_NUTRIMENT = (
        "Surdosage nutriment",
        "Denrée ou ingrédient non autorisé ou dangereux > Surdosage nutriment (vitamines, minéraux, autres / denrées enrichies ou CA)",
    )
    CA_NON_TELEDECLARE = (
        "Complément alimentaire non télédéclaré",
        "Denrée ou ingrédient non autorisé ou dangereux > Complément alimentaire non télédéclaré",
    )

    INDETERMINE = "Indéterminé", "Indéterminé > Indéterminé"

    @classmethod
    def dangers_bacteriens(cls):
        return [choice.value for choice in cls if choice.label.startswith("Bactérie >")]
