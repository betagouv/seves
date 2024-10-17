from dataclasses import dataclass
from sv.models import FicheDetection, OrganismeNuisible, FicheZoneDelimitee


@dataclass
class DisplayedFiche:
    type: str
    numero: str
    organisme_nuisible: OrganismeNuisible
    date_creation: str
    createur: str
    communes_list: list[str]
    etat: str
    is_ac_notified: bool
    visibilite: str
    url: str

    @classmethod
    def from_fiche_zone(cls, fiche: FicheZoneDelimitee):
        return cls(
            type="Zone",
            numero=str(fiche.numero),
            organisme_nuisible="TODO", # TODO waiting for more details for design
            url="TODO", # TODO waiting for details view @alan
            is_ac_notified=False,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            etat="TODO", # TODO waiting for Alan
            visibilite="TODO", # TODO waiting for Alan
            communes_list=[] # TODO waiting for more details for design
        )

    # TODO vérifier sur main que tout est similaire
    @classmethod
    def from_fiche_detection(cls, fiche: FicheDetection):
        return cls(
            type="Détection",
            numero=str(fiche.numero),
            organisme_nuisible=fiche.organisme_nuisible,
            url=fiche.get_absolute_url,
            is_ac_notified=fiche.is_ac_notified,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            etat=str(fiche.etat),
            visibilite=str(fiche.visibilite),
            communes_list=fiche.lieux_list
        )
