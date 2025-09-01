from django.db import models
from .choicejs_utils import WithChoicesToJS


class CategorieProduit(WithChoicesToJS, models.TextChoices):
    DE_BOUCHERIE = "Produit carné de boucherie", "Produit carné > De boucherie"
    VIANDE_OS_ABAT_ROUGE = (
        "Viande, os et abat rouge de boucherie",
        "Produit carné > De boucherie > Viande, os et abat rouge de boucherie",
    )
    VIANDE_HACHEE = "Viande hachée de boucherie", "Produit carné > De boucherie > Viande hachée de boucherie"
    VSM = "VSM de boucherie", "Produit carné > De boucherie > VSM de boucherie"
    ABAT_BLANC = "Abat blanc de boucherie", "Produit carné > De boucherie > Abat blanc de boucherie"
    PV = "PV de boucherie", "Produit carné > De boucherie > PV de boucherie"
    PABV_CRU = "PABV de boucherie cru", "Produit carné > De boucherie > PABV de boucherie cru"
    PABV_CUIT = "PABV de boucherie cuit", "Produit carné > De boucherie > PABV de boucherie cuit"

    DE_VOLAILLE = "Produit carné de volaille/lagomorphe", "Produit carné > De volaille/lagomorphe"
    VIANDE_OS_ABAT_VOLAILLE = (
        "Viande, os et abat de volaille/lagomorphe",
        "Produit carné > De volaille/lagomorphe > Viande, os et abat de volaille/lagomorphe",
    )
    VIANDE_HACHEE_VOLAILLE = (
        "Viande hachée de volaille/lagomorphe",
        "Produit carné > De volaille/lagomorphe > Viande hachée de volaille/lagomorphe",
    )
    VSM_VOLAILLE = "VSM de volaille/lagomorphe", "Produit carné > De volaille/lagomorphe > VSM de volaille/lagomorphe"
    PV_VOLAILLE = "PV de volaille/lagomorphe", "Produit carné > De volaille/lagomorphe > PV de volaille/lagomorphe"
    PABV_VOLAILLE = (
        "PABV de volaille/lagomorphe",
        "Produit carné > De volaille/lagomorphe > PABV de volaille/lagomorphe",
    )

    DE_GIBIER = "Produit carné de gibier", "Produit carné > De gibier"
    VIANDE_GRAND_GIBIER = (
        "Viande et produits de grand gibier",
        "Produit carné > De gibier > Viande et produits de grand gibier",
    )
    VIANDE_PETIT_GIBIER_MAM = (
        "Viande et produits de petit gibier (mammifères)",
        "Produit carné > De gibier > Viande et produits de petit gibier (mammifères)",
    )
    VIANDE_PETIT_GIBIER_OISEAUX = (
        "Viande et produits de petit gibier (oiseaux)",
        "Produit carné > De gibier > Viande et produits de petit gibier (oiseaux)",
    )

    DE_POISSON = "Produit de la pêche de poisson", "Produit de la pêche > de poisson"
    POISSON_CRU = "Poisson cru entier ou fileté", "Produit de la pêche > de poisson > Poisson cru entier ou fileté"
    POISSON_TRANSFORME = "Poisson fumé salé ou mariné", "Produit de la pêche > de poisson > Poisson fumé salé ou mariné"
    CONSERVE_POISSON = "Conserves de poisson", "Produit de la pêche > de poisson > Conserves de poisson"

    DE_CEPHALOPODE = "Produit de la pêche de céphalopode", "Produit de la pêche > de céphalopode"
    CEPHALOPODE_CRU = (
        "Céphalopode cru entier ou coupé",
        "Produit de la pêche > de céphalopode > Céphalopode cru entier ou coupé",
    )
    PRODUIT_CEPHALOPODE = "Produit de céphalopode", "Produit de la pêche > de céphalopode > Produit de céphalopode"

    DE_COQUILLAGE = "Produit de la pêche de coquillage", "Produit de la pêche > de coquillage"
    COQUILLAGE_VIVANT = "Coquillage vivant", "Produit de la pêche > de coquillage > Coquillage vivant"
    PRODUIT_COQUILLAGE = "Produit de coquillage", "Produit de la pêche > de coquillage > Produit de coquillage"

    DE_CRUSTACE = "Produit de la pêche de crustacé", "Produit de la pêche > de crustacé"
    CRUSTACE_VIVANT = "Crustacé vivant ou cru", "Produit de la pêche > de crustacé > Crustacé vivant ou cru"
    PRODUIT_CRUSTACE = "Produit de crustacé", "Produit de la pêche > de crustacé > Produit de crustacé"

    D_ESCARGOT = "Produit de la pêche d'escargot", "Produit de la pêche > d'escargot"
    ESCARGOT_CRU = "Escargot cru", "Produit de la pêche > d'escargot > Escargot cru"
    PRODUIT_ESCARGOT = "Produit d'escargot", "Produit de la pêche > d'escargot > Produit d'escargot"

    DE_GRENOUILLE = "Produit de la pêche grenouille", "Produit de la pêche > de grenouille"
    GRENOUILLE = "Grenouille", "Produit de la pêche > de grenouille > Grenouille"
    PRODUIT_GRENOUILLE = "Produit de grenouille", "Produit de la pêche > de grenouille > Produit de grenouille"

    D_OEUF = "Oeuf", "Produit d'oeuf > Oeuf"
    OEUF_COQUILLE = "oeuf coquille", "Produit d'oeuf > Oeuf > Oeuf coquille"

    OVOPRODUIT = "Ovoproduit", "Produit d'oeuf > Ovoproduit"
    COULE_FRAICHE = "Coule fraiche d'oeuf", "Produit d'oeuf > Ovoproduit > Coule fraiche d'oeuf"
    OEUF_LIQUIDE = (
        "oeuf liquide pasteurisé (jaune, blanc, entier)",
        "Produit d'oeuf > Ovoproduit > Oeuf liquide pasteurisé (jaune, blanc, entier)",
    )
    POUDRE_OEUF = "Poudre d'oeuf", "Produit d'oeuf > Ovoproduit > Poudre d'oeuf"
    OEUFS_DURS = "Oeufs durs (écalés ou non)", "Produit d'oeuf > Ovoproduit > Oeufs durs (écalés ou non)"
    AUTRE_OVOPRODUIT = "Autre", "Produit d'oeuf > Ovoproduit > Autre"

    PRODUIT_LAITIER = "Produit laitiier lait", "Produit laitier > Lait "
    LAIT_CRU = (
        "Lait cru (matière 1ère ou de consommation)",
        "Produit laitier > Lait > Lait cru (matière 1ère ou de consommation)",
    )
    LAIT_TRAITE = (
        "Lait traité (pasteurisé, microfilté, stérilisé), hors infantile",
        "Produit laitier > Lait > Lait traité (pasteurisé, microfilté, stérilisé), hors infantile",
    )

    POUDRE_LAIT = "Poudre de lait", "Produit laitier > Poudre de lait"
    POUDRE_LAIT_NON_INFANTILE = (
        "Poudre de lait et dérivés (poudre de sérum, caséïne, lactose, minéraux...), hors infantile",
        "Produit laitier > Poudre de lait > Poudre de lait et dérivés (poudre de sérum, caséïne, lactose, minéraux...), hors infantile",
    )

    PRODUIT_LAITIER_FERMENTES = "Produit laitier fermentes", "Produit laitier > Produits laitiers fermentés"
    YAOURT = "Yaourt", "Produit laitier > Produits laitiers fermentés > Yaourt"
    LAIT_FERMENTE = "Lait fermenté", "Produit laitier > Produits laitiers fermentés > Lait fermenté"

    FROMAGE = "Produit laitier fromage", "Produit laitier > Fromage"
    FROMAGE_FRAIS = "Fromage lait cru à pâtes fraiches", "Produit laitier > Fromage > Fromage lait cru à pâtes fraiches"
    FROMAGE_LACTIQUE = (
        "Fromage lait cru à pâtes lactiques",
        "Produit laitier > Fromage > Fromage lait cru à pâtes lactiques",
    )
    FROMAGE_MOLLE = "Fromage lait cru à pâtes molles", "Produit laitier > Fromage > Fromage lait cru à pâtes molles"
    FROMAGE_PRESSE_NON_CUIT = (
        "Fromage lait cru à pâtes pressées non cuites",
        "Produit laitier > Fromage > Fromage lait cru à pâtes pressées non cuites",
    )
    FROMAGE_PRESSE_CUIT = (
        "Fromage lait cru à pâtes pressées cuites",
        "Produit laitier > Fromage > Fromage lait cru à pâtes pressées cuites",
    )
    FROMAGE_TRAITE = "Fromage lait traité", "Produit laitier > Fromage > Fromage lait traité"
    FROMAGE_FONDU = "Fromage fondu et autre", "Produit laitier > Fromage > Fromage fondu et autre"

    CREME_BEURRE = "Produit laitier creme beurre", "Produit laitier > Crème et beurre"
    CREME_CRUE = "Crème crue", "Produit laitier > Crème et beurre > Crème crue"
    CREME_TRAITEE = "Crème traitée", "Produit laitier > Crème et beurre > Crème traitée"
    BEURRE_CRU = "Beurre cru", "Produit laitier > Crème et beurre > Beurre cru"
    BEURRE_TRAITE = "Beurre traité", "Produit laitier > Crème et beurre > Beurre traité"

    PRODUIT_RUCHE = "Produit ruche", "Produit de la ruche > Miel et produit de la ruche"
    MIEL = "Miel", "Produit de la ruche > Miel et produit de la ruche > Miel"
    PRODUIT_RUCHE_HORS_MIEL = (
        "Produit de la ruche (sauf miel)",
        "Produit de la ruche > Miel et produit de la ruche > Produit de la ruche (sauf miel)",
    )

    AUTRES_COLLAGENE = "Collagène", "Autres produits animaux > Collagène"
    AUTRES_GELATINE = "Gélatine", "Autres produits animaux > Gélatine"
    AUTRES_GRAISSE = (
        "Graisse et fonte DOA (sauf beurre et crème)",
        "Autres produits animaux > Graisse et fonte DOA (sauf beurre et crème)",
    )
    AUTRES_RAFFINES = "Autres produits raffinés DOA", "Autres produits animaux > Autres produits raffinés DOA"

    FRUIT_CHARNU = "Fruit charnu", "Fruits et légumes > Fruit charnu, légume ou champignon"
    FRUITS_FRAIS = (
        "Fruit, légume ou champignon frais ou non transformé",
        "Fruits et légumes > Fruit charnu, légume ou champignon > Fruit, légume ou champignon frais ou non transformé",
    )
    FRUITS_SECHES = (
        "Fruits, légumes ou champignons séchés (yc chips, sauf herboristerie)",
        "Fruits et légumes > Fruit charnu, légume ou champignon > Fruits, légumes ou champignons séchés (yc chips, sauf herboristerie)",
    )
    FRUITS_SOUPE = (
        "Soupe à base de fruit, légume ou champignon",
        "Fruits et légumes > Fruit charnu, légume ou champignon > Soupe à base de fruit, légume ou champignon",
    )
    FRUITS_JUS = (
        "Jus de fruit, légume ou champignon",
        "Fruits et légumes > Fruit charnu, légume ou champignon > Jus de fruit, légume ou champignon",
    )
    FRUITS_TRANSFORME = (
        "Fruit, légume ou champignon transformé",
        "Fruits et légumes > Fruit charnu, légume ou champignon > Fruit, légume ou champignon transformé",
    )

    GRAINE_NON_TRANSFORMEE = (
        "Graine non transformée (protéagineuse, oléagineuse)",
        "Noix, graine et grain > Graine non transformée (protéagineuse, oléagineuse)",
    )
    GRAINE_PREPARATION = (
        "Préparation et dérivé de graine ou noix (hors huile et graine germée, hors céréale)",
        "Noix, graine et grain > Préparation et dérivé de graine ou noix (hors huile et graine germée, hors céréale)",
    )
    GRAINE_GERMEE = "Graine germée ou à germer", "Noix, graine et grain > Graine germée ou à germer"
    FRUIT_COQUE = "Fruit à coque non transformé", "Noix, graine et grain > Fruit à coque non transformé"
    FRUIT_COQUE_PREPARATION = (
        "Préparation et dérivé de fruit à coque (hors huile)",
        "Noix, graine et grain > Préparation et dérivé de fruit à coque (hors huile)",
    )
    HUILE_VEGETALE = "Graisse et huile végétale", "Noix, graine et grain > Graisse et huile végétale"

    CEREALE_ENTIERE = (
        "Produit de céréale entière ou moulue, farine",
        "Produit de céréale > Produit de céréale entière ou moulue, farine",
    )
    CEREALE_PREPARATION = (
        "Préparation de céréale (yc pâte sans oeuf ou vermicelle)",
        "Produit de céréale > Préparation de céréale (yc pâte sans oeuf ou vermicelle)",
    )
    BOULANGERIE = (
        "Produit de la boulangerie (pain et viennoiserie)",
        "Produit de céréale > Produit de la boulangerie (pain et viennoiserie)",
    )

    SUBSTITUT_PRODUIT_LAITIER = "Substitut produit laitier", "Analogue végétal > Substitut végétal de produit laitier"
    SUBSTITUT_LAIT_INFANTILE = (
        "Substitut de lait infantile végétal",
        "Analogue végétal > Substitut végétal de produit laitier > Substitut de lait infantile végétal",
    )
    SUBSTITUT_LAIT = "Substitut de lait", "Analogue végétal > Substitut végétal de produit laitier > Substitut de lait"
    SUBSTITUT_FROMAGE = (
        "Substitut de fromage",
        "Analogue végétal > Substitut végétal de produit laitier > Substitut de fromage",
    )
    SUBSTITUT_YAOURT = (
        "Substitut de yaourt",
        "Analogue végétal > Substitut végétal de produit laitier > Substitut de yaourt",
    )
    SUBSTITUT_CARNE = "Substitut végétal de produit carné", "Analogue végétal > Substitut végétal de produit carné"
    SUBSTITUT_MER = (
        "Substitut végétal de produit de la mer",
        "Analogue végétal > Substitut végétal de produit de la mer",
    )

    CONDIMENT_SUCRE = "Sucre", "Condiment > Sucre"
    CONDIMENT_VINAIGRE = "Moutarde, vinaigre et vinaigrette", "Condiment > Moutarde, vinaigre et vinaigrette"
    CONDIMENT_EPICES = "Fines herbes et épices", "Condiment > Fines herbes et épices"
    CONDIMENT_SAUCE = (
        "Bouillon ou sauce (mayonnaise, pesto, tomate)",
        "Condiment > Bouillon ou sauce (mayonnaise, pesto, tomate)",
    )
    CONDIMENT_SEL = "Sel", "Condiment > Sel"

    SNACK_CONFISERIE = "Confiserie (yc chewing gum)", "Produit sucré, salé, snack > Confiserie (yc chewing gum)"
    SNACK_CHOCOLAT = "Chocolat (bouchée, tablette)", "Produit sucré, salé, snack > Chocolat (bouchée, tablette)"

    DESSERT_FRAIS = "Dessert Frais", "Produit sucré, salé, snack > Dessert frais (hors yaourt)"
    SNACK_GLACE = "Crème glacée", "Produit sucré, salé, snack > Dessert frais (hors yaourt) > Crème glacée"
    SNACK_CREME = (
        "Crème dessert, riz au lait, mousse au chocolat...",
        "Produit sucré, salé, snack > Dessert frais (hors yaourt) > Crème dessert, riz au lait, mousse au chocolat...",
    )
    SNACK_PATISSERIE = "Dessert patissier, pâtisserie", "Produit sucré, salé, snack > Dessert patissier, pâtisserie"
    SNACK_SEC = (
        "Dessert sec (biscuit, cake, produit petit-dejeuner, snack)",
        "Produit sucré, salé, snack > Dessert sec (biscuit, cake, produit petit-dejeuner, snack)",
    )
    SNACK_TARTINER = "Pâtes à tartiner", "Produit sucré, salé, snack > Pâtes à tartiner"
    SNACK_SALE = (
        "Biscuit, cake, snack salé  (hors chips ou noix/graine)",
        "Produit sucré, salé, snack > Biscuit, cake, snack salé  (hors chips ou noix/graine)",
    )

    CUISINE_SALADE = "Salade composée", "Cuisiné ou composé > Salade composée"
    CUISINE_PLAT = (
        "Plat ou soupe composé (hors soupe de légumes/fruits/champignons)",
        "Cuisiné ou composé > Plat ou soupe composé (hors soupe de légumes/fruits/champignons)",
    )

    BOISSON_ALCOOL = (
        "Boisson alcoolisée (dont vin, bière, hydromel)",
        "Boisson > Boisson alcoolisée (dont vin, bière, hydromel)",
    )

    BOISSON_NON_ALCOOL = "Boisson alcoolisée", "Boisson > Boisson non alcoolisée"
    BOISSON_SODA = (
        "Soda, kombucha (hors jus de fruit, produit lacté, analogue lacté)",
        "Boisson > Boisson non alcoolisée > Soda, kombucha (hors jus de fruit, produit lacté, analogue lacté)",
    )
    BOISSON_CHAUDE = (
        "Préparation pour boisson chaude (chocolaté, café, thé, tisane)",
        "Boisson > Boisson non alcoolisée > Préparation pour boisson chaude (chocolaté, café, thé, tisane)",
    )
    BOISSON_FROIDE = (
        "Préparation pour boisson froide (sirop, base à soda)",
        "Boisson > Boisson non alcoolisée > Préparation pour boisson froide (sirop, base à soda)",
    )
    BOISSON_EAU = "Eau minérale et naturelle, eau embouteillée", "Boisson > Eau minérale et naturelle, eau embouteillée"
    BOISSON_AROMATISEE = "Eau aromatisée", "Boisson > Eau aromatisée"
    BOISSON_POTABLE = "Eau potable autre", "Boisson > Eau potable autre"

    ALIMENTATION_INFANTILE = "Alimentation infantile", "DADFMS > Alimentation Infantile"
    DADFMS_LAIT_0_1 = "Lait infantile 0-1an", "DADFMS > Alimentation Infantile > Lait infantile 0-1an"
    DADFMS_LAIT_1_3 = "Lait infantile 1-3ans", "DADFMS > Alimentation Infantile > Lait infantile 1-3ans"
    DADFMS_AUTRE_INFANTILE = (
        "Autre aliment infantile 0-3ans",
        "DADFMS > Alimentation Infantile > Autre aliment infantile 0-3ans",
    )
    DADFMS_36M = "Aliment pour personne de plus de 36 mois", "DADFMS > Aliment pour personne de plus de 36 mois"

    AMELIORANT_ADDITIF = "Additif alimentaire", "Améliorant ou auxiliaire > Additif alimentaire"
    AMELIORANT_AROME = "Arome", "Améliorant ou auxiliaire > Arome"
    AMELIORANT_FERMENT = "Ferment, enzyme", "Améliorant ou auxiliaire > Ferment, enzyme"

    ALIMENT_ANIMAL_ADDITIF = (
        "Additif et pré-mélange pour animaux",
        "Alimentation animale > Additif et pré-mélange pour animaux",
    )
    ALIMENT_ANIMAL_COMPOSE = "Aliment composé pour animaux", "Alimentation animale > Aliment composé pour animaux"
    ALIMENT_ANIMAL_VEGETAL = (
        "Matière première végétale pour animaux",
        "Alimentation animale > Matière première végétale pour animaux",
    )
    ALIMENT_ANIMAL_PETFOOD = "Petfood", "Alimentation animale > Petfood"
    ALIMENT_ANIMAL_AUTRE = "Autre aliment pour animaux", "Alimentation animale > Autre aliment pour animaux"

    HERBORISTERIE = "Herbes et huiles essentielles", "Herbes et huiles essentielles"
    COMPLEMENT_ALIMENTAIRE = "Complément alimentaire", "Complément alimentaire"
    INDETERMINE = "Produit alimentaire indéterminé", "Produit alimentaire indéterminé"
    SOUS_PRODUIT_ANIMAL = "Sous-produit animal", "Sous-produit animal"
    AUTRE_NON_ALIMENTAIRE = (
        "Autre produit non alimentaire",
        "Autre produit non alimentaire",
    )
    SANS_OBJET = "Sans objet", "Sans objet"

    @classmethod
    def build_options(cls):
        def insert_node(path, value, tree):
            current_level = tree
            for label in path[:-1]:
                existing = next((n for n in current_level if n["name"] == label), None)
                if not existing:
                    existing = {"name": label, "value": value, "children": []}
                    current_level.append(existing)
                current_level = existing["children"]
            current_level.append({"name": path[-1], "value": value, "children": []})

        options = []
        for option in cls:
            path = [p.strip() for p in option.label.split(">")]
            insert_node(path, option.value, options)

        for option in options:
            if option["children"] != []:
                option["isGroupSelectable"] = False
                option["value"] = 2 * option["value"]  # We can pick it we just need a unique value for TreeselectJS
        return options
