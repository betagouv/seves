from dataclasses import dataclass
from datetime import datetime

from tiac.models import EvenementSimple, InvestigationTiac


@dataclass
class DisplayItem:
    numero: str
    absolute_url: str
    createur: str
    date_publication: str
    nb_sick_persons: str
    type_evenement: str
    conclusion: str
    danger_retenu: list[str]
    etat: str
    readable_etat: str
    etablissements: list[str]
    last_update: datetime

    @classmethod
    def from_evenement_simple(cls, evenement_simple: EvenementSimple):
        nb_sick_persons = evenement_simple.nb_sick_persons
        return cls(
            numero=evenement_simple.numero,
            absolute_url=evenement_simple.get_absolute_url(),
            createur=str(evenement_simple.createur),
            date_publication=evenement_simple.date_creation.strftime("%d/%m/%Y"),
            nb_sick_persons=str(nb_sick_persons if nb_sick_persons is not None else "-"),
            type_evenement=f"Enr. simple / {evenement_simple.get_follow_up_display() if evenement_simple.get_follow_up_display() else '-'}",
            conclusion="-",
            danger_retenu=[],
            etat=evenement_simple.etat,
            readable_etat=evenement_simple.readable_etat,
            etablissements=[e.displayed_name for e in evenement_simple.etablissements.all()],
            last_update=evenement_simple.last_updated,
        )

    @classmethod
    def from_investigation_tiac(cls, investigation_tiac: InvestigationTiac):
        nb_sick_persons = investigation_tiac.nb_sick_persons
        return cls(
            numero=investigation_tiac.numero,
            absolute_url=investigation_tiac.get_absolute_url(),
            createur=str(investigation_tiac.createur),
            date_publication=investigation_tiac.date_creation.strftime("%d/%m/%Y"),
            nb_sick_persons=str(nb_sick_persons if nb_sick_persons is not None else "-"),
            type_evenement=investigation_tiac.type_evenement_display,
            conclusion=investigation_tiac.get_suspicion_conclusion_display() or "-",
            danger_retenu=investigation_tiac.short_conclusion_selected_hazard,
            etat=investigation_tiac.etat,
            readable_etat=investigation_tiac.readable_etat,
            etablissements=[e.displayed_name for e in investigation_tiac.etablissements.all()],
            last_update=investigation_tiac.last_updated,
        )

    @classmethod
    def from_object(cls, obj):
        if isinstance(obj, EvenementSimple):
            return DisplayItem.from_evenement_simple(obj)
        if isinstance(obj, InvestigationTiac):
            return DisplayItem.from_investigation_tiac(obj)
        raise NotImplementedError
