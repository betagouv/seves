from dataclasses import dataclass
from enum import auto
import json

from django.db.models import TextChoices
from django.utils.functional import classproperty
from django.utils.safestring import mark_safe

from core.mixins import WithChoicesToJS
from ssa.constants import CategorieDanger


class EvenementOrigin(TextChoices):
    ANSES = "anses", "ANSES"
    ARS = "ars", "ARS"
    CONSUMER = "consommateur", "Consommateur"
    ETABLISSEMENT = "etablissement", "Établissement"
    DOCTOR = "medecin", "Médecin / Personnel médical"
    OTHER = "autre", "Autre"


class Motif(TextChoices):
    PARTAGE = "repas partage", "Repas partagé par la plupart des malades"
    COMPATIBLE = "repas compatible", "Repas compatible avec les délais d'incubations"
    RISQUE = "repas risque", "Repas comportant un aliment à risque particulier"


class MotifAliment(TextChoices):
    CONSOMME = "aliment consomme", "Aliment consommé par la plupart des malades"
    RISQUE = "aliment risque", "Aliment ou ingrédient à risque particulier"
    ANALYSE = "aliment analyse", "Aliment analysé et résultats positifs"


class TypeRepas(TextChoices):
    DOMICILE = "elabore a domicile", "Élaboré à domicile"
    EMBALLE = "emballe a la demande", "Élaboré à la demande à emporter ou livré"
    PRE_EMBALLE = "préemballe", "Préemballé consommé en l'état ou réchauffé"
    RESTAURATION_COLLECTIVE = "restauration collective", "Servi sur place restauration collective"
    RESTAURATION_COMMERCIALE = "restauration commerciale", "Servi sur place restauration commerciale"


class TypeCollectivite(TextChoices):
    JEUNES_ENFANTS = "jeunes enfants", "Jeunes enfants (0-5)"
    ENFANTS = "enfants", "Enfants (6-16)"
    ACCUEILS_MEDICALISES = "accueil medicalises", "Accueils médicalisés"
    ENTREPRISE = "entreprise", "Entreprise"
    PERSONNES_AGEES = "personnes agees", "Personnes agées"
    DIVERS_PUBLICS_SENSIBLES = "divers publics sensibles", "Divers publics sensibles"
    DIVERS_PUBLICS = "divers publics", "Divers publics"


class TypeAliment(TextChoices):
    CUISINE = "aliment cuisine", "Aliment cuisiné"
    SIMPLE = "aliment simple", "Matière première"


class ModaliteDeclarationEvenement(TextChoices):
    SIGNAL_CONSO = "signalconso", "SignalConso"
    OTHER = "autre", "Autre"


class EvenementFollowUp(TextChoices):
    NONE = "aucune suite", "Aucune suite"
    INSPECTION = "programmation futur controle", "Futur contrôle programmé"
    TRANSMISSION_DELEGATAIRE = "programmation au delegataire pour controle", "Transmis au délégataire pour contrôle"
    TRANSMISSION_DD = "programmation a une autre DD", "Transféré à une autre structure"
    INVESGTIGATION_TIAC = "investigation tiac", "Passé en investigation de TIAC"
    PASSE_EVENEMENT_PRODUIT = "passe en evenement produit", "Passé en événement produit"


@dataclass
class ChoiceData:
    value: str
    name: str
    help_text: str
    short_name: str
    description: str = ""
    html_id: str = ""


class SafeTextChoices(TextChoices):
    def __new__(cls, data: ChoiceData):
        obj = str.__new__(cls, data.value)
        obj._value_ = data.value
        obj.name_display = data.name
        obj.help_text = data.help_text
        obj.description = data.description
        obj.short_name = data.short_name
        obj.html_id = data.value.replace(" ", "-")
        return obj

    @property
    def label(self):
        return mark_safe(f'{self.name_display} <div class="fr-hint-text">{self.help_text}</div>')

    def to_dict(self):
        return {
            "value": self.value,
            "name": self.name_display,
            "help_text": self.help_text,
            "description": self.description,
            "html_id": self.html_id,
        }


