from dataclasses import dataclass
from sv.models import FicheDetection, OrganismeNuisible, FicheZoneDelimitee, Etat


@dataclass
class DisplayedLink:
    enabled: bool
    url: str
    icon: str
    text: str

    @classmethod
    def from_fiche_zone(cls, fiche: FicheZoneDelimitee):
        return cls(
            enabled=True,
            url="",
            icon="ri-node-tree",
            text=fiche.nb_fiches_detection,
        )

    @classmethod
    def from_fiche_detection(cls, fiche: FicheDetection):
        zone = fiche.get_fiche_zone_delimitee()
        return cls(
            enabled=bool(zone),
            url=zone.get_absolute_url() if zone else "",
            icon="ri-focus-line",
            text=str(zone) if zone else "Pas de zone",
        )


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
    link: DisplayedLink

    @classmethod
    def from_fiche_zone(cls, fiche: FicheZoneDelimitee):
        return cls(
            type="Zone",
            numero=str(fiche.numero) if fiche.numero else "non attribué",
            organisme_nuisible=fiche.organisme_nuisible,
            is_ac_notified=False,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            visibilite=str(fiche.visibilite),
            etat=fiche.etat,
            communes_list=[],
            get_absolute_url=fiche.get_absolute_url(),
            link=DisplayedLink.from_fiche_zone(fiche),
        )

    @classmethod
    def from_fiche_detection(cls, fiche: FicheDetection):
        return cls(
            type="Détection",
            numero=str(fiche.numero) if fiche.numero else "non attribué",
            organisme_nuisible=fiche.organisme_nuisible,
            is_ac_notified=fiche.is_ac_notified,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            etat=fiche.etat,
            visibilite=str(fiche.visibilite),
            communes_list=fiche.lieux_list_with_commune,
            get_absolute_url=fiche.get_absolute_url(),
            link=DisplayedLink.from_fiche_detection(fiche),
        )
