from dataclasses import dataclass
from sv.models import FicheDetection, OrganismeNuisible, FicheZoneDelimitee, Etat


@dataclass
class DisplayedFiche:
    type: str
    numero: str
    organisme_nuisible: OrganismeNuisible
    date_creation: str
    createur: str
    communes_list: list[str]
    etat: Etat
    is_ac_notified: bool
    visibilite: str
    get_absolute_url: str

    @classmethod
    def from_fiche_zone(cls, fiche: FicheZoneDelimitee):
        return cls(
            type="Zone",
            numero=str(fiche.numero),
            organisme_nuisible=fiche.organisme_nuisible,
            is_ac_notified=False,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            etat=None,
            visibilite="",
            communes_list=[],
            get_absolute_url=fiche.get_absolute_url(),
        )

    @classmethod
    def from_fiche_detection(cls, fiche: FicheDetection):
        return cls(
            type="Détection",
            numero=str(fiche.numero),
            organisme_nuisible=fiche.organisme_nuisible,
            is_ac_notified=fiche.is_ac_notified,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            etat=fiche.etat,
            visibilite=str(fiche.visibilite),
            communes_list=fiche.lieux_list,
            get_absolute_url=fiche.get_absolute_url(),
        )