class DangersSyndromiques(WithChoicesToJS, SafeTextChoices):
    INTOXINATION_BACILLUS = ChoiceData(
        value="intoxination bacillus cereus",
        name="Intoxination à toxine émétique thermostable préformée dans l'aliment à <span class='danger-emphasis'>bacillus cereus - staphylococcus aureus</span>",
        help_text="Incubation courte (30min - 8h) - nausées vomissements prédominants",
        short_name="Intoxination émétique bacillus cereus staphylococcus aureus",
        description="""Attention, autres toxines possibles notamment si haricots rouges, courges, produits de la mer, betterave crue... : conserver des échantillons pour d'autres analyses. <br/><br/>
Pour rappel : si les aliments ou ingrédients sont cuits, l'absence de la bactérie ne signifie pas l'absence de toxine (ces toxines sont thermostables). Si les aliments sont crus, en l'absence de la bactérie, il est inutile de rechercher les toxines. <br/><br/>
Staphylocoques : en première intention, recherche de la bactérie et des toxines A à E. Pour rechercher les autres toxines (si suspicion forte), envoi de la souche au LNR. Attention : l'absence de toxines A à E ne signifie pas l'absence de toxines staphylococciques. En l'absence de la bactérie, impossible de poursuivre les analyses. <br/><br/>
Bacillus cereus : en première intention, recherche de la bactérie. Pour rechercher ou doser les céréulides, envoi de la souche à l'ANSES. En l'absence de la bactérie, impossible de poursuivre les analyses.
        """,
    )
    TOXI_INFECTION_BACILLUS = ChoiceData(
        value="toxi infection bacillus cereus",
        name="Toxi-infection à toxine diarrhéique de <span class='danger-emphasis'>bacillus cereus - clostridium perfringens</span>",
        short_name="Toxi-infection diarrhéique bacillus cereus clostridium perfringens",
        help_text="Incubation moyenne (6h - 24h) - diarrhées aqueuses et douleurs abdominales prédominantes",
        description="Une contamination bactérienne importante des plats est attendue. Il est inutile de rechercher les toxines (sauf dossiers à enjeux particuliers). ",
    )
    BACTERIE_INTESTINALE = ChoiceData(
        value="bactérie intestinale",
        name="Infection bactérienne intestinale à <span class='danger-emphasis'>salmonella - campylobacter - yersinia enterocolitica - shigella - E. Coli</span> pathogènes",
        short_name="Infection bactérienne salmonella campylobacter",
        help_text="Incubation longue (Salmonella: 6 à 72 heures, Campylobacter: 2 à 5 jours, Yersinia enterocolitica: 3 à 7 jours, Shigella : 1 à 4 jours) - fièvre et diarrhées prédominants",
        description="""
        Compte tenu des délais d'incubation, les dates et heures d'apparition des symptômes sont étalées dans le temps, et les repas suspects sont aussi anciens.<br/><br/>
Attention, une gastro-entérite virale ou une infection par vibrio parahaemolyticus sont aussi à envisager. <br/><br/>
Bien récupérer et transmettre les informations de traçabilité si un ingrédient (oeuf, viande, crudité, coquillage, fromage...) est suspecté.<br/><br/>
Les souches sont à envoyer aux LNR.""",
    )
    SHU = ChoiceData(
        value="shu",
        name="Infection à <span class='danger-emphasis'>E. coli</span> STEC avec cas de syndrome hémolytique et urémique (SHU)",
        short_name="Syndrome hémolytique et urémique SHU",
        help_text="Incubation longue (1 à 10 jours) - diarrhées souvent sanglantes - puis complications en Syndrôme hémolytique et urémique",
        description="""
        Bien récupérer et transmettre les informations de traçabilité si un ingrédient (fromage au lait cru, crudité, viande hachée, pâte crue...) est suspecté. <br/><br/>Les souches sont à envoyer au LNR.""",
    )
    GASTRO = ChoiceData(
        value="gastro-enterite",
        name="Virus de la Gastro-entérite aigüe virale à norovirus, <span class='danger-emphasis'>sapovirus</span> etc.",
        short_name="Gastro-entérite aiguë virale",
        help_text="Incubation longue (10h - 50h) - tous symptômes de gastro-entérite, vomissements très fréquents, fièvre ~50% des cas - cas secondaires fréquents (transmission inter-humaine)",
        description="""Attention, une infection bactérienne à Salmonella etc. ou par vibrio parahaemolyticus est aussi à envisager.<br/><br/>
Bien récupérer et transmettre les informations de traçabilité si un ingrédient (coquillages, fruits rouges, crudité…) est suspecté.
        """,
    )
    VIBRIO_PARAHAEMOLYTICUS = ChoiceData(
        value="vibrio parahmeolyticus",
        name="Infection à <span class='danger-emphasis'>vibrio parahaemolyticus</span> (poissons ou fruits de mer crus ou peu cuits)",
        short_name="Infection vibrio parahaemolyticus",
        help_text="Incubation variable (2h à 48h) - diarrhées, douleurs abdominales, vomissements",
        description="""Bien récupérer et transmettre les informations de traçabilité des poissons ou fruits de mer qui ont été consommés crus ou peu cuits.<br/><br/>
Envoi direct au LNR pour analyse.
        """,
    )
    HISTAMINE = ChoiceData(
        value="histamine",
        name="Intoxination à l'histamine",
        short_name="Intoxination histamine",
        help_text="Incubation courte (1 minute à 3 heures) - urticaire, flush, sensation de brulure de la peau, de la bouche et/ou de la gorge, goût de poivre dans la bouche, palpitations cardiaques",
        description="""Principalement poissons (thon, maquereau, bonite...)  et aliments fermentés (fromages, boissons alcoolisées, charcuterie, fruits et légumes).""",
    )
    TOXINE_DES_COQUILLAGES = ChoiceData(
        value="toxine des coquillages",
        name="Intoxination par des coquillages : toxines lipophiles, PSP et autres toxines",
        short_name="Intoxination coquillages toxines lipophiles ASP PSP",
        help_text="Incubation courte (30 minutes à 3 heures) - Consommation de coquillages ou plats cuisinés comportant des coquillages - Toxines lipophiles : nausées, diarrhées, douleurs abdominales - Toxines PSP : diarrhées, nausées, vomissements, paresthésie de la bouche, des lèvres, dysphasie, paralysie respiratoire",
        description="",
    )
    TOXINE_DES_POISSONS = ChoiceData(
        value="toxine des poissons",
        name="Intoxination par des poissons coralliens : ciguatoxine",
        short_name="Intoxination ciguatoxine",
        help_text="Incubation courte (2 à 6 heures) - douleurs abdominales, nausées, vomissements, diarrhées, prurit, hypotension artérielle, bradycardie, symptômes neurologiques (parésthésies, faiblesse musculaire, etc)",
        description="Poissons des récifs coralliens (carangues, mérous, murènes, barracudas…) ",
    )
    AUTRE = ChoiceData(
        value="autre",
        name="Autres cas",
        short_name="Autres cas",
        help_text="Préciser les symptômes et les investigations médicales dans le contenu du signalement et dans le fil de suivi.",
        description="",
    )

    @classmethod
    def as_list(cls):
        return [
            cls.INTOXINATION_BACILLUS,
            cls.TOXI_INFECTION_BACILLUS,
            cls.BACTERIE_INTESTINALE,
            cls.SHU,
            cls.GASTRO,
            cls.VIBRIO_PARAHAEMOLYTICUS,
            cls.HISTAMINE,
            cls.TOXINE_DES_COQUILLAGES,
            cls.TOXINE_DES_POISSONS,
            cls.AUTRE,
        ]

    @classproperty
    def short_names(cls):
        return [item.short_name for item in cls]

    @classproperty
    def choices_short_names(cls):
        return [(item.value, item.short_name) for item in cls]


