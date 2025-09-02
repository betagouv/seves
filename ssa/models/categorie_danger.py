from django.db import models
from .mixins import WithChoicesToJS


class CategorieDanger(WithChoicesToJS, models.TextChoices):
    ALLERGENE_ARACHIDE = "Allergène - Arachide", "Allergène - composition ou étiquetage > Allergène - Arachide"
    ALLERGENE_CELERI = "Allergène - Céleri", "Allergène - composition ou étiquetage > Allergène - Céleri"
    ALLERGENE_CRUSTACES = "Allergène - Crustacés", "Allergène - composition ou étiquetage > Allergène - Crustacés"
    ALLERGENE_FRUITS_A_COQUES = (
        "Allergène - Fruits à coques",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques",
    )
    AMANDE = "Amande", "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Amande"
    AUTRE_FRUIT_A_COQUE_OU_INDETERMINE = (
        "Autre fruit à coque ou indéterminé",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Autre fruit à coque ou indéterminé",
    )
    NOISETTE = "Noisette", "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Noisette"
    NOIX = "Noix", "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Noix"
    NOIX_DE_CAJOU = (
        "Noix de cajou",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Noix de cajou",
    )
    NOIX_DE_MACADAMIA = (
        "Noix de Macadamia",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Noix de Macadamia",
    )
    NOIX_DE_PECAN = (
        "Noix de Pécan",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Noix de Pécan",
    )
    NOIX_DU_BRESIL = (
        "Noix du Brésil",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Noix du Brésil",
    )
    NOIX_DU_QUEENSLAND = (
        "Noix du Queensland",
        "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Noix du Queensland",
    )
    PISTACHE = "Pistache", "Allergène - composition ou étiquetage > Allergène - Fruits à coques > Pistache"
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
    AUTRE_ALLERGENE_OU_INDETERMINE = (
        "Autre allergène ou indéterminé",
        "Allergène - composition ou étiquetage > Autre allergène ou indéterminé",
    )
    AUTRE_BACTERIE_OU_INDETERMINEE = "Autre bactérie ou indéterminée", "Bactérie > Autre bactérie ou indéterminée"
    BACILLUS = "Bacillus", "Bactérie > Bacillus"
    BACILLUS_ANTHRACIS = "Bacillus anthracis", "Bactérie > Bacillus > Bacillus anthracis"
    BACILLUS_CEREUS = "Bacillus cereus", "Bactérie > Bacillus > Bacillus cereus"
    BACILLUS_THURIGIENSIS = "Bacillus thurigiensis", "Bactérie > Bacillus > Bacillus thurigiensis"
    BRUCELLA = "Brucella", "Bactérie > Brucella"
    BRUCELLA_ABORTUS = "Brucella abortus", "Bactérie > Brucella > Brucella abortus"
    BRUCELLA_MELITENSIS = "Brucella melitensis", "Bactérie > Brucella > Brucella melitensis"
    BRUCELLA_SUIS = "Brucella suis", "Bactérie > Brucella > Brucella suis"
    CAMPYLOBACTER = "Campylobacter", "Bactérie > Campylobacter"
    CAMPYLOBACTER_COLI = "Campylobacter coli", "Bactérie > Campylobacter > Campylobacter coli"
    CAMPYLOBACTER_JEJUNI = "Campylobacter jejuni", "Bactérie > Campylobacter > Campylobacter jejuni"
    CLOSTRIDIUM = "Clostridium", "Bactérie > Clostridium"
    CLOSTRIDIUM_BOTULINUM = "Clostridium botulinum", "Bactérie > Clostridium > Clostridium botulinum"
    CLOSTRIDIUM_PERFRINGENS = "Clostridium perfringens", "Bactérie > Clostridium > Clostridium perfringens"
    COLIFORMES = "Coliformes", "Bactérie > Coliformes"
    COXIELLA = "Coxiella", "Bactérie > Coxiella"
    COXIELLA_BURNETII = "Coxiella burnetii (fièvre Q)", "Bactérie > Coxiella > Coxiella burnetii (fièvre Q)"
    CRONOBACTER = "Cronobacter", "Bactérie > Cronobacter"
    CRONOBACTER_MALONATICUS = "Cronobacter malonaticus", "Bactérie > Cronobacter > Cronobacter malonaticus"
    CRONOBACTER_SAKAZAKII = "Cronobacter sakazakii", "Bactérie > Cronobacter > Cronobacter sakazakii"
    ENTEROBACTERIES = "Entérobactéries", "Bactérie > Entérobactéries"
    ESCHERICHIA_COLI = "Escherichia Coli", "Bactérie > Escherichia Coli"
    ESCHERICHIA_COLI_SHIGATOXINOGENE = (
        "Escherichia coli shigatoxinogène (STEC - EHEC)",
        "Bactérie > Escherichia Coli > Escherichia coli shigatoxinogène (STEC - EHEC)",
    )
    LEPTOSPIRA = "Leptospira", "Bactérie > Leptospira"
    LISTERIA = "Listeria", "Bactérie > Listeria"
    LISTERIA_MONOCYTOGENES = "Listeria monocytogenes", "Bactérie > Listeria > Listeria monocytogenes"
    MYCOBACTERIUM = "Mycobacterium", "Bactérie > Mycobacterium"
    MYCOBACTERIUM_BOVIS = "Mycobacterium bovis", "Bactérie > Mycobacterium > Mycobacterium bovis"
    MYCOBACTERIUM_SUIS = "Mycobacterium suis", "Bactérie > Mycobacterium > Mycobacterium suis"
    MYCOBACTERIUM_TUBERCULOSIS = "Mycobacterium tuberculosis", "Bactérie > Mycobacterium > Mycobacterium tuberculosis"
    PSEUDOMONAS = "Pseudomonas", "Bactérie > Pseudomonas"
    SALMONELLA = "Salmonella", "Bactérie > Salmonella"
    AUTRE_SALMONELLA = "Autre salmonella (à préciser)", "Bactérie > Salmonella > Autre salmonella (à préciser)"
    SALMONELLA_DUBLIN = "Salmonella dublin", "Bactérie > Salmonella > Salmonella dublin"
    SALMONELLA_ENTERITIDIS = "Salmonella enteritidis", "Bactérie > Salmonella > Salmonella enteritidis"
    SALMONELLA_HADAR = "Salmonella hadar", "Bactérie > Salmonella > Salmonella hadar"
    SALMONELLA_INFANTIS = "Salmonella infantis", "Bactérie > Salmonella > Salmonella infantis"
    SALMONELLA_KENTUCKY = "Salmonella kentucky", "Bactérie > Salmonella > Salmonella kentucky"
    SALMONELLA_MBANDAKA = "Salmonella mbandaka", "Bactérie > Salmonella > Salmonella mbandaka"
    SALMONELLA_TYPHIMURIUM = "Salmonella typhimurium", "Bactérie > Salmonella > Salmonella typhimurium"
    SALMONELLA_VIRCHOW = "Salmonella virchow", "Bactérie > Salmonella > Salmonella virchow"
    SHIGELLA = "Shigella", "Bactérie > Shigella"
    STAPHYLOCOCCUS = "Staphylococcus", "Bactérie > Staphylococcus"
    STAPHYLOCOCCUS_AUREUS_ET_OU_SA_TOXINE = (
        "Staphylococcus aureus et/ou sa toxine",
        "Bactérie > Staphylococcus > Staphylococcus aureus et/ou sa toxine",
    )
    VIBRIO = "Vibrio", "Bactérie > Vibrio"
    VIBRIO_CHOLERAE = "Vibrio cholerae", "Bactérie > Vibrio > Vibrio cholerae"
    VIBRIO_PARAHAEMOLYTICUS = "Vibrio parahaemolyticus", "Bactérie > Vibrio > Vibrio parahaemolyticus"
    VIBRIO_VULNIFICUS = "Vibrio vulnificus", "Bactérie > Vibrio > Vibrio vulnificus"
    YERSINIA = "Yersinia", "Bactérie > Yersinia"
    YERSINIA_ENTEROCOLITICA = "Yersinia enterocolitica", "Bactérie > Yersinia > Yersinia enterocolitica"
    AUTRE_CONTAMINANT_DE_L_ENVIRONNEMENT = (
        "Autre contaminant de l'environnement",
        "Contaminant - autre > Autre contaminant de l'environnement",
    )
    BISPHENOL = "Bisphénol (hors MCDA)", "Contaminant - autre > Bisphénol (hors MCDA)"
    MELAMINE = "Mélamine (hors MCDA)", "Contaminant - autre > Mélamine (hors MCDA)"
    NITRATE = "Nitrate (hors additif)", "Contaminant - autre > Nitrate (hors additif)"
    NITRITE = "Nitrite (hors additif)", "Contaminant - autre > Nitrite (hors additif)"
    PERCHLORATE = "Perchlorate", "Contaminant - autre > Perchlorate"
    ARSENIC = "Arsenic (As)", "Contaminant - métauet autre élément > Arsenic (As)"
    AUTRE_ELEMENT_TRACE_METALLIQUE_OU_COMPOSE_INORGANIQUE = (
        "Autre élément trace métallique ou composé inorganique",
        "Contaminant - métauet autre élément > Autre élément trace métallique ou composé inorganique",
    )
    CADMIUM = "Cadmium (Cd)", "Contaminant - métauet autre élément > Cadmium (Cd)"
    FLUOR = "Fluor (F)", "Contaminant - métauet autre élément > Fluor (F)"
    MERCURE = "Mercure (Hg)", "Contaminant - métauet autre élément > Mercure (Hg)"
    NICKEL = "Nickel (Ni)", "Contaminant - métauet autre élément > Nickel (Ni)"
    PLOMB = "Plomb (Pb)", "Contaminant - métauet autre élément > Plomb (Pb)"
    AFLATOXINE = "Aflatoxine", "Contaminant - mycotoxine > Aflatoxine"
    ALTERNARIOL_ALTERNARIOL_MONOMETHYL_ETHER_ACIDE_TENUAZONIQUE = (
        "Alternariol (AOH) Alternariol monométhyl éther (AME) Acide ténuazonique (TeA)",
        "Contaminant - mycotoxine > Alternariol (AOH) Alternariol monométhyl éther (AME) Acide ténuazonique (TeA)",
    )
    AUTRE_MYCOTOXINE_OU_INDETERMINEE = (
        "Autre mycotoxine ou indéterminée",
        "Contaminant - mycotoxine > Autre mycotoxine ou indéterminée",
    )
    CITRININE = "Citrinine", "Contaminant - mycotoxine > Citrinine"
    DEOXYNIVALENOL = "Déoxynivalénol (DON)", "Contaminant - mycotoxine > Déoxynivalénol (DON)"
    FUMONISINE = "Fumonisine", "Contaminant - mycotoxine > Fumonisine"
    OCHRATOXINE_A = "Ochratoxine A", "Contaminant - mycotoxine > Ochratoxine A"
    PATULINE = "Patuline", "Contaminant - mycotoxine > Patuline"
    SCLEROTE_D_ERGOT_ALCALOIDE_DE_L_ERGOT = (
        "Sclérote d'ergot - Alcaloïde de l'ergot",
        "Contaminant - mycotoxine > Sclérote d'ergot - Alcaloïde de l'ergot",
    )
    TOXINE_T2_OU_HT2 = "Toxine T2 ou HT2", "Contaminant - mycotoxine > Toxine T2 ou HT2"
    ZEARALENONE = "Zéaralénone (ZEA)", "Contaminant - mycotoxine > Zéaralénone (ZEA)"
    AUTRE_POLLUANT_ORGANIQUE_PERSISTANT = (
        "Autre polluant organique persistant",
        "Contaminant - polluant organique persistant > Autre polluant organique persistant",
    )
    DIOXINES_ET_PCB = "Dioxines et  PCB", "Contaminant - polluant organique persistant > Dioxines et  PCB"
    PBDE_ET_AUTRE_RETARDATEUR_DE_FLAMME_BROME = (
        "PBDE et autre retardateur de flamme bromé",
        "Contaminant - polluant organique persistant > PBDE et autre retardateur de flamme bromé",
    )
    SUBSTANCES_PERFLUOROALKYLEES = (
        "Substances perfluoroalkylées (PFAS)",
        "Contaminant - polluant organique persistant > Substances perfluoroalkylées (PFAS)",
    )
    MCPD_ET_ESTER_D_ACIDE_GRAS_DE_3_MCPD = (
        "3MCPD et ester d'acide gras de 3-MCPD",
        "Contaminant - procédé de transformation > 3MCPD et ester d'acide gras de 3-MCPD",
    )
    AAH = "AAH", "Contaminant - procédé de transformation > AAH"
    ACRYLAMIDE = "Acrylamide", "Contaminant - procédé de transformation > Acrylamide"
    AUTRE_CONTAMINANT_DES_PROCEDES = (
        "Autre contaminant des procédés",
        "Contaminant - procédé de transformation > Autre contaminant des procédés",
    )
    ESTER_D_ACIDE_GRAS_DE_GLYCIDOL = (
        "Ester d'acide gras de glycidol",
        "Contaminant - procédé de transformation > Ester d'acide gras de glycidol",
    )
    FURANE_ET_DERIVE_METHYLE_DU_FURANE = (
        "Furane et dérivé méthylé du furane",
        "Contaminant - procédé de transformation > Furane et dérivé méthylé du furane",
    )
    HAP = "HAP", "Contaminant - procédé de transformation > HAP"
    HYDROCARBURE_D_HUILE_MINERALE = (
        "Hydrocarbure d'huile minérale (MOAH et MOSH)",
        "Contaminant - procédé de transformation > Hydrocarbure d'huile minérale (MOAH et MOSH)",
    )
    NITROSAMINE = "Nitrosamine", "Contaminant - procédé de transformation > Nitrosamine"
    PHYCOTOXINE_ET_CYANOTOXINE = (
        "Phycotoxine et cyanotoxine",
        "Contaminant - toxine végétale > Phycotoxine et cyanotoxine",
    )
    AUTRE_PHYCOTOXINE_ET_CYANOTOXINE = (
        "Autre phycotoxine et cyanotoxine",
        "Contaminant - toxine végétale > Phycotoxine et cyanotoxine > Autre phycotoxine et cyanotoxine",
    )
    CIGUATOXINE = "Ciguatoxine", "Contaminant - toxine végétale > Phycotoxine et cyanotoxine > Ciguatoxine"
    HISTAMINE = "Histamine", "Contaminant - toxine végétale > Phycotoxine et cyanotoxine > Histamine"
    TOXINE_ASP = "Toxine ASP", "Contaminant - toxine végétale > Phycotoxine et cyanotoxine > Toxine ASP"
    TOXINE_DSP = (
        "Toxine DSP (toxines lipophiles)",
        "Contaminant - toxine végétale > Phycotoxine et cyanotoxine > Toxine DSP (toxines lipophiles)",
    )
    TOXINE_PSP = "Toxine PSP", "Contaminant - toxine végétale > Phycotoxine et cyanotoxine > Toxine PSP"
    PHYTO_ESTROGENE = "Phyto-estrogène", "Contaminant - toxine végétale > Phyto-estrogène"
    TOXINE_VEGETALE_AUTRE = "Toxine végétale autre", "Contaminant - toxine végétale > Toxine végétale autre"
    AUTRE_TOXINE_VEGETALE_OU_PLANTE_EN_CONTENANT = (
        "Autre toxine végétale ou plante en contenant",
        "Contaminant - toxine végétale > Toxine végétale autre > Autre toxine végétale ou plante en contenant",
    )
    BETTERAVE_CRUE_TOXINE_INDETERMINEE = (
        "Betterave crue : toxine indéterminée",
        "Contaminant - toxine végétale > Toxine végétale autre > Betterave crue : toxine indéterminée",
    )
    CHAMPIGNON_TOXIQUE_OU_VENENEU = (
        "Champignon toxique ou vénéneu(amanite, divers)",
        "Contaminant - toxine végétale > Toxine végétale autre > Champignon toxique ou vénéneu(amanite, divers)",
    )
    CUCURBITACINE_ET_AUTRES_TOXINES_DE_COURGES = (
        "Cucurbitacine et autres toxines de courges",
        "Contaminant - toxine végétale > Toxine végétale autre > Cucurbitacine et autres toxines de courges",
    )
    GOSSYPOL = "Gossypol", "Contaminant - toxine végétale > Toxine végétale autre > Gossypol"
    PIGNON_DE_PIN_AMER = (
        "Pignon de pin amer (dysgueusie)",
        "Contaminant - toxine végétale > Toxine végétale autre > Pignon de pin amer (dysgueusie)",
    )
    THEOBROMINE = "Théobromine", "Contaminant - toxine végétale > Toxine végétale autre > Théobromine"
    TOXINE_VEGETALE_REGLEMENTEE = (
        "Toxine végétale réglementée",
        "Contaminant - toxine végétale > Toxine végétale réglementée",
    )
    ACIDE_CYANHYDRIQUE = (
        "Acide cyanhydrique",
        "Contaminant - toxine végétale > Toxine végétale réglementée > Acide cyanhydrique",
    )
    ACIDE_ERUCIQUE = "Acide érucique", "Contaminant - toxine végétale > Toxine végétale réglementée > Acide érucique"
    ALCALOIDE_OPIOIDE = (
        "Alcaloïde opioïde",
        "Contaminant - toxine végétale > Toxine végétale réglementée > Alcaloïde opioïde",
    )
    ALCALOIDE_PYRROLIZIDINIQUE = (
        "Alcaloïde pyrrolizidinique",
        "Contaminant - toxine végétale > Toxine végétale réglementée > Alcaloïde pyrrolizidinique",
    )
    ALCALOIDE_TROPANIQUE_ET_GRAINE_DE_DATURA = (
        "Alcaloïde tropanique (Datura) et graine de Datura",
        "Contaminant - toxine végétale > Toxine végétale réglementée > Alcaloïde tropanique (Datura) et graine de Datura",
    )
    DELTA_9_THC = (
        "Delta-9-THC (<=0,3%)",
        "Contaminant - toxine végétale > Toxine végétale réglementée > Delta-9-THC (<=0,3%)",
    )
    GLYCOALCALOIDE = "Glycoalcaloïde", "Contaminant - toxine végétale > Toxine végétale réglementée > Glycoalcaloïde"
    AUTRE_CORPS_ETRANGER_OU_INDETERMINE = (
        "Autre corps étranger ou indéterminé",
        "Corps étranger et indésirable > Autre corps étranger ou indéterminé",
    )
    IMPURETE_BOTANIQUE_ESPECE_VEGETALE_NUISIBLE = (
        "Impureté botanique - espèce végétale nuisible (yc Ambroisie)",
        "Corps étranger et indésirable > Impureté botanique - espèce végétale nuisible (yc Ambroisie)",
    )
    INSECTE_VERS_RONGEUR_AUTRE_ANIMAL_INDESIRABLE = (
        "Insecte - vers - rongeur - autre animal indésirable",
        "Corps étranger et indésirable > Insecte - vers - rongeur - autre animal indésirable",
    )
    VERRE_CAILLOUX_METAL_OS_AUTRE_BLESSANT = (
        "Verre - cailloux - métal - os - autre blessant",
        "Corps étranger et indésirable > Verre - cailloux - métal - os - autre blessant",
    )
    ACTIVITE_INTERDITE = (
        "Activité interdite (mesure administrative)",
        "Etablissement - activité non autorisée > Activité interdite (mesure administrative)",
    )
    ACTIVITE_NON_AGREEE = (
        "Activité non agréée (défaut d'agrément)",
        "Etablissement - activité non autorisée > Activité non agréée (défaut d'agrément)",
    )
    AUTRE_ACTIVITE_NON_AUTORISEE = (
        "Autre activité non autorisée",
        "Etablissement - activité non autorisée > Autre activité non autorisée",
    )
    IRRADIATION_IONISATION_NON_AUTORISEE = (
        "Irradiation Ionisation non autorisée",
        "Etablissement - activité non autorisée > Irradiation Ionisation non autorisée",
    )
    NON_PRESENTATION_A_UN_CONTROLE_OBLIGATOIRE = (
        'Non présentation à un contrôle obligatoire (yc "tout droit")',
        'Etablissement - activité non autorisée > Non présentation à un contrôle obligatoire (yc "tout droit")',
    )
    ANOMALIE_DOCUMENTAIRE_SOUS_PRODUIT_ANIMAL = (
        "Anomalie documentaire sous-produit animal (DAC, DOCOM, CS)",
        "Etablissement - perte de maîtrise sanitaire > Anomalie documentaire sous-produit animal (DAC, DOCOM, CS)",
    )
    AUTRE_PERTE_DE_MAITRISE_SANITAIRE = (
        "Autre perte de maîtrise sanitaire",
        "Etablissement - perte de maîtrise sanitaire > Autre perte de maîtrise sanitaire",
    )
    DEFAUT_DE_COMPOSITION = (
        "Défaut de composition (sauf allergène)",
        "Etablissement - perte de maîtrise sanitaire > Défaut de composition (sauf allergène)",
    )
    DEFAUT_DE_PASTEURISATION = (
        "Défaut de pasteurisation",
        "Etablissement - perte de maîtrise sanitaire > Défaut de pasteurisation",
    )
    DEFAUT_DE_STERILISATION = (
        "Défaut de stérilisation",
        "Etablissement - perte de maîtrise sanitaire > Défaut de stérilisation",
    )
    DEFAUT_DE_TRACABILITE = (
        "Défaut de traçabilité",
        "Etablissement - perte de maîtrise sanitaire > Défaut de traçabilité",
    )
    DEFAUT_DU_CONDITIONNEMENT = (
        "Défaut du conditionnement (herméticité, gaz…)",
        "Etablissement - perte de maîtrise sanitaire > Défaut du conditionnement (herméticité, gaz…)",
    )
    DEFAUT_ORGANOLEPTIQUE = (
        "Défaut organoleptique (toute cause)",
        "Etablissement - perte de maîtrise sanitaire > Défaut organoleptique (toute cause)",
    )
    FEED_ANIMAL_NON_CIBLE = (
        "Feed - animal non-cible (contamination)",
        "Etablissement - perte de maîtrise sanitaire > Feed - animal non-cible (contamination)",
    )
    IONISATION_NON_CONFORME = (
        "Ionisation non conforme (hors étiquetage)",
        "Etablissement - perte de maîtrise sanitaire > Ionisation non conforme (hors étiquetage)",
    )
    MAUVAISES_CONDITIONS_D_HYGIENE_RISQUES_DE_CONTAMINATION = (
        "Mauvaises conditions d'hygiène, risques de contamination",
        "Etablissement - perte de maîtrise sanitaire > Mauvaises conditions d'hygiène, risques de contamination",
    )
    RUPTURE_DE_LA_CHAINE_DU_FROID = (
        "Rupture de la chaîne du froid",
        "Etablissement - perte de maîtrise sanitaire > Rupture de la chaîne du froid",
    )
    AUTRE_ETIQUETAGE_OU_INDETERMINE = (
        "Autre étiquetage ou indéterminé (hors allergène)",
        "Etiquetage > Autre étiquetage ou indéterminé (hors allergène)",
    )
    ETIQUETAGE_ALLEGATION = "Etiquetage / allégation", "Etiquetage > Etiquetage / allégation"
    ETIQUETAGE_COMPOSITION = (
        "Etiquetage / composition (hors allergène)",
        "Etiquetage > Etiquetage / composition (hors allergène)",
    )
    ETIQUETAGE_DLC = "Etiquetage / DLC", "Etiquetage > Etiquetage / DLC"
    ETIQUETAGE_IONISATION = "Etiquetage / ionisation", "Etiquetage > Etiquetage / ionisation"
    ETIQUETAGE_MODE_D_EMPLOI_MENTION_DE_BON_USAGE = (
        "Etiquetage / mode d'emploi / mention de bon usage",
        "Etiquetage > Etiquetage / mode d'emploi / mention de bon usage",
    )
    ETIQUETAGE_TEMPERATURE_DE_CONSERVATION = (
        "Etiquetage / température de conservation",
        "Etiquetage > Etiquetage / température de conservation",
    )
    ADDITIF = "Additif", "Ingrédient - additif et auxilliaire technologique > Additif"
    ADDITIF_NITRE = (
        "Additif - nitré (nitrate/nitrite)",
        "Ingrédient - additif et auxilliaire technologique > Additif > Additif - nitré (nitrate/nitrite)",
    )
    ADDITIF_NON_RESPECT_CATEGORIE_DENREE_AMM = (
        "Additif - non-respect catégorie denrée / AMM",
        "Ingrédient - additif et auxilliaire technologique > Additif > Additif - non-respect catégorie denrée / AMM",
    )
    ADDITIF_NON_RESPECT_DOSAGE_AMM = (
        "Additif - non-respect dosage / AMM",
        "Ingrédient - additif et auxilliaire technologique > Additif > Additif - non-respect dosage / AMM",
    )
    ADDITIF_SULFITE = (
        "Additif - sulfite",
        "Ingrédient - additif et auxilliaire technologique > Additif > Additif - sulfite",
    )
    AUTRE_ADDITIF = (
        "Autre additif (yc additif non autorisé en UE)",
        "Ingrédient - additif et auxilliaire technologique > Additif > Autre additif (yc additif non autorisé en UE)",
    )
    RESIDU_D_ADDITIF_FEED = (
        "Résidu d'additif feed (yc coccidiostatique, histomonostatique)",
        "Ingrédient - additif et auxilliaire technologique > Additif > Résidu d'additif feed (yc coccidiostatique, histomonostatique)",
    )
    ADDITIF_FEED = "Additif - Feed", "Ingrédient - additif et auxilliaire technologique > Additif - Feed"
    FEED_ADDITIF_NON_AUTORISE = (
        "Feed - additif non autorisé",
        "Ingrédient - additif et auxilliaire technologique > Additif - Feed > Feed - additif non autorisé",
    )
    FEED_NON_RESPECT_CONDITION_D_AUTORISATION = (
        "Feed - non-respect condition d'autorisation",
        "Ingrédient - additif et auxilliaire technologique > Additif - Feed > Feed - non-respect condition d'autorisation",
    )
    AUXILLIAIRE_TECHNOLOGIQUE = (
        "Auxilliaire technologique",
        "Ingrédient - additif et auxilliaire technologique > Auxilliaire technologique",
    )
    NON_RESPECT_CATEGORIE_DENREE_DOMAINE_D_APPLICATION = (
        "Non-respect catégorie denrée / domaine d'application",
        "Ingrédient - additif et auxilliaire technologique > Auxilliaire technologique > Non-respect catégorie denrée / domaine d'application",
    )
    NON_RESPECT_CONDITION_D_EMPLOI_DOSE_RESIDUELLE = (
        "Non-respect condition d'emploi / dose résiduelle",
        "Ingrédient - additif et auxilliaire technologique > Auxilliaire technologique > Non-respect condition d'emploi / dose résiduelle",
    )
    RESIDU_D_AUXILLIAIRE_TECHNOLOGIQUE_ET_IMPURETE_ISSUE = (
        "Résidu d'auxilliaire technologique et impureté issue",
        "Ingrédient - additif et auxilliaire technologique > Auxilliaire technologique > Résidu d'auxilliaire technologique et impureté issue",
    )
    ENZYME = "Enzyme", "Ingrédient - additif et auxilliaire technologique > Enzyme"
    COMPLEMENT_ALIMENTAIRE_NON_TELEDECLARE = (
        "Complément alimentaire non télédéclaré",
        "Ingrédient - non autorisé ou dangereux > Complément alimentaire non télédéclaré",
    )
    DECHET_PRODUIT_TECHNIQUE_NON_ALIMENTAIRE = (
        "Déchet, produit technique non-alimentaire (yc feed)",
        "Ingrédient - non autorisé ou dangereux > Déchet, produit technique non-alimentaire (yc feed)",
    )
    FEED_MP_INTERDITE = "Feed - MP interdite", "Ingrédient - non autorisé ou dangereux > Feed - MP interdite"
    FEED_AUTRE_MP_INTERDITE = (
        "Feed - autre MP interdite",
        "Ingrédient - non autorisé ou dangereux > Feed - MP interdite > Feed - autre MP interdite",
    )
    FEED_EMBALLAGE_DE_PRODUIT_DES_IAA = (
        "Feed - emballage de produit des IAA",
        "Ingrédient - non autorisé ou dangereux > Feed - MP interdite > Feed - emballage de produit des IAA",
    )
    FEED_SEMENCE_OU_PLANT_TRAITE_ET_DERIVE = (
        "Feed - semence ou plant traité et dérivé",
        "Ingrédient - non autorisé ou dangereux > Feed - MP interdite > Feed - semence ou plant traité et dérivé",
    )
    FEED_SOUS_PRODUIT_ANIMAL = (
        "Feed - sous-produit animal",
        "Ingrédient - non autorisé ou dangereux > Feed - sous-produit animal",
    )
    FEED_PRODUIT_ANIMAL_INTERDIT_FEED_BAN = (
        "Feed - Produit animal interdit / feed ban (yc PAT)",
        "Ingrédient - non autorisé ou dangereux > Feed - sous-produit animal > Feed - Produit animal interdit / feed ban (yc PAT)",
    )
    FEED_SPAN_DE_CATEGORIE_1_OU_2 = (
        "Feed - SPAn de catégorie 1 ou 2",
        "Ingrédient - non autorisé ou dangereux > Feed - sous-produit animal > Feed - SPAn de catégorie 1 ou 2",
    )
    FEED_SPAN_DE_CATEGORIE_3_NON_CONFORME = (
        "Feed - SPAn de catégorie 3 non-conforme",
        "Ingrédient - non autorisé ou dangereux > Feed - sous-produit animal > Feed - SPAn de catégorie 3 non-conforme",
    )
    NOVEL_FOOD = "Novel food", "Ingrédient - non autorisé ou dangereux > Novel food"
    NF_CBD_AUTRES_CANNABINOIDES = (
        "NF - CBD/autres cannabinoïdes",
        "Ingrédient - non autorisé ou dangereux > Novel food > NF - CBD/autres cannabinoïdes",
    )
    NF_NON_RESPECT_CATEGORIE_DENREE_AMM = (
        "NF - non-respect catégorie denrée / AMM",
        "Ingrédient - non autorisé ou dangereux > Novel food > NF - non-respect catégorie denrée / AMM",
    )
    NF_NON_RESPECT_POPULATION_CIBLE_AMM = (
        "NF - non-respect population cible / AMM",
        "Ingrédient - non autorisé ou dangereux > Novel food > NF - non-respect population cible / AMM",
    )
    NF_SURDOSAGE_AMM = "NF - surdosage/AMM", "Ingrédient - non autorisé ou dangereux > Novel food > NF - surdosage/AMM"
    OGM = "OGM", "Ingrédient - non autorisé ou dangereux > OGM"
    ANIMAL_GM = "Animal GM", "Ingrédient - non autorisé ou dangereux > OGM > Animal GM"
    MICROORGANISME_GM = "Microorganisme GM", "Ingrédient - non autorisé ou dangereux > OGM > Microorganisme GM"
    PLANTE_GM = "Plante GM", "Ingrédient - non autorisé ou dangereux > OGM > Plante GM"
    SOUS_PRODUIT_ANIMAL_EN_ALIMENTATION_HUMAINE = (
        "Sous-produit animal en alimentation humaine",
        "Ingrédient - non autorisé ou dangereux > Sous-produit animal en alimentation humaine",
    )
    STUPEFIANT_ET_PSYCHOACTIF = (
        "Stupéfiant et psychoactif",
        "Ingrédient - non autorisé ou dangereux > Stupéfiant et psychoactif",
    )
    PSYCHOACTIF = (
        "Psychoactif (hors médicament, stupéfiant, novel food)",
        "Ingrédient - non autorisé ou dangereux > Stupéfiant et psychoactif > Psychoactif (hors médicament, stupéfiant, novel food)",
    )
    STUPEFIANT = (
        "Stupéfiant (dont THC>0,3%)",
        "Ingrédient - non autorisé ou dangereux > Stupéfiant et psychoactif > Stupéfiant (dont THC>0,3%)",
    )
    SUBSTANCE_INTERDITE_OU_RESTRICTION_DENREE_ENRICHIE_OU_COMPLEMENT_ALIMENTAIRE = (
        "Substance interdite ou restriction / denrée enrichie ou complément alimentaire",
        "Ingrédient - non autorisé ou dangereux > Substance interdite ou restriction / denrée enrichie ou complément alimentaire",
    )
    SUBSTANCE_MEDICAMENTEUSE = (
        "Substance médicamenteuse",
        "Ingrédient - non autorisé ou dangereux > Substance médicamenteuse",
    )
    AUTRE_SUBSTANCE_MEDICAMENTEUSE = (
        "Autre substance médicamenteuse",
        "Ingrédient - non autorisé ou dangereux > Substance médicamenteuse > Autre substance médicamenteuse",
    )
    SIBUTRAMINE = "Sibutramine", "Ingrédient - non autorisé ou dangereux > Substance médicamenteuse > Sibutramine"
    SILDENAFIL = "Sildénafil", "Ingrédient - non autorisé ou dangereux > Substance médicamenteuse > Sildénafil"
    SURDOSAGE_NUTRIMENT_DENREE_ENRICHIE_OU_COMPLEMENT_ALIMENTAIRE = (
        "Surdosage nutriment / denrée enrichie ou complément alimentaire",
        "Ingrédient - non autorisé ou dangereux > Surdosage nutriment / denrée enrichie ou complément alimentaire",
    )
    LEVURE_MOISISSURE_DIVERS_OU_INDETERMINEE = (
        "Levure Moisissure divers ou indéterminée",
        "Levure Moisissure > Levure Moisissure divers ou indéterminée",
    )
    AUTRE_RESIDU_MV_OU_INDETERMINE = (
        "Autre résidu MV ou indéterminé (hors additif coccidiostatique et histomonostatique)",
        "Médicament vétérinaire > Autre résidu MV ou indéterminé (hors additif coccidiostatique et histomonostatique)",
    )
    FEED_MV_ANIMAL_NON_CIBLE = "Feed - MV - animal non-cible", "Médicament vétérinaire > Feed - MV - animal non-cible"
    FEED_MV_NON_RESPECT_DOSE_ALIMENT_MEDICAMENTEUX = (
        "Feed - MV - non-respect dose / aliment médicamenteux",
        "Médicament vétérinaire > Feed - MV - non-respect dose / aliment médicamenteux",
    )
    RESIDU_MV_GROUPE_A_SUBSTANCE_INTERDITE_OU_NON_AUTORISEE_TRAITEMENT_ILLEGAL = (
        "Résidu MV - Groupe A - substance interdite ou non autorisée, traitement illégal",
        "Médicament vétérinaire > Résidu MV - Groupe A - substance interdite ou non autorisée, traitement illégal",
    )
    AUTRE_RESIDU_MV_INTERDIT_OU_NON_AUTORISE = (
        "Autre - Résidu MV interdit ou non autorisé",
        "Médicament vétérinaire > Résidu MV - Groupe A - substance interdite ou non autorisée, traitement illégal > Autre - Résidu MV interdit ou non autorisé",
    )
    RESIDU_MV_SUBSTANCES_A_EFFET_HORMONAL_ET_THYREOSTATIQUE_ET_BETA_AGONISTES = (
        "Résidu MV - Substances à effet hormonal et thyréostatique et béta-agonistes",
        "Médicament vétérinaire > Résidu MV - Groupe A - substance interdite ou non autorisée, traitement illégal > Résidu MV - Substances à effet hormonal et thyréostatique et béta-agonistes",
    )
    RESIDU_MV_GROUPE_B_SUBSTANCE_AUTORISEE = (
        "Résidu MV - Groupe B - substance autorisée",
        "Médicament vétérinaire > Résidu MV - Groupe B - substance autorisée",
    )
    ALARIA_ALATA = "Alaria alata", "Parasite > Alaria alata"
    ANISAKIS = "Anisakis", "Parasite > Anisakis"
    AUTRE_PARASITE_OU_INDETERMINE = "Autre parasite ou indéterminé", "Parasite > Autre parasite ou indéterminé"
    CLINOSTOMUM_COMPLANATUM = "Clinostomum complanatum", "Parasite > Clinostomum complanatum"
    DIPHYLLOBOTHRIUM = "Diphyllobothrium", "Parasite > Diphyllobothrium"
    ECHINOCOCCUS = "Echinococcus", "Parasite > Echinococcus"
    PSEUDOTERRANOVA = "Pseudoterranova", "Parasite > Pseudoterranova"
    TOXACARA = "Toxacara", "Parasite > Toxacara"
    TOXOPLASMA = "Toxoplasma", "Parasite > Toxoplasma"
    TRICHINE = "Trichine", "Parasite > Trichine"
    RESIDU_DE_PESTICIDE_BIOCIDE = "Résidu de Pesticide Biocide", "Pesticide biocide > Résidu de Pesticide Biocide"
    AUTRE_PRION_OU_INDETERMINE = "Autre prion ou indéterminé", "Prion > Autre prion ou indéterminé"
    ENCEPHALOPATHIE_SPONGIFORME_BOVINE = (
        "Encéphalopathie spongiforme bovine",
        "Prion > Encéphalopathie spongiforme bovine",
    )
    TREMBLANTE = "Tremblante", "Prion > Tremblante"
    RADIONUCLEIDE = "Radionucléide", "Radionucléide > Radionucléide"
    MCDA_AUTRE_CONTAMINANT = "MCDA - Autre contaminant", "Substance migrante - MCDA > MCDA - Autre contaminant"
    MCDA_AUTRE_PERTURBATEUR_ENDOCRINIEN = (
        "MCDA - Autre perturbateur endocrinien (hors bisphénol)",
        "Substance migrante - MCDA > MCDA - Autre perturbateur endocrinien (hors bisphénol)",
    )
    MCDA_BISPHENOL = (
        "MCDA - Bisphénol (hors contaminant)",
        "Substance migrante - MCDA > MCDA - Bisphénol (hors contaminant)",
    )
    MCDA_COBALT = "MCDA - Cobalt", "Substance migrante - MCDA > MCDA - Cobalt"
    MCDA_FORMALDEHYDE = "MCDA - Formaldéhyde", "Substance migrante - MCDA > MCDA - Formaldéhyde"
    MCDA_MELAMINE = (
        "MCDA - Mélamine (hors contaminant)",
        "Substance migrante - MCDA > MCDA - Mélamine (hors contaminant)",
    )
    MCDA_PHTALATES = "MCDA - Phtalates", "Substance migrante - MCDA > MCDA - Phtalates"
    AUTRE_VIRUS_ALIMENTAIRE_OU_INDETERMINE = (
        "Autre virus alimentaire ou indéterminé",
        "Virus > Autre virus alimentaire ou indéterminé",
    )
    VIRUS_DE_LA_GASTROENTERITE_AIGUE = (
        "Virus de la gastroentérite aigüe (GEA) (Calicivirus, Norovirus, Sapovirus, Rotavirus, Astrovirus, Adénovirus)",
        "Virus > Virus de la gastroentérite aigüe (GEA) (Calicivirus, Norovirus, Sapovirus, Rotavirus, Astrovirus, Adénovirus)",
    )
    VIRUS_DE_L_ENCEPHALITE_A_TIQUE = (
        "Virus de l'encéphalite à tique (TBEV)",
        "Virus > Virus de l'encéphalite à tique (TBEV)",
    )
    VIRUS_DE_L_HEPATITE_A = "Virus de l'hépatite A (VHA)", "Virus > Virus de l'hépatite A (VHA)"
    VIRUS_DE_L_HEPATITE_E = "Virus de l'hépatite E (VHE)", "Virus > Virus de l'hépatite E (VHE)"
    VIRUS_INFLUENZA_ZOONOTIQUE_PAR_VOIE_ALIMENTAIRE = (
        "Virus influenza zoonotique par voie alimentaire (IAHP zoo)",
        "Virus > Virus influenza zoonotique par voie alimentaire (IAHP zoo)",
    )
    VIRUS_NIPAH = "Virus Nipah", "Virus > Virus Nipah"
    ENTEROVIRUS = "Entérovirus", "Virus > Entérovirus"
    SA_AUTRE_EN_SANTE_ANIMALE = "SA - Autre en santé animale", "x Santé animale > SA - Autre en santé animale"
    SA_FIEVRE_APHTEUSE = "SA - Fièvre aphteuse", "x Santé animale > SA - Fièvre aphteuse"
    SA_INFLUENZA_AVIAIRE_HAUTEMENT_PATHOGENE = (
        "SA - Influenza aviaire hautement pathogène",
        "x Santé animale > SA - Influenza aviaire hautement pathogène",
    )
    SA_PESTE_PORCINE_AFRICAINE = "SA - Peste porcine africaine", "x Santé animale > SA - Peste porcine africaine"
    SA_PESTE_PORCINE_CLASSIQUE = "SA - Peste porcine classique", "x Santé animale > SA - Peste porcine classique"
    SV_ORGANISME_DE_QUARANTAINE = "SV - Organisme de quarantaine", "x Santé végétale > SV - Organisme de quarantaine"

    @classmethod
    def dangers_bacteriens(cls):
        return [choice.value for choice in cls if choice.label.startswith("Bactérie >")]
