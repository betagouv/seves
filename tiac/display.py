from dataclasses import dataclass

from tiac.models import EvenementSimple, InvestigationTiac


@dataclass
class DisplayItem:
    numero: str
    absolute_url: str
    createur: str
    date_reception: str
    nb_sick_persons: str
    type_evenement: str
    etat: str
    readable_etat: str

    @classmethod
    def from_evenement_simple(cls, evenement_simple: EvenementSimple):
        nb_sick_persons = evenement_simple.nb_sick_persons
        return cls(
            numero=evenement_simple.numero,
            absolute_url=evenement_simple.get_absolute_url(),
            createur=str(evenement_simple.createur),
            date_reception=evenement_simple.date_reception.strftime("%d/%m/%Y"),
            nb_sick_persons=str(nb_sick_persons if nb_sick_persons is not None else "-"),
            type_evenement=f"Enr. simple / {evenement_simple.get_follow_up_display() if evenement_simple.get_follow_up_display() else '-'}",
            etat=evenement_simple.etat,
            readable_etat=evenement_simple.readable_etat,
        )

    @classmethod
    def from_investigation_tiac(cls, investigation_tiac: InvestigationTiac):
        return cls(
            numero=investigation_tiac.numero,
            absolute_url=investigation_tiac.get_absolute_url(),
            createur=str(investigation_tiac.createur),
            date_reception=investigation_tiac.date_reception.strftime("%d/%m/%Y"),
            nb_sick_persons="-",
            type_evenement=investigation_tiac.type_evenement_display,
            etat=investigation_tiac.etat,
            readable_etat=investigation_tiac.readable_etat,
        )

    @classmethod
    def from_object(cls, obj):
        if isinstance(obj, EvenementSimple):
            return DisplayItem.from_evenement_simple(obj)
        if isinstance(obj, InvestigationTiac):
            return DisplayItem.from_investigation_tiac(obj)
        raise NotImplementedError
