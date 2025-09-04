from django.db import models
from .mixins import WithChoicesToJS


class CategorieProduit(WithChoicesToJS, models.TextChoices):
    FROMAGE_AU_LAIT_CRU = "Fromage au lait cru", "Produit laitier > Fromage au lait cru"
    FROMAGE_LAIT_CRU_A_PATES_FRAICHES = (
        "Fromage lait cru à pâtes fraiches (caillé, fromage blanc, faisselle, tomme fraiche, brousse…)",
        "Produit laitier > Fromage au lait cru > Fromage lait cru à pâtes fraiches (caillé, fromage blanc, faisselle, tomme fraiche, brousse…)",
    )
    FROMAGE_LAIT_CRU_A_PATES_LACTIQUES = (
        "Fromage lait cru à pâtes lactiques (chèvre frais, cendré, affiné, chaource, neuchatel...)",
        "Produit laitier > Fromage au lait cru > Fromage lait cru à pâtes lactiques (chèvre frais, cendré, affiné, chaource, neuchatel...)",
    )
    FROMAGE_LAIT_CRU_A_PATES_MOLLES_A_CROUTE_FLEURIE = (
        "Fromage lait cru à pâtes molles à croûte fleurie (camembert, brie…)",
        "Produit laitier > Fromage au lait cru > Fromage lait cru à pâtes molles à croûte fleurie (camembert, brie…)",
    )
    FROMAGE_LAIT_CRU_A_PATES_MOLLES_A_CROUTE_LAVEE = (
        "Fromage lait cru à pâtes molles à croûte lavée (munster, pont-lévêque…)",
        "Produit laitier > Fromage au lait cru > Fromage lait cru à pâtes molles à croûte lavée (munster, pont-lévêque…)",
    )
    FROMAGE_LAIT_CRU_A_PATES_PRESSEES_NON_CUITES = (
        "Fromage lait cru à pâtes pressées non cuites (reblochon, saint-nectaire, cantal, ossau-iraty…)",
        "Produit laitier > Fromage au lait cru > Fromage lait cru à pâtes pressées non cuites (reblochon, saint-nectaire, cantal, ossau-iraty…)",
    )
    FROMAGE_LAIT_CRU_A_PATES_PRESSEES_CUITES = (
        "Fromage lait cru à pâtes pressées cuites (comté, gruyère, emmental, parmesan…)",
        "Produit laitier > Fromage au lait cru > Fromage lait cru à pâtes pressées cuites (comté, gruyère, emmental, parmesan…)",
    )
    FROMAGE_AU_LAIT_TRAITE_OU_TRANSFORME = (
        "Fromage au lait traité ou transformé",
        "Produit laitier > Fromage au lait traité ou transformé",
    )
    FROMAGE_LAIT_TRAITE = (
        "Fromage lait traité (microfiltré, pasteurisé, stérilisé)",
        "Produit laitier > Fromage au lait traité ou transformé > Fromage lait traité (microfiltré, pasteurisé, stérilisé)",
    )
    FROMAGE_FONDU_TARTINADE_ET_AUTRE = (
        "Fromage fondu, tartinade et autre (cancoillotte...)",
        "Produit laitier > Fromage au lait traité ou transformé > Fromage fondu, tartinade et autre (cancoillotte...)",
    )
    FROMAGE_INDETERMINE = "Fromage indéterminé", "Produit laitier > Fromage indéterminé"
    YAOURT_ET_PRODUIT_LAITIER_FERMENTE = (
        "Yaourt et produit laitier fermenté",
        "Produit laitier > Yaourt et produit laitier fermenté",
    )
    YAOURT = "Yaourt", "Produit laitier > Yaourt et produit laitier fermenté > Yaourt"
    LAIT_FERMENTE_BOISSON_LACTEE_FERMENTEE_KEFIR_DE_LAIT = (
        "Lait fermenté, boisson lactée fermentée, kefir de lait",
        "Produit laitier > Yaourt et produit laitier fermenté > Lait fermenté, boisson lactée fermentée, kefir de lait",
    )
    MATIERE_GRASSE_DU_LAIT = "Matière grasse du lait", "Produit laitier > Matière grasse du lait"
    CREME_CRUE = "Crème crue", "Produit laitier > Matière grasse du lait > Crème crue"
    CREME_TRAITEE = (
        "Crème traitée (pasteurisée, stérilisée)",
        "Produit laitier > Matière grasse du lait > Crème traitée (pasteurisée, stérilisée)",
    )
    BEURRE_CRU = "Beurre cru", "Produit laitier > Matière grasse du lait > Beurre cru"
    BEURRE_TRAITE_ET_MGLA = (
        "Beurre traité (pasteurisé, stérilisé) et MGLA",
        "Produit laitier > Matière grasse du lait > Beurre traité (pasteurisé, stérilisé) et MGLA",
    )
    LAIT = "Lait", "Produit laitier > Lait"
    LAIT_CRU = (
        "Lait cru (matière première ou de consommation)",
        "Produit laitier > Lait > Lait cru (matière première ou de consommation)",
    )
    LAIT_TRAITE = (
        "Lait traité (microfiltré, pasteurisé, stérilisé) (hors infantile)",
        "Produit laitier > Lait > Lait traité (microfiltré, pasteurisé, stérilisé) (hors infantile)",
    )
    POUDRE_DE_LAIT_ET_DERIVES = (
        "Poudre de lait et dérivés (poudre de lactosérum, caséïne, lactose, minéraux...) (hors infantile)",
        "Produit laitier > Lait > Poudre de lait et dérivés (poudre de lactosérum, caséïne, lactose, minéraux...) (hors infantile)",
    )
    CONCENTRE_LAITIER = "Concentré laitier", "Produit laitier > Lait > Concentré laitier"
    LACTOSERUM_LIQUIDE = "Lactosérum liquide", "Produit laitier > Lactosérum liquide"
    CARCASSE_VIANDE_OS_ET_ABAT_ROUGE = (
        "Carcasse, viande, os et abat rouge",
        "Produit carné > Carcasse, viande, os et abat rouge",
    )
    V_BOVIN = "V - Bovin", "Produit carné > Carcasse, viande, os et abat rouge > V - Bovin"
    V_OVIN = "V - Ovin", "Produit carné > Carcasse, viande, os et abat rouge > V - Ovin"
    V_CAPRIN = "V - Caprin", "Produit carné > Carcasse, viande, os et abat rouge > V - Caprin"
    V_PORCIN = "V - Porcin", "Produit carné > Carcasse, viande, os et abat rouge > V - Porcin"
    V_CHEVALIN = "V - Chevalin", "Produit carné > Carcasse, viande, os et abat rouge > V - Chevalin"
    V_GRAND_GIBIER = (
        "V - Grand gibier (cerf, chevreuil, sanglier…)",
        "Produit carné > Carcasse, viande, os et abat rouge > V - Grand gibier (cerf, chevreuil, sanglier…)",
    )
    V_DE_BOUCHERIE = (
        "V - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
        "Produit carné > Carcasse, viande, os et abat rouge > V - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
    )
    V_VOLAILLE = (
        "V - Volaille (yc autruche)",
        "Produit carné > Carcasse, viande, os et abat rouge > V - Volaille (yc autruche)",
    )
    V_LAPIN = "V - Lapin", "Produit carné > Carcasse, viande, os et abat rouge > V - Lapin"
    V_REPTILE = "V - Reptile", "Produit carné > Carcasse, viande, os et abat rouge > V - Reptile"
    V_DE_VOLAILLE_LAGOMORPHE_OU_REPTILE = (
        "V - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
        "Produit carné > Carcasse, viande, os et abat rouge > V - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
    )
    V_PETIT_GIBIER = (
        "V - Petit gibier (mammifères - lapin, lièvre...)",
        "Produit carné > Carcasse, viande, os et abat rouge > V - Petit gibier (mammifères - lapin, lièvre...)",
    )
    V_PETIT_GIBIER_OISEAUX = (
        "V - Petit gibier (oiseaux - caille, perdrix, faisan...)",
        "Produit carné > Carcasse, viande, os et abat rouge > V - Petit gibier (oiseaux - caille, perdrix, faisan...)",
    )
    V_DE_GIBIER = (
        "V - De gibier (indéterminé ou mélange)",
        "Produit carné > Carcasse, viande, os et abat rouge > V - De gibier (indéterminé ou mélange)",
    )
    VIANDE_HACHEE = "Viande hachée", "Produit carné > Viande hachée"
    VH_BOVIN = "VH - Bovin", "Produit carné > Viande hachée > VH - Bovin"
    VH_OVIN = "VH - Ovin", "Produit carné > Viande hachée > VH - Ovin"
    VH_CAPRIN = "VH - Caprin", "Produit carné > Viande hachée > VH - Caprin"
    VH_PORCIN = "VH - Porcin", "Produit carné > Viande hachée > VH - Porcin"
    VH_CHEVALIN = "VH - Chevalin", "Produit carné > Viande hachée > VH - Chevalin"
    VH_GRAND_GIBIER = (
        "VH - Grand gibier (cerf, chevreuil, sanglier…)",
        "Produit carné > Viande hachée > VH - Grand gibier (cerf, chevreuil, sanglier…)",
    )
    VH_DE_BOUCHERIE = (
        "VH - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
        "Produit carné > Viande hachée > VH - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
    )
    VH_VOLAILLE = "VH - Volaille (yc autruche)", "Produit carné > Viande hachée > VH - Volaille (yc autruche)"
    VH_LAPIN = "VH - Lapin", "Produit carné > Viande hachée > VH - Lapin"
    VH_REPTILE = "VH - Reptile", "Produit carné > Viande hachée > VH - Reptile"
    VH_DE_VOLAILLE_LAGOMORPHE_OU_REPTILE = (
        "VH - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
        "Produit carné > Viande hachée > VH - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
    )
    VH_PETIT_GIBIER = (
        "VH - Petit gibier (mammifères - lapin, lièvre...)",
        "Produit carné > Viande hachée > VH - Petit gibier (mammifères - lapin, lièvre...)",
    )
    VH_PETIT_GIBIER_OISEAUX = (
        "VH - Petit gibier (oiseaux - caille, perdrix, faisan...)",
        "Produit carné > Viande hachée > VH - Petit gibier (oiseaux - caille, perdrix, faisan...)",
    )
    VH_DE_GIBIER = (
        "VH - De gibier (indéterminé ou mélange)",
        "Produit carné > Viande hachée > VH - De gibier (indéterminé ou mélange)",
    )
    VSM_VIANDE_SEPAREE_MECANIQUEMENT = (
        "VSM - viande séparée mécaniquement",
        "Produit carné > VSM - viande séparée mécaniquement",
    )
    VSM_BOVIN = "VSM - Bovin", "Produit carné > VSM - viande séparée mécaniquement > VSM - Bovin"
    VSM_OVIN = "VSM - Ovin", "Produit carné > VSM - viande séparée mécaniquement > VSM - Ovin"
    VSM_CAPRIN = "VSM - Caprin", "Produit carné > VSM - viande séparée mécaniquement > VSM - Caprin"
    VSM_PORCIN = "VSM - Porcin", "Produit carné > VSM - viande séparée mécaniquement > VSM - Porcin"
    VSM_CHEVALIN = "VSM - Chevalin", "Produit carné > VSM - viande séparée mécaniquement > VSM - Chevalin"
    VSM_GRAND_GIBIER = (
        "VSM - Grand gibier (cerf, chevreuil, sanglier…)",
        "Produit carné > VSM - viande séparée mécaniquement > VSM - Grand gibier (cerf, chevreuil, sanglier…)",
    )
    VSM_DE_BOUCHERIE = (
        "VSM - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
        "Produit carné > VSM - viande séparée mécaniquement > VSM - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
    )
    VSM_VOLAILLE = (
        "VSM - Volaille (yc autruche)",
        "Produit carné > VSM - viande séparée mécaniquement > VSM - Volaille (yc autruche)",
    )
    VSM_LAPIN = "VSM - Lapin", "Produit carné > VSM - viande séparée mécaniquement > VSM - Lapin"
    VSM_REPTILE = "VSM - Reptile", "Produit carné > VSM - viande séparée mécaniquement > VSM - Reptile"
    VSM_DE_VOLAILLE_LAGOMORPHE_OU_REPTILE = (
        "VSM - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
        "Produit carné > VSM - viande séparée mécaniquement > VSM - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
    )
    VSM_PETIT_GIBIER = (
        "VSM - Petit gibier (mammifères - lapin, lièvre...)",
        "Produit carné > VSM - viande séparée mécaniquement > VSM - Petit gibier (mammifères - lapin, lièvre...)",
    )
    VSM_PETIT_GIBIER_OISEAUX = (
        "VSM - Petit gibier (oiseaux - caille, perdrix, faisan...)",
        "Produit carné > VSM - viande séparée mécaniquement > VSM - Petit gibier (oiseaux - caille, perdrix, faisan...)",
    )
    VSM_DE_GIBIER = (
        "VSM - De gibier (indéterminé ou mélange)",
        "Produit carné > VSM - viande séparée mécaniquement > VSM - De gibier (indéterminé ou mélange)",
    )
    ABAT_BLANC = (
        "Abat blanc (non cuit, non saumuré si porc)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc)",
    )
    ABATB_BOVIN = "ABATB - Bovin", "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Bovin"
    ABATB_OVIN = "ABATB - Ovin", "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Ovin"
    ABATB_CAPRIN = "ABATB - Caprin", "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Caprin"
    ABATB_PORCIN = "ABATB - Porcin", "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Porcin"
    ABATB_CHEVALIN = "ABATB - Chevalin", "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Chevalin"
    ABATB_GRAND_GIBIER = (
        "ABATB - Grand gibier (cerf, chevreuil, sanglier…)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Grand gibier (cerf, chevreuil, sanglier…)",
    )
    ABATB_DE_BOUCHERIE = (
        "ABATB - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
    )
    ABATB_VOLAILLE = (
        "ABATB - Volaille (yc autruche)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Volaille (yc autruche)",
    )
    ABATB_LAPIN = "ABATB - Lapin", "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Lapin"
    ABATB_REPTILE = "ABATB - Reptile", "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Reptile"
    ABATB_DE_VOLAILLE_LAGOMORPHE_OU_REPTILE = (
        "ABATB - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
    )
    ABATB_PETIT_GIBIER = (
        "ABATB - Petit gibier (mammifères - lapin, lièvre...)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Petit gibier (mammifères - lapin, lièvre...)",
    )
    ABATB_PETIT_GIBIER_OISEAUX = (
        "ABATB - Petit gibier (oiseaux - caille, perdrix, faisan...)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - Petit gibier (oiseaux - caille, perdrix, faisan...)",
    )
    ABATB_DE_GIBIER = (
        "ABATB - De gibier (indéterminé ou mélange)",
        "Produit carné > Abat blanc (non cuit, non saumuré si porc) > ABATB - De gibier (indéterminé ou mélange)",
    )
    BOYAU_TRAITE = "Boyau traité", "Produit carné > Boyau traité"
    PV_PREPARATION_DE_VIANDE = "PV - préparation de viande", "Produit carné > PV - préparation de viande"
    PV_BOVIN = "PV - Bovin", "Produit carné > PV - préparation de viande > PV - Bovin"
    PV_OVIN = "PV - Ovin", "Produit carné > PV - préparation de viande > PV - Ovin"
    PV_CAPRIN = "PV - Caprin", "Produit carné > PV - préparation de viande > PV - Caprin"
    PV_PORCIN = "PV - Porcin", "Produit carné > PV - préparation de viande > PV - Porcin"
    PV_CHEVALIN = "PV - Chevalin", "Produit carné > PV - préparation de viande > PV - Chevalin"
    PV_GRAND_GIBIER = (
        "PV - Grand gibier (cerf, chevreuil, sanglier…)",
        "Produit carné > PV - préparation de viande > PV - Grand gibier (cerf, chevreuil, sanglier…)",
    )
    PV_DE_BOUCHERIE = (
        "PV - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
        "Produit carné > PV - préparation de viande > PV - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
    )
    PV_VOLAILLE = (
        "PV - Volaille (yc autruche)",
        "Produit carné > PV - préparation de viande > PV - Volaille (yc autruche)",
    )
    PV_LAPIN = "PV - Lapin", "Produit carné > PV - préparation de viande > PV - Lapin"
    PV_REPTILE = "PV - Reptile", "Produit carné > PV - préparation de viande > PV - Reptile"
    PV_DE_VOLAILLE_LAGOMORPHE_OU_REPTILE = (
        "PV - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
        "Produit carné > PV - préparation de viande > PV - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
    )
    PV_PETIT_GIBIER = (
        "PV - Petit gibier (mammifères - lapin, lièvre...)",
        "Produit carné > PV - préparation de viande > PV - Petit gibier (mammifères - lapin, lièvre...)",
    )
    PV_PETIT_GIBIER_OISEAUX = (
        "PV - Petit gibier (oiseaux - caille, perdrix, faisan...)",
        "Produit carné > PV - préparation de viande > PV - Petit gibier (oiseaux - caille, perdrix, faisan...)",
    )
    PV_DE_GIBIER = (
        "PV - De gibier (indéterminé ou mélange)",
        "Produit carné > PV - préparation de viande > PV - De gibier (indéterminé ou mélange)",
    )
    PABV_CRU_PRODUIT_A_BASE_DE_VIANDE_CRU = (
        "PABV cru - produit à base de viande cru",
        "Produit carné > PABV cru - produit à base de viande cru",
    )
    PABV_CRU_BOVIN = "PABV cru - Bovin", "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Bovin"
    PABV_CRU_OVIN = "PABV cru - Ovin", "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Ovin"
    PABV_CRU_CAPRIN = "PABV cru - Caprin", "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Caprin"
    PABV_CRU_PORCIN = "PABV cru - Porcin", "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Porcin"
    PABV_CRU_CHEVALIN = (
        "PABV cru - Chevalin",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Chevalin",
    )
    PABV_CRU_GRAND_GIBIER = (
        "PABV cru - Grand gibier (cerf, chevreuil, sanglier…)",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Grand gibier (cerf, chevreuil, sanglier…)",
    )
    PABV_CRU_DE_BOUCHERIE = (
        "PABV cru - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
    )
    PABV_CRU_VOLAILLE = (
        "PABV cru - Volaille (yc autruche)",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Volaille (yc autruche)",
    )
    PABV_CRU_LAPIN = "PABV cru - Lapin", "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Lapin"
    PABV_CRU_REPTILE = (
        "PABV cru - Reptile",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Reptile",
    )
    PABV_CRU_DE_VOLAILLE_LAGOMORPHE_OU_REPTILE = (
        "PABV cru - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
    )
    PABV_CRU_PETIT_GIBIER = (
        "PABV cru - Petit gibier (mammifères - lapin, lièvre...)",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Petit gibier (mammifères - lapin, lièvre...)",
    )
    PABV_CRU_PETIT_GIBIER_OISEAUX = (
        "PABV cru - Petit gibier (oiseaux - caille, perdrix, faisan...)",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - Petit gibier (oiseaux - caille, perdrix, faisan...)",
    )
    PABV_CRU_DE_GIBIER = (
        "PABV cru - De gibier (indéterminé ou mélange)",
        "Produit carné > PABV cru - produit à base de viande cru > PABV cru - De gibier (indéterminé ou mélange)",
    )
    PABV_CUIT_PRODUIT_A_BASE_DE_VIANDE_CUIT = (
        "PABV cuit - produit à base de viande cuit",
        "Produit carné > PABV cuit - produit à base de viande cuit",
    )
    PABV_CUIT_BOVIN = (
        "PABV cuit - Bovin",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Bovin",
    )
    PABV_CUIT_OVIN = "PABV cuit - Ovin", "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Ovin"
    PABV_CUIT_CAPRIN = (
        "PABV cuit - Caprin",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Caprin",
    )
    PABV_CUIT_PORCIN = (
        "PABV cuit - Porcin",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Porcin",
    )
    PABV_CUIT_CHEVALIN = (
        "PABV cuit - Chevalin",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Chevalin",
    )
    PABV_CUIT_GRAND_GIBIER = (
        "PABV cuit - Grand gibier (cerf, chevreuil, sanglier…)",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Grand gibier (cerf, chevreuil, sanglier…)",
    )
    PABV_CUIT_DE_BOUCHERIE = (
        "PABV cuit - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - De boucherie (indéterminé ou mélange) (yc camélidé, bovidé)",
    )
    PABV_CUIT_VOLAILLE = (
        "PABV cuit - Volaille (yc autruche)",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Volaille (yc autruche)",
    )
    PABV_CUIT_LAPIN = (
        "PABV cuit - Lapin",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Lapin",
    )
    PABV_CUIT_REPTILE = (
        "PABV cuit - Reptile",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Reptile",
    )
    PABV_CUIT_DE_VOLAILLE_LAGOMORPHE_OU_REPTILE = (
        "PABV cuit - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - De volaille, lagomorphe ou reptile (indéterminé ou mélange)",
    )
    PABV_CUIT_PETIT_GIBIER = (
        "PABV cuit - Petit gibier (mammifères - lapin, lièvre...)",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Petit gibier (mammifères - lapin, lièvre...)",
    )
    PABV_CUIT_PETIT_GIBIER_OISEAUX = (
        "PABV cuit - Petit gibier (oiseaux - caille, perdrix, faisan...)",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - Petit gibier (oiseaux - caille, perdrix, faisan...)",
    )
    PABV_CUIT_DE_GIBIER = (
        "PABV cuit - De gibier (indéterminé ou mélange)",
        "Produit carné > PABV cuit - produit à base de viande cuit > PABV cuit - De gibier (indéterminé ou mélange)",
    )
    ETAT_DE_TRANSFORMATION_INDETERMINE = (
        "Etat de transformation indéterminé (catégorie à éviter)",
        "Produit carné > Etat de transformation indéterminé (catégorie à éviter)",
    )
    PRODUIT_VIVANT = "Produit vivant", "Produit aquatique > Produit vivant"
    POISSON = "Poisson", "Produit aquatique > Produit vivant > Poisson"
    CEPHALOPODE = "Céphalopode", "Produit aquatique > Produit vivant > Céphalopode"
    COQUILLAGE = (
        "Coquillage (bivalve, gastéropode marin)",
        "Produit aquatique > Produit vivant > Coquillage (bivalve, gastéropode marin)",
    )
    CRUSTACE = "Crustacé", "Produit aquatique > Produit vivant > Crustacé"
    TUNICIER_ECHINODERME = (
        "Tunicier, échinoderme (oursin)",
        "Produit aquatique > Produit vivant > Tunicier, échinoderme (oursin)",
    )
    ESCARGOT = "Escargot", "Produit aquatique > Produit vivant > Escargot"
    GRENOUILLE = "Grenouille", "Produit aquatique > Produit vivant > Grenouille"
    ALGUE = "Algue (macroalgue)", "Produit aquatique > Produit vivant > Algue (macroalgue)"
    MICROALGUE = "Microalgue (spiruline)", "Produit aquatique > Produit vivant > Microalgue (spiruline)"
    PRODUIT_CRU_ENTIER_FILETE_COUPE_OS_PEAU_UF = (
        "Produit cru entier, fileté, coupé, os, peau, œuf",
        "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf",
    )
    PC_POISSON = "PC - Poisson", "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf > PC - Poisson"
    PC_CEPHALOPODE = (
        "PC - Céphalopode",
        "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf > PC - Céphalopode",
    )
    PC_COQUILLAGE = (
        "PC - Coquillage (bivalve, gastéropode marin)",
        "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf > PC - Coquillage (bivalve, gastéropode marin)",
    )
    PC_CRUSTACE = (
        "PC - Crustacé",
        "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf > PC - Crustacé",
    )
    PC_TUNICIER_ECHINODERME = (
        "PC - Tunicier, échinoderme (oursin)",
        "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf > PC - Tunicier, échinoderme (oursin)",
    )
    PC_ESCARGOT = (
        "PC - Escargot",
        "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf > PC - Escargot",
    )
    PC_GRENOUILLE = (
        "PC - Grenouille",
        "Produit aquatique > Produit cru entier, fileté, coupé, os, peau, œuf > PC - Grenouille",
    )
    PRODUIT_FERMENTE_FUME_SALE_MARINE_CUIT = (
        "Produit fermenté, fumé, salé, mariné, cuit",
        "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit",
    )
    PT_POISSON = "PT - Poisson", "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Poisson"
    PT_CEPHALOPODE = (
        "PT - Céphalopode",
        "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Céphalopode",
    )
    PT_COQUILLAGE = (
        "PT - Coquillage (bivalve, gastéropode marin)",
        "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Coquillage (bivalve, gastéropode marin)",
    )
    PT_CRUSTACE = "PT - Crustacé", "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Crustacé"
    PT_TUNICIER_ECHINODERME = (
        "PT - Tunicier, échinoderme (oursin)",
        "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Tunicier, échinoderme (oursin)",
    )
    PT_ESCARGOT = "PT - Escargot", "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Escargot"
    PT_GRENOUILLE = (
        "PT - Grenouille",
        "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Grenouille",
    )
    PT_ALGUE = (
        "PT - Algue (macroalgue)",
        "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Algue (macroalgue)",
    )
    PT_MICROALGUE = (
        "PT - Microalgue (spiruline)",
        "Produit aquatique > Produit fermenté, fumé, salé, mariné, cuit > PT - Microalgue (spiruline)",
    )
    PRODUIT_SEPARE_MECANIQUEMENT = "Produit séparé mécaniquement", "Produit aquatique > Produit séparé mécaniquement"
    PSM_POISSON = "PSM - Poisson", "Produit aquatique > Produit séparé mécaniquement > PSM - Poisson"
    PSM_CEPHALOPODE = "PSM - Céphalopode", "Produit aquatique > Produit séparé mécaniquement > PSM - Céphalopode"
    PSM_COQUILLAGE = (
        "PSM - Coquillage (bivalve, gastéropode marin)",
        "Produit aquatique > Produit séparé mécaniquement > PSM - Coquillage (bivalve, gastéropode marin)",
    )
    PSM_CRUSTACE = "PSM - Crustacé", "Produit aquatique > Produit séparé mécaniquement > PSM - Crustacé"
    PSM_TUNICIER_ECHINODERME = (
        "PSM - Tunicier, échinoderme (oursin)",
        "Produit aquatique > Produit séparé mécaniquement > PSM - Tunicier, échinoderme (oursin)",
    )
    PSM_ESCARGOT = "PSM - Escargot", "Produit aquatique > Produit séparé mécaniquement > PSM - Escargot"
    PSM_GRENOUILLE = "PSM - Grenouille", "Produit aquatique > Produit séparé mécaniquement > PSM - Grenouille"
    OEUF_COQUILLE = "Oeuf coquille", "Produit d'œuf > Oeuf coquille"
    OVOPRODUIT = "Ovoproduit", "Produit d'œuf > Ovoproduit"
    COULE_D_UF_FRAICHE_NON_PASTEURISEE = (
        "Coule d'œuf fraîche non pasteurisée (entier, jaune, blanc)",
        "Produit d'œuf > Ovoproduit > Coule d'œuf fraîche non pasteurisée (entier, jaune, blanc)",
    )
    OEUF_LIQUIDE_PASTEURISE = (
        "Oeuf liquide pasteurisé (jaune, blanc, entier)",
        "Produit d'œuf > Ovoproduit > Oeuf liquide pasteurisé (jaune, blanc, entier)",
    )
    POUDRE_D_OEUF = "Poudre d'oeuf", "Produit d'œuf > Ovoproduit > Poudre d'oeuf"
    OEUFS_DURS_ET_OVOPRODUITS_DURCIS = (
        "Oeufs durs (écalés ou non) et ovoproduits durcis (barre, omelette nature)",
        "Produit d'œuf > Ovoproduit > Oeufs durs (écalés ou non) et ovoproduits durcis (barre, omelette nature)",
    )
    PRODUIT_DE_LA_RUCHE = "Produit de la ruche", "Autre produit animal > Produit de la ruche"
    MIEL = "Miel (hors bonbon, hydromel)", "Autre produit animal > Produit de la ruche > Miel (hors bonbon, hydromel)"
    POLLEN_PROPOLYS_GELEE_ROYALE_RAYON = (
        "Pollen, propolys, gelée royale, rayon",
        "Autre produit animal > Produit de la ruche > Pollen, propolys, gelée royale, rayon",
    )
    PRODUIT_D_INSECTE = "Produit d'insecte", "Autre produit animal > Produit d'insecte"
    COLLAGENE = "Collagène", "Autre produit animal > Collagène"
    GELATINE = "Gélatine (yc capsule)", "Autre produit animal > Gélatine (yc capsule)"
    GRAISSE_ET_FONTE_D_ORIGINE_ANIMALE = (
        "Graisse et fonte d'origine animale (hors beurre et crème)",
        "Autre produit animal > Graisse et fonte d'origine animale (hors beurre et crème)",
    )
    PRODUITS_RAFFINES_D_ORIGINE_ANIMALE = (
        "Produits raffinés d'origine animale (hors complément alimentaire)",
        "Autre produit animal > Produits raffinés d'origine animale (hors complément alimentaire)",
    )
    HUILE_DE_POISSON = (
        "Huile de poisson (hors feed)",
        "Autre produit animal > Produits raffinés d'origine animale (hors complément alimentaire) > Huile de poisson (hors feed)",
    )
    SUBSTITUT_DE_LAIT = "Substitut de lait (hors infantile)", "Analogue végétal > Substitut de lait (hors infantile)"
    SUBSTITUT_DE_FROMAGE = "Substitut de fromage", "Analogue végétal > Substitut de fromage"
    SUBSTITUT_DE_DESSERT_LACTE_DE_YAOURT = (
        "Substitut de dessert lacté, de yaourt",
        "Analogue végétal > Substitut de dessert lacté, de yaourt",
    )
    SUBTITUT_DE_PRODUIT_CARNE = "Subtitut de produit carné", "Analogue végétal > Subtitut de produit carné"
    SUBTITUT_DE_PRODUIT_AQUATIQUE = "Subtitut de produit aquatique", "Analogue végétal > Subtitut de produit aquatique"
    SUBSTITUT_D_OEUF = "Substitut d'oeuf", "Analogue végétal > Substitut d'oeuf"
    SANDWICH = "Sandwich (avec ou sans DAOA)", "Composé ou cuisiné > Sandwich (avec ou sans DAOA)"
    PIZZA = "Pizza (avec ou sans DAOA)", "Composé ou cuisiné > Pizza (avec ou sans DAOA)"
    TOURTE_TARTE_SALEE = (
        "Tourte, tarte salée (avec ou sans DAOA)",
        "Composé ou cuisiné > Tourte, tarte salée (avec ou sans DAOA)",
    )
    ASSORTIMENT_AMUSE_BOUCHES = (
        "Assortiment, amuse-bouches (avec ou sans DAOA)",
        "Composé ou cuisiné > Assortiment, amuse-bouches (avec ou sans DAOA)",
    )
    NOUILLE_PATE_PATE_A_TARTE_PATE_A_CREPE = (
        "Nouille, pâte, pâte à tarte, pâte à crêpe (avec œuf)",
        "Composé ou cuisiné > Nouille, pâte, pâte à tarte, pâte à crêpe (avec œuf)",
    )
    PLAT_A_BASE_DE_SALADE = (
        "Plat à base de salade (crudité ou cuidité, avec ou sans DAOA)",
        "Composé ou cuisiné > Plat à base de salade (crudité ou cuidité, avec ou sans DAOA)",
    )
    PLAT_A_BASE_DE_PATE_DE_RIZ_OU_DAUTRE_CEREALE = (
        "Plat à base de pâte, de riz ou d’autre céréale (yc ravioli)",
        "Composé ou cuisiné > Plat à base de pâte, de riz ou d’autre céréale (yc ravioli)",
    )
    PLAT_A_BASE_DE_VIANDE = "Plat à base de viande", "Composé ou cuisiné > Plat à base de viande"
    PLAT_A_BASE_DE_POISSON_ET_FRUIT_DE_MER = (
        "Plat à base de poisson et fruit de mer (yc soupe)",
        "Composé ou cuisiné > Plat à base de poisson et fruit de mer (yc soupe)",
    )
    PLAT_A_BASE_D_UF = "Plat à base d'œuf", "Composé ou cuisiné > Plat à base d'œuf"
    PLAT_A_BASE_DE_FROMAGE = "Plat à base de fromage", "Composé ou cuisiné > Plat à base de fromage"
    PLAT_A_BASE_DE_LEGUME = "Plat à base de légume (yc soupe)", "Composé ou cuisiné > Plat à base de légume (yc soupe)"
    PLAT_MIXTE_DE_DIVERS_VEGETAUX_UF_VIANDE_POISSON_ET_OU_FROMAGE = (
        "Plat mixte de divers végétaux, œuf, viande, poisson et/ou fromage (yc en poudre) (hors infantile)",
        "Composé ou cuisiné > Plat mixte de divers végétaux, œuf, viande, poisson et/ou fromage (yc en poudre) (hors infantile)",
    )
    PLAT_INDETERMINE = (
        "Plat indéterminé (catégorie à éviter)",
        "Composé ou cuisiné > Plat indéterminé (catégorie à éviter)",
    )
    ENTREMET_LACTE_CREME_MOUSSE = (
        "Entremet lacté, crème, mousse",
        "Entremet salé, dessert ou confiserie > Entremet lacté, crème, mousse",
    )
    SORBET_GLACE_CREME_GLACEE = (
        "Sorbet, glace, crème glacée",
        "Entremet salé, dessert ou confiserie > Sorbet, glace, crème glacée",
    )
    ENTREMET_PATISSIER_PATISSERIE_TARTE_FRAICHE = (
        "Entremet pâtissier, pâtisserie, tarte fraîche (yc en poudre)",
        "Entremet salé, dessert ou confiserie > Entremet pâtissier, pâtisserie, tarte fraîche (yc en poudre)",
    )
    BISCUIT_SEC_BARRE = "Biscuit sec, barre", "Entremet salé, dessert ou confiserie > Biscuit sec, barre"
    PATE_A_TARTINER_COMPOSEE = (
        "Pâte à tartiner composée (hors simple pâte d'oléagineux) (yc confiture de lait)",
        "Entremet salé, dessert ou confiserie > Pâte à tartiner composée (hors simple pâte d'oléagineux) (yc confiture de lait)",
    )
    MELANGE_PETIT_DEJEUNER = (
        "Mélange petit déjeuner (muesli) (hors simple céréale)",
        "Entremet salé, dessert ou confiserie > Mélange petit déjeuner (muesli) (hors simple céréale)",
    )
    BONBON_CHEWING_GUM_CARAMEL = (
        "Bonbon, chewing gum, caramel (hors simple fruit confit, hors complément alimentaire)",
        "Entremet salé, dessert ou confiserie > Bonbon, chewing gum, caramel (hors simple fruit confit, hors complément alimentaire)",
    )
    CHOCOLAT = (
        "Chocolat (bouchée, tablette) (hors boisson)",
        "Entremet salé, dessert ou confiserie > Chocolat (bouchée, tablette) (hors boisson)",
    )
    HUILE_VEGETALE = "Huile végétale", "Noix, graine, grain et dérivé > Huile végétale"
    MARGARINE = "Margarine", "Noix, graine, grain et dérivé > Margarine"
    FRUIT_A_COQUE = (
        "Fruit à coque (amande, noisette, noix, pistache, châtaigne…)",
        "Fruit à coque, graine, céréale et dérivé > Fruit à coque (amande, noisette, noix, pistache, châtaigne…)",
    )
    FC_NON_TRANSFORME = (
        "FC - Non transformé (yc mélange)",
        "Fruit à coque, graine, céréale et dérivé > Fruit à coque (amande, noisette, noix, pistache, châtaigne…) > FC - Non transformé (yc mélange)",
    )
    FC_SECHE_CUIT_FERMENTE = (
        "FC - Séché, cuit, fermenté (yc aromatisé, pâte, farine) (hors huile)",
        "Fruit à coque, graine, céréale et dérivé > Fruit à coque (amande, noisette, noix, pistache, châtaigne…) > FC - Séché, cuit, fermenté (yc aromatisé, pâte, farine) (hors huile)",
    )
    FC_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "FC - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Fruit à coque, graine, céréale et dérivé > Fruit à coque (amande, noisette, noix, pistache, châtaigne…) > FC - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    GRAINE_LEGUMINEUSE = (
        "Graine légumineuse (soja, lentille, haricot grain, pois…)",
        "Fruit à coque, graine, céréale et dérivé > Graine légumineuse (soja, lentille, haricot grain, pois…)",
    )
    GL_NON_TRANSFORME = (
        "GL - Non transformé (yc mélange)",
        "Fruit à coque, graine, céréale et dérivé > Graine légumineuse (soja, lentille, haricot grain, pois…) > GL - Non transformé (yc mélange)",
    )
    GL_SECHE_CUIT_FERMENTE = (
        "GL - Séché, cuit, fermenté (yc aromatisé, farine) (hors germé) (yc chips)",
        "Fruit à coque, graine, céréale et dérivé > Graine légumineuse (soja, lentille, haricot grain, pois…) > GL - Séché, cuit, fermenté (yc aromatisé, farine) (hors germé) (yc chips)",
    )
    GL_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "GL - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Fruit à coque, graine, céréale et dérivé > Graine légumineuse (soja, lentille, haricot grain, pois…) > GL - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    GRAINE_OU_FRUIT_OLEAGINEUX = (
        "Graine ou fruit oléagineux (olive, coco, pignon, sésame, tournesol, lin, courge, arachide...)",
        "Fruit à coque, graine, céréale et dérivé > Graine ou fruit oléagineux (olive, coco, pignon, sésame, tournesol, lin, courge, arachide...)",
    )
    GO_NON_TRANSFORME = (
        "GO - Non transformé (yc mélange)",
        "Fruit à coque, graine, céréale et dérivé > Graine ou fruit oléagineux (olive, coco, pignon, sésame, tournesol, lin, courge, arachide...) > GO - Non transformé (yc mélange)",
    )
    GO_SECHE_CUIT_FERMENTE = (
        "GO - Séché, cuit, fermenté (yc aromatisé) (hors huile, germé)",
        "Fruit à coque, graine, céréale et dérivé > Graine ou fruit oléagineux (olive, coco, pignon, sésame, tournesol, lin, courge, arachide...) > GO - Séché, cuit, fermenté (yc aromatisé) (hors huile, germé)",
    )
    GO_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "GO - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Fruit à coque, graine, céréale et dérivé > Graine ou fruit oléagineux (olive, coco, pignon, sésame, tournesol, lin, courge, arachide...) > GO - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    CEREALE = (
        "Céréale (riz, blé, avoine, épeautre…)",
        "Fruit à coque, graine, céréale et dérivé > Céréale (riz, blé, avoine, épeautre…)",
    )
    GC_NON_TRANSFORME = (
        "GC - Non transformé (yc mélange)",
        "Fruit à coque, graine, céréale et dérivé > Céréale (riz, blé, avoine, épeautre…) > GC - Non transformé (yc mélange)",
    )
    GC_SECHE_CUIT_FERMENTE = (
        "GC - Séché, cuit, fermenté  (yc aromatisé) (hors germé) (hors farine)",
        "Fruit à coque, graine, céréale et dérivé > Céréale (riz, blé, avoine, épeautre…) > GC - Séché, cuit, fermenté  (yc aromatisé) (hors germé) (hors farine)",
    )
    GC_PREPARATION_A_BASE_DE_CEREALE_ET_D_EAU = (
        "GC - Préparation à base de céréale et d'eau (pâte, nouille ou vermiGClle, sans œuf)",
        "Fruit à coque, graine, céréale et dérivé > Céréale (riz, blé, avoine, épeautre…) > GC - Préparation à base de céréale et d'eau (pâte, nouille ou vermiGClle, sans œuf)",
    )
    GC_PRODUIT_DE_LA_BOULANGERIE = (
        "GC - Produit de la boulangerie (pain et viennoiserie)",
        "Fruit à coque, graine, céréale et dérivé > Céréale (riz, blé, avoine, épeautre…) > GC - Produit de la boulangerie (pain et viennoiserie)",
    )
    GC_ECRASE_MOULU_FARINE_SON_FLOCON = (
        "GC - Ecrasé, moulu, farine, son, flocon",
        "Fruit à coque, graine, céréale et dérivé > Céréale (riz, blé, avoine, épeautre…) > GC - Ecrasé, moulu, farine, son, flocon",
    )
    BAIE_OU_PETIT_FRUIT = (
        "Baie ou petit fruit (myrtille, fraise…)",
        "Fruit charnu et dérivé > Baie ou petit fruit (myrtille, fraise…)",
    )
    FB_NON_TRANSFORME = (
        "FB - Non transformé (yc mélange)",
        "Fruit charnu et dérivé > Baie ou petit fruit (myrtille, fraise…) > FB - Non transformé (yc mélange)",
    )
    FB_SECHE_CUIT_FERMENTE = (
        "FB - Séché, cuit, fermenté",
        "Fruit charnu et dérivé > Baie ou petit fruit (myrtille, fraise…) > FB - Séché, cuit, fermenté",
    )
    FB_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "FB - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Fruit charnu et dérivé > Baie ou petit fruit (myrtille, fraise…) > FB - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    AGRUME = "Agrume", "Fruit charnu et dérivé > Agrume"
    FA_NON_TRANSFORME = (
        "FA - Non transformé (yc mélange)",
        "Fruit charnu et dérivé > Agrume > FA - Non transformé (yc mélange)",
    )
    FA_SECHE_CUIT_FERMENTE = (
        "FA - Séché, cuit, fermenté",
        "Fruit charnu et dérivé > Agrume > FA - Séché, cuit, fermenté",
    )
    FA_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "FA - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Fruit charnu et dérivé > Agrume > FA - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    AUTRE_FRUIT_CHARNU_OU_MELANGE_DE_FRUIT = (
        "Autre fruit charnu ou mélange de fruit",
        "Fruit charnu et dérivé > Autre fruit charnu ou mélange de fruit",
    )
    FF_NON_TRANSFORME = (
        "FF - Non transformé (yc mélange) (yc salade crue)",
        "Fruit charnu et dérivé > Autre fruit charnu ou mélange de fruit > FF - Non transformé (yc mélange) (yc salade crue)",
    )
    FF_SECHE_CUIT_FERMENTE = (
        "FF - Séché, cuit, fermenté (yc salade cuite)",
        "Fruit charnu et dérivé > Autre fruit charnu ou mélange de fruit > FF - Séché, cuit, fermenté (yc salade cuite)",
    )
    FF_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "FF - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Fruit charnu et dérivé > Autre fruit charnu ou mélange de fruit > FF - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_FEUILLE = "Légume-feuille (salade, épinard…)", "Légume et dérivé > Légume-feuille (salade, épinard…)"
    LF_NON_TRANSFORME = (
        "LF - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-feuille (salade, épinard…) > LF - Non transformé (yc mélange)",
    )
    LF_SECHE_CUIT_FERMENTE = (
        "LF - Séché, cuit, fermenté",
        "Légume et dérivé > Légume-feuille (salade, épinard…) > LF - Séché, cuit, fermenté",
    )
    LF_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LF - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-feuille (salade, épinard…) > LF - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_TIGE = (
        "Légume-tige (céleri branche, asperge...)",
        "Légume et dérivé > Légume-tige (céleri branche, asperge...)",
    )
    LT_NON_TRANSFORME = (
        "LT- Non transformé (yc mélange)",
        "Légume et dérivé > Légume-tige (céleri branche, asperge...) > LT- Non transformé (yc mélange)",
    )
    LT_SECHE_CUIT_FERMENTE = (
        "LT- Séché, cuit, fermenté",
        "Légume et dérivé > Légume-tige (céleri branche, asperge...) > LT- Séché, cuit, fermenté",
    )
    LT_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LT- Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-tige (céleri branche, asperge...) > LT- Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_BULBE = "Légume-bulbe (oignon, échalotte...)", "Légume et dérivé > Légume-bulbe (oignon, échalotte...)"
    LB_NON_TRANSFORME = (
        "LB - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-bulbe (oignon, échalotte...) > LB - Non transformé (yc mélange)",
    )
    LB_SECHE_CUIT_FERMENTE = (
        "LB - Séché, cuit, fermenté",
        "Légume et dérivé > Légume-bulbe (oignon, échalotte...) > LB - Séché, cuit, fermenté",
    )
    LB_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LB - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-bulbe (oignon, échalotte...) > LB - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_FLEUR = (
        "Légume-fleur (choux fleur, choux de Bruxelles, fleur comestible...)",
        "Légume et dérivé > Légume-fleur (choux fleur, choux de Bruxelles, fleur comestible...)",
    )
    LFL_NON_TRANSFORME = (
        "LFL - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-fleur (choux fleur, choux de Bruxelles, fleur comestible...) > LFL - Non transformé (yc mélange)",
    )
    LFL_SECHE_CUIT_FERMENTE = (
        "LFL - Séché, cuit, fermenté",
        "Légume et dérivé > Légume-fleur (choux fleur, choux de Bruxelles, fleur comestible...) > LFL - Séché, cuit, fermenté",
    )
    LFL_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LFL - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-fleur (choux fleur, choux de Bruxelles, fleur comestible...) > LFL - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_FRUIT_SOLANACEE = (
        "Légume-fruit : solanacée (tomate, aubergine…)",
        "Légume et dérivé > Légume-fruit : solanacée (tomate, aubergine…)",
    )
    LFRS_NON_TRANSFORME = (
        "LFRS - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-fruit : solanacée (tomate, aubergine…) > LFRS - Non transformé (yc mélange)",
    )
    LFRS_SECHE_CUIT_FERMENTE = (
        "LFRS - Séché, cuit, fermenté",
        "Légume et dérivé > Légume-fruit : solanacée (tomate, aubergine…) > LFRS - Séché, cuit, fermenté",
    )
    LFRS_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LFRS - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-fruit : solanacée (tomate, aubergine…) > LFRS - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_FRUIT_CUCURBITACEE_A_PEAU_FINE = (
        "Légume-fruit : cucurbitacée à peau fine (courgette, concombre…)",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau fine (courgette, concombre…)",
    )
    LFRCF_NON_TRANSFORME = (
        "LFRCF - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau fine (courgette, concombre…) > LFRCF - Non transformé (yc mélange)",
    )
    LFRCF_SECHE_CUIT_FERMENTE = (
        "LFRCF - Séché, cuit, fermenté",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau fine (courgette, concombre…) > LFRCF - Séché, cuit, fermenté",
    )
    LFRCF_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LFRCF - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau fine (courgette, concombre…) > LFRCF - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_FRUIT_CUCURBITACEE_A_PEAU_EPAISSE = (
        "Légume-fruit : cucurbitacée à peau épaisse (courge, potiron…)",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau épaisse (courge, potiron…)",
    )
    LFRCE_NON_TRANSFORME = (
        "LFRCE - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau épaisse (courge, potiron…) > LFRCE - Non transformé (yc mélange)",
    )
    LFRCE_SECHE_CUIT_FERMENTE = (
        "LFRCE - Séché, cuit, fermenté",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau épaisse (courge, potiron…) > LFRCE - Séché, cuit, fermenté",
    )
    LFRCE_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LFRCE - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-fruit : cucurbitacée à peau épaisse (courge, potiron…) > LFRCE - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_FRUIT_MAIS = "Légume-fruit : maïs", "Légume et dérivé > Légume-fruit : maïs"
    LFRM_NON_TRANSFORME = (
        "LFRM - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-fruit : maïs > LFRM - Non transformé (yc mélange)",
    )
    LFRM_SECHE_CUIT_FERMENTE = (
        "LFRM - Séché, cuit, fermenté (yc pop corn, flocon)",
        "Légume et dérivé > Légume-fruit : maïs > LFRM - Séché, cuit, fermenté (yc pop corn, flocon)",
    )
    LFRM_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LFRM - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-fruit : maïs > LFRM - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_GOUSSE = (
        "Légume-gousse (haricot vert) (hors graine de légumineuse)",
        "Légume et dérivé > Légume-gousse (haricot vert) (hors graine de légumineuse)",
    )
    LG_NON_TRANSFORME = (
        "LG - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-gousse (haricot vert) (hors graine de légumineuse) > LG - Non transformé (yc mélange)",
    )
    LG_SECHE_CUIT_FERMENTE = (
        "LG - Séché, cuit, fermenté",
        "Légume et dérivé > Légume-gousse (haricot vert) (hors graine de légumineuse) > LG - Séché, cuit, fermenté",
    )
    LG_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LG - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-gousse (haricot vert) (hors graine de légumineuse) > LG - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    LEGUME_RACINE_ET_TUBERCULE = (
        "Légume-racine et tubercule (radis, pomme-de-terre, carotte…)",
        "Légume et dérivé > Légume-racine et tubercule (radis, pomme-de-terre, carotte…)",
    )
    LR_NON_TRANSFORME = (
        "LR - Non transformé (yc mélange)",
        "Légume et dérivé > Légume-racine et tubercule (radis, pomme-de-terre, carotte…) > LR - Non transformé (yc mélange)",
    )
    LR_SECHE_CUIT_FERMENTE = (
        "LR - Séché, cuit, fermenté (yc chips)",
        "Légume et dérivé > Légume-racine et tubercule (radis, pomme-de-terre, carotte…) > LR - Séché, cuit, fermenté (yc chips)",
    )
    LR_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LR - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Légume-racine et tubercule (radis, pomme-de-terre, carotte…) > LR - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    CHAMPIGNON = "Champignon", "Légume et dérivé > Champignon"
    CH_NON_TRANSFORME = (
        "CH - Non transformé (yc mélange)",
        "Légume et dérivé > Champignon > CH - Non transformé (yc mélange)",
    )
    CH_SECHE_CUIT_FERMENTE = "CH - Séché, cuit, fermenté", "Légume et dérivé > Champignon > CH - Séché, cuit, fermenté"
    CH_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "CH - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Champignon > CH - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    MELANGE_DE_LEGUME = "Mélange de légume", "Légume et dérivé > Mélange de légume"
    LL_NON_TRANSFORME_OU_PEU_TRANSFORME = (
        "LL - Non transformé (yc mélange) ou peu transformé (yc salade de crudité)",
        "Légume et dérivé > Mélange de légume > LL - Non transformé (yc mélange) ou peu transformé (yc salade de crudité)",
    )
    LL_SECHE_CUIT_FERMENTE_EN_SOUPE_YC_SALADE_DE_CUIDITE = (
        "LL - Séché, cuit, fermenté, en soupe, yc salade de cuidité",
        "Légume et dérivé > Mélange de légume > LL - Séché, cuit, fermenté, en soupe, yc salade de cuidité",
    )
    LL_CONFIT_EN_CONFITURE_EN_VINAIGRE_EN_SAUMURE_EN_ALCOOL = (
        "LL - Confit, en confiture, en vinaigre, en saumure, en alcool",
        "Légume et dérivé > Mélange de légume > LL - Confit, en confiture, en vinaigre, en saumure, en alcool",
    )
    GRAINE_GERMEE_ET_POUSSE = "Graine germée et pousse", "Légume et dérivé > Graine germée et pousse"
    GRAINE_GERMEE = (
        "Graine germée (avec agrément)",
        "Légume et dérivé > Graine germée et pousse > Graine germée (avec agrément)",
    )
    POUSSE_JEUNE_POUSSE = (
        "Pousse, jeune pousse (sans agrément)",
        "Légume et dérivé > Graine germée et pousse > Pousse, jeune pousse (sans agrément)",
    )
    SUCRE_PUR_SIROP_DE_SUCRE_MELASSE = (
        "Sucre, pur sirop de sucre, mélasse",
        "Condiment et herboristerie > Sucre, pur sirop de sucre, mélasse",
    )
    SEL_SEL_AROMATISE = "Sel, sel aromatisé", "Condiment et herboristerie > Sel, sel aromatisé"
    EPICE_MELANGE_EPICE = "Epice, mélange épicé", "Condiment et herboristerie > Epice, mélange épicé"
    HERBE_OU_GRAINE_AROMATIQUE_MELANGE_AROMATIQUE = (
        "Herbe ou graine aromatique, mélange aromatique",
        "Condiment et herboristerie > Herbe ou graine aromatique, mélange aromatique",
    )
    MOUTARDE_VINAIGRE_ET_VINAIGRETTE = (
        "Moutarde, vinaigre et vinaigrette",
        "Condiment et herboristerie > Moutarde, vinaigre et vinaigrette",
    )
    SAUCE_A_BASE_VEGETALE = (
        "Sauce à base végétale (yc tomate, pesto) (yc avec DAOA)",
        "Condiment et herboristerie > Sauce à base végétale (yc tomate, pesto) (yc avec DAOA)",
    )
    SAUCE_A_BASE_UF = (
        "Sauce à base œuf (mayonnaise, hollandaise)",
        "Condiment et herboristerie > Sauce à base œuf (mayonnaise, hollandaise)",
    )
    BOUILLON = (
        "Bouillon (cube, poudre) (yc avec DAOA)",
        "Condiment et herboristerie > Bouillon (cube, poudre) (yc avec DAOA)",
    )
    HUILE_ESSENTIELLE = "Huile essentielle", "Condiment et herboristerie > Huile essentielle"
    EAU_MINERALE_ET_NATURELLE_EAU_EMBOUTEILLEE = (
        "Eau minérale et naturelle, eau embouteillée",
        "Boisson > Eau minérale et naturelle, eau embouteillée",
    )
    EAU_AROMATISEE = "Eau aromatisée", "Boisson > Eau aromatisée"
    EAU_POTABLE_AUTRE = "Eau potable autre (yc glaçon)", "Boisson > Eau potable autre (yc glaçon)"
    JUS_DE_FRUIT_OU_LEGUME = "Jus de fruit ou légume", "Boisson > Jus de fruit ou légume"
    POUR_BOISSON_CHAUDE_OU_CUISINE = (
        "Pour boisson chaude ou cuisine (chocolaté, cacao, café, thé, tisane, yc en grain, feuile, poudre)",
        "Boisson > Pour boisson chaude ou cuisine (chocolaté, cacao, café, thé, tisane, yc en grain, feuile, poudre)",
    )
    POUR_BOISSON_FROIDE = (
        "Pour boisson froide (sirop aromatisé, base à soda)",
        "Boisson > Pour boisson froide (sirop aromatisé, base à soda)",
    )
    SODA_KOMBUCHA = (
        "Soda, kombucha (hors jus de fruit, kefir, produit lacté, analogue lacté)",
        "Boisson > Soda, kombucha (hors jus de fruit, kefir, produit lacté, analogue lacté)",
    )
    BOISSON_ALCOOLISEE = (
        "Boisson alcoolisée (dont vin, bière, hydromel, spiritueux)",
        "Boisson > Boisson alcoolisée (dont vin, bière, hydromel, spiritueux)",
    )
    BOISSON_DESALCOOLISEE = (
        "Boisson désalcoolisée (vin, bière sans alcool)",
        "Boisson > Boisson désalcoolisée (vin, bière sans alcool)",
    )
    PREPARATION_EN_POUDRE_POUR_ENFANT_DE_0_36_MOIS = (
        "Préparation en poudre pour enfant de 0-36 mois (hors DADFMS)",
        "Aliment infantile > Préparation en poudre pour enfant de 0-36 mois (hors DADFMS)",
    )
    PREPARATION_LIQUIDE_POUR_ENFANT_DE_0_36_MOIS = (
        "Préparation liquide pour enfant de 0-36 mois (hors DADFMS)",
        "Aliment infantile > Préparation liquide pour enfant de 0-36 mois (hors DADFMS)",
    )
    PREPARATION_A_BASE_DE_CEREALE_POUR_ENFANT_DE_0_36_MOIS = (
        "Préparation à base de céréale pour enfant de 0-36 mois (hors DADFMS) (hors poudre) (hors liquide)",
        "Aliment infantile > Préparation à base de céréale pour enfant de 0-36 mois (hors DADFMS) (hors poudre) (hors liquide)",
    )
    AUTRE_ALIMENT_POUR_ENFANT_DE_0_36_MOIS = (
        "Autre aliment pour enfant de 0-36 mois (hors DADFMS)",
        "Aliment infantile > Autre aliment pour enfant de 0-36 mois (hors DADFMS)",
    )
    DADFMS_POUR_ENFANT_0_36_MOIS = "DADFMS pour enfant 0-36 mois", "DADFMS > DADFMS pour enfant 0-36 mois"
    DADFMS_POUR_PERSONNE_DE_PLUS_DE_3_ANS = (
        "DADFMS pour personne de plus de 3 ans",
        "DADFMS > DADFMS pour personne de plus de 3 ans",
    )
    ADDITIF_ALIMENTAIRE = "Additif alimentaire", "Améliorant ou auxiliaire > Additif alimentaire"
    AROME = "Arome", "Améliorant ou auxiliaire > Arome"
    FERMENT_ENZYME = "Ferment, enzyme", "Améliorant ou auxiliaire > Ferment, enzyme"
    COMPLEMENT_ALIMENTAIRE = "Complément alimentaire", "Complément alimentaire > Complément alimentaire"
    FEED_MP_CEREALE_ET_DERIVE = (
        "Feed - MP céréale et dérivé",
        "Alimentation animale - matière première végétale > Feed - MP céréale et dérivé",
    )
    FEED_MP_OLEAGINEUX_ET_DERIVE = (
        "Feed - MP oléagineux et dérivé",
        "Alimentation animale - matière première végétale > Feed - MP oléagineux et dérivé",
    )
    FEED_MP_LEGUMINEUSE_ET_DERIVE = (
        "Feed - MP légumineuse (pois, féverole, lupin…) et dérivé",
        "Alimentation animale - matière première végétale > Feed - MP légumineuse (pois, féverole, lupin…) et dérivé",
    )
    FEED_MP_TUBERCULE_RACINE_ET_DERIVE = (
        "Feed - MP tubercule, racine (betterave, pomme de terre…) et dérivé",
        "Alimentation animale - matière première végétale > Feed - MP tubercule, racine (betterave, pomme de terre…) et dérivé",
    )
    FEED_MP_FOURRAGE = (
        "Feed - MP fourrage (herbe, foin, paille, ensilage, luzerne, trèfle…)",
        "Alimentation animale - matière première végétale > Feed - MP fourrage (herbe, foin, paille, ensilage, luzerne, trèfle…)",
    )
    FEED_MP_AUTRE = (
        "Feed - MP autre (coproduit, algue, bois, DVOV déclassée...)",
        "Alimentation animale - matière première végétale > Feed - MP autre (coproduit, algue, bois, DVOV déclassée...)",
    )
    FEED_MP_D_ORIGINE_MINERALE = (
        "Feed - MP d'origine minérale",
        "Alimentation animale - matière première autre > Feed - MP d'origine minérale",
    )
    FEED_MP_D_ORIGINE_AUTRE = (
        "Feed - MP d'origine autre (micro-organisme inactivé...)",
        "Alimentation animale - matière première autre > Feed - MP d'origine autre (micro-organisme inactivé...)",
    )
    FEED_MP_LAIT_ET_PRODUIT_LAITIER = (
        "Feed - MP lait et produit laitier",
        "Alimentation animale - matière première animale > Feed - MP lait et produit laitier",
    )
    FEED_MP_PRODUIT_D_ANIMAUX_TERRESTRES = (
        "Feed - MP produit d'animaux terrestres",
        "Alimentation animale - matière première animale > Feed - MP produit d'animaux terrestres",
    )
    AAMPAT_PROTEINE_ANIMALE_TRANSFORMEE = (
        "AAMPAT - Protéine animale transformée (PAT)",
        "Alimentation animale - matière première animale > Feed - MP produit d'animaux terrestres > AAMPAT - Protéine animale transformée (PAT)",
    )
    AAMPAT_AUTRE = (
        "AAMPAT - Autre",
        "Alimentation animale - matière première animale > Feed - MP produit d'animaux terrestres > AAMPAT - Autre",
    )
    FEED_MP_PRODUIT_D_ANIMAUX_AQUATIQUES = (
        "Feed - MP produit d'animaux aquatiques",
        "Alimentation animale - matière première animale > Feed - MP produit d'animaux aquatiques",
    )
    AAMPAA_PROTEINE_ANIMALE_TRANSFORMEE = (
        "AAMPAA - Protéine animale transformée (PAT)",
        "Alimentation animale - matière première animale > Feed - MP produit d'animaux aquatiques > AAMPAA - Protéine animale transformée (PAT)",
    )
    AAMPAA_AUTRE = (
        "AAMPAA - Autre",
        "Alimentation animale - matière première animale > Feed - MP produit d'animaux aquatiques > AAMPAA - Autre",
    )
    FEED_ADDITIF = "Feed - additif", "Alimentation animale - additif, prémélange > Feed - additif"
    FEED_PREMELANGE_POUR_ANIMAUX_D_ELEVAGE = (
        "Feed - prémélange pour animaux d'élevage",
        "Alimentation animale - additif, prémélange > Feed - prémélange pour animaux d'élevage",
    )
    FEED_PREMELANGE_POUR_ANIMAUX_FAMILIERS = (
        "Feed - prémélange pour animaux familiers",
        "Alimentation animale - additif, prémélange > Feed - prémélange pour animaux familiers",
    )
    FEED_ALIMENT_COMPOSE_POUR_ANIMAUX_FAMILIERS = (
        "Feed - Aliment composé pour animaux familiers",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux familiers",
    )
    AACOMP_POUR_CARNIVORE_DOMESTIQUE = (
        "AACOMP - Pour carnivore domestique (chien, chat, furet...)",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux familiers > AACOMP - Pour carnivore domestique (chien, chat, furet...)",
    )
    AACOMP_POUR_OISEAU_D_ORNEMENT_OU_OISEAU_DU_CIEL = (
        "AACOMP - Pour oiseau d'ornement ou oiseau du ciel (hors volaille)",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux familiers > AACOMP - Pour oiseau d'ornement ou oiseau du ciel (hors volaille)",
    )
    AACOMP_POUR_POISSON_D_ORNEMENT_ET_AUTRE_ANIMAL_AQUATIQUE_D_ORNEMENT = (
        "AACOMP - Pour poisson d'ornement et autre animal aquatique d'ornement",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux familiers > AACOMP - Pour poisson d'ornement et autre animal aquatique d'ornement",
    )
    AACOMP_POUR_AUTRE_ANIMAL_FAMILIER = (
        "AACOMP - Pour autre animal familier (rongeur, hérisson, reptile…) (hors lapin)",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux familiers > AACOMP - Pour autre animal familier (rongeur, hérisson, reptile…) (hors lapin)",
    )
    FEED_ALIMENT_COMPOSE_POUR_ANIMAUX_D_ELEVAGE = (
        "Feed - Aliment composé pour animaux d'élevage",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage",
    )
    AACOMP_POUR_PORCIN = (
        "AACOMP - Pour porcin",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage > AACOMP - Pour porcin",
    )
    AACOMP_POUR_VOLAILLE = (
        "AACOMP - Pour volaille",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage > AACOMP - Pour volaille",
    )
    AACOMP_POUR_RUMINANT = (
        "AACOMP - Pour ruminant",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage > AACOMP - Pour ruminant",
    )
    AACOMP_POUR_ANIMAUX_D_ELEVAGE_AQUATIQUES = (
        "AACOMP - Pour animaux d'élevage aquatiques (poisson, invertébré) (yc appâts)",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage > AACOMP - Pour animaux d'élevage aquatiques (poisson, invertébré) (yc appâts)",
    )
    AACOMP_POUR_LEPORIDE = (
        "AACOMP - Pour léporidé (lapin, lièvre)",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage > AACOMP - Pour léporidé (lapin, lièvre)",
    )
    AACOMP_POUR_EQUIN = (
        "AACOMP - Pour équin",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage > AACOMP - Pour équin",
    )
    AACOMP_POUR_AUTRE = (
        "AACOMP - Pour autre (abeille, camélidé, animaux à fourrure …)",
        "Alimentation animale - aliment composé > Feed - Aliment composé pour animaux d'élevage > AACOMP - Pour autre (abeille, camélidé, animaux à fourrure …)",
    )
    FEED_ALIMENT_MEDICAMENTEUX = (
        "Feed - Aliment médicamenteux",
        "Alimentation animale - médicamenteux > Feed - Aliment médicamenteux",
    )
    FEED_PRODUIT_INTERMEDIAIRE = (
        "Feed - Produit intermédiaire",
        "Alimentation animale - médicamenteux > Feed - Produit intermédiaire",
    )
    FEED_ALIMENTATION_ANIMALE_AUTRE = (
        "Feed - Alimentation animale - autre (catégorie à éviter)",
        "Alimentation animale - autre > Feed - Alimentation animale - autre (catégorie à éviter)",
    )
    PRODUIT_ALIMENTAIRE_INDETERMINE = (
        "Produit alimentaire indéterminé",
        "Produit alimentaire indéterminé > Produit alimentaire indéterminé",
    )
    SOUS_PRODUIT_ANIMAL_TECHNIQUE = (
        "Sous-produit animal technique (non destiné à l'alimentation animale)",
        "Produit non alimentaire > Sous-produit animal technique (non destiné à l'alimentation animale)",
    )
    AUTRE_PRODUIT_NON_ALIMENTAIRE = (
        "Autre produit non alimentaire",
        "Produit non alimentaire > Autre produit non alimentaire",
    )
    PRODUIT_INDETERMINE = "Produit indéterminé", "Produit indéterminé > Produit indéterminé"
    ENVIRONNEMENT_SURFACE = "Environnement - surface", "Environnement - surface > Environnement - surface"
    SANS_OBJET = "Sans objet", "Sans objet > Sans objet"
