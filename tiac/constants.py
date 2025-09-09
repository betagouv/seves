from dataclasses import dataclass

from django.db.models import TextChoices
from django.utils.safestring import mark_safe


class EvenementOrigin(TextChoices):
    ARS = "ars", "ARS"
    CONSUMER = "consommateur", "Consommateur"
    ETABLISSEMENT = "etablissement", "Établissement"
    DOCTOR = "medecin", "Médecin / Personnel médical"
    OTHER = "autre", "Autre"


class ModaliteDeclarationEvenement(TextChoices):
    SIGNAL_CONSO = "signalconso", "SignalConso"
    OTHER = "autre", "Autre"


class EvenementFollowUp(TextChoices):
    NONE = "aucune suite", "Aucune suite"
    INSPECTION = "programmation futur controle", "Programmation d’un futur contrôle"


@dataclass
class ChoiceData:
    value: str
    name: str
    help_text: str
    description: str = ""
    html_id: str = ""


class SafeTextChoices(TextChoices):
    def __new__(cls, data: ChoiceData):
        obj = str.__new__(cls, data.value)
        obj._value_ = data.value
        obj.name_display = data.name
        obj.help_text = data.help_text
        obj.description = data.description
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


class DangersSyndromiques(SafeTextChoices):
    INTOXINATION_BACILLUS = ChoiceData(
        value="intoxination bacillus cereus",
        name="Intoxination à toxine émétique thermostable préformée dans l'aliment à <b>bacillus cereus - staphylococcus aureus</b>",
        help_text="Incubation courte (30min - 8h) - nausées vomissements prédominants",
        description="""Attention, autres toxines possibles notamment si haricots rouges, courges, produits de la mer, betterave crue... : conserver des échantillons pour d'autres analyses. <br/><br/>
Pour rappel : si les aliments ou ingrédients sont cuits, l'absence de la bactérie ne signifie pas l'absence de toxine (ces toxines sont thermostables). Si les aliments sont crus, en l'absence de la bactérie, il est inutile de rechercher les toxines. <br/><br/>
Staphylocoques : en première intention, recherche de la bactérie et des toxines A à E. Pour rechercher les autres toxines (si suspicion forte), envoi de la souche au LNR. Attention : l'absence de toxines A à E ne signifie pas l'absence de toxines staphylococciques. En l'absence de la bactérie, impossible de poursuivre les analyses. <br/><br/>
Bacillus cereus : en première intention, recherce de la bactérie. Pour rechercher ou doser les céréulides, envoi de la souche à l'ANSES. En l'absence de la bactérie, impossible de poursuivre les analyses.
        """,
    )
    TOXI_INFECTION_BACILLUS = ChoiceData(
        value="toxi infection bacillus cereus",
        name="Toxi-infection à toxine diarrhéique de <b>bacillus cereus - clostridium perfringens</b>",
        help_text="Incubation moyenne (6h - 24h) - diarrhées aqueuses et douleurs abdominales prédominantes",
        description="Une contamination bactérienne importante des plats est attendue. Il est inutile de rechercher les toxines (sauf dossiers à enjeux particuliers). ",
    )
    BACTERIE_INTESTINALE = ChoiceData(
        value="bactérie intestinale",
        name="Infection bactérienne intestinale à <b>salmonella - campylobacter - yersinia enterocolitica - shigella - E. Coli</b> pathogènes",
        help_text="Incubation longue (Salmonella: 6 à 72 heures, Campylobacter: 2 à 5 jours, Yersinia enterocolitica: 3 à 7 jours, Shigella : 1 à 4 jours) - fièvre et diarrhées prédominants",
        description="""
        Compte tenu des délais d'incubation, les dates et heures d'apparition des symptômes sont étalées dans le temps, et les repas suspects sont aussi anciens.<br/><br/>
Attention, une gastro-entérite virale ou une infection par vibrio parahaemolyticus sont aussi à envisager. <br/><br/>
Bien récupérer et transmettre les informations de traçabilité si un ingrédient (oeuf, viande, crudité, coquillage, fromage...) est suspecté.<br/><br/>
Les souches sont à envoyer aux LNR.""",
    )
    SHU = ChoiceData(
        value="shu",
        name="Infection à <b>E. coli</b> STEC avec cas de syndrome hémolytique et urémique (SHU)",
        help_text="Incubation longue (1 à 10 jours) - diarrhées souvent sanglantes - puis complications en Syndrôme hémolytique et urémique",
        description="""
        Bien récupérer et transmettre les informations de traçabilité si un ingrédient (fromage au lait cru, crudité, viande hachée, pâte crue...) est suspecté. <br/><br/>Les souches sont à envoyer au LNR.""",
    )
    GASTRO = ChoiceData(
        value="gastro-enterite",
        name="Gastro-entérite aigüe virale à norovirus, <b>sapovirus</b> etc.",
        help_text="Incubation longue (10h - 50h) - tous symptômes de gastro-entérite, vomissements très fréquents, fièvre ~50% des cas - cas secondaires fréquents (transmission inter-humaine)",
        description="""Attention, une infection bactérienne à Salmonella etc. ou par vibrio parahaemolyticus est aussi à envisager.<br/><br/>
Bien récupérer et transmettre les informations de traçabilité si un ingrédient (coquillages, fruits rouges, crudité…) est suspecté.
        """,
    )
    VIBRIO_PARAHAEMOLYTICUS = ChoiceData(
        value="vibrio parahmeolyticus",
        name="Infection à <b>vibrio parahaemolyticus</b> (poissons ou fruits de mer crus ou peu cuits)",
        help_text="Incubation variable (2h à 48h) - diarrhées, douleurs abdominales, vomissements",
        description="""Bien récupérer et transmettre les informations de traçabilité des poissons ou fruits de mer qui ont été consommés crus ou peu cuits.<br/><br/>
Envoi direct au LNR pour analyse.
        """,
    )
    HISTAMINE = ChoiceData(
        value="histamine",
        name="Intoxination à l'histamine",
        help_text="Incubation courte (1 minute à 3 heures) - urticaire, flush, sensation de brulure de la peau, de la bouche et/ou de la gorge, goût de poivre dans la bouche, palpitations cardiaques",
        description="""Principalement poissons (thon, maquereau, bonite...)  et aliments fermentés (fromages, boissons alcoolisées, charcuterie, fruits et légumes).""",
    )
    TOXINE_DES_COQUILLAGES = ChoiceData(
        value="toxine des coquillages",
        name="Intoxination par des coquillages : toxines lipophiles, PSP et autres toxines",
        help_text="Incubation courte (30 minutes à 3 heures) - Consommation de coquillages ou plats cuisinés comportant des coquillages - Toxines lipophiles : nausées, diarrhées, douleurs abdominales - Toxines PSP : diarrhées, nausées, vomissements, paresthésie de la bouche, des lèvres, dysphasie, paralysie respiratoire",
        description="",
    )
    TOXINE_DES_POISSONS = ChoiceData(
        value="toxine des poissons",
        name="Intoxination par des poissons coralliens : ciguatoxine",
        help_text="Incubation courte (2 à 6 heures) - douleurs abdominales, nausées, vomissements, diarrhées, prurit, hypotension artérielle, bradycardie, symptômes neurologiques (parésthésies, faiblesse musculaire, etc)",
        description="Poissons des récifs coralliens (carangues, mérou, murènes, barracuda...) ",
    )
    AUTRE = ChoiceData(
        value="autre",
        name="Autres cas",
        help_text="Préciser les symptômes et les investigations médicales dans la description de l'évènement et dans le fil de suivi. ",
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