class EtatPrelevement(TextChoices):
    ENVIRONNEMENT_SURFACE = auto(), "Environnement/surface"
    AUTRE_LOT = auto(), "Plat ou ingrédient autre lot"
    MEME_LOT = auto(), "Plat ou ingrédient même lot"
    PLAT_TEMOIN = auto(), "Plat témoin"
    RESTE_REPAS = auto(), "Reste de repas"
    RESTE_INGREDIENT = auto(), "Reste d'ingrédient"


DANGERS_COURANTS = (
    CategorieDanger.STAPHYLOCOCCUS_AUREUS_ET_OU_SA_TOXINE,
    CategorieDanger.BACILLUS_CEREUS,
    CategorieDanger.CLOSTRIDIUM_PERFRINGENS,
    CategorieDanger.CAMPYLOBACTER_COLI,
    CategorieDanger.CAMPYLOBACTER_JEJUNI,
    CategorieDanger.SALMONELLA_ENTERITIDIS,
    CategorieDanger.SALMONELLA_TYPHIMURIUM,
    CategorieDanger.SHIGELLA,
    CategorieDanger.YERSINIA_ENTEROCOLITICA,
    CategorieDanger.HISTAMINE,
    CategorieDanger.TOXINE_DSP,
    CategorieDanger.VIRUS_DE_LA_GASTROENTERITE_AIGUE,
)


class SuspicionConclusion(TextChoices):
    CONFIRMED = auto(), "TIAC à agent confirmé"
    UNKNOWN = auto(), "TIAC à agent inconnu"
    SUSPECTED = auto(), "TIAC à agent suspecté"
    DISCARDED = auto(), "TIAC non retenue"

    @classproperty
    def no_clue(self):
        return tuple(item for item in self if item not in (self.CONFIRMED, self.SUSPECTED))

    @classmethod
    def as_json(cls):
        return json.dumps({item.name: {"value": item.value, "label": item.label} for item in cls})


SELECTED_HAZARD_CHOICES = (*DangersSyndromiques.choices_short_names, *CategorieDanger.choices)
