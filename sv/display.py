from dataclasses import dataclass
from sv.models import FicheDetection, OrganismeNuisible, FicheZoneDelimitee


@dataclass
class DisplayedFiche:
    type: str
    numero: str
    numero_evenement: str
    organisme_nuisible: OrganismeNuisible
    date_creation: str
    createur: str
    communes_list: list[str]
    etat: str
    readable_etat: str
    is_ac_notified: bool
    visibilite: str
    get_absolute_url: str
    nb_related_objects: int

    @classmethod
    def from_fiche_zone(cls, fiche: FicheZoneDelimitee):
        return cls(
            type="Z",
            numero=str(fiche.evenement.numero) if fiche.evenement.numero else "non attribué",
            organisme_nuisible=fiche.evenement.organisme_nuisible,
            is_ac_notified=fiche.evenement.is_ac_notified,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            visibilite=str(fiche.evenement.visibilite),
            etat=fiche.evenement.etat,
            readable_etat=fiche.evenement.get_etat_display(),
            communes_list=[],
            get_absolute_url=fiche.get_absolute_url() + "#tabpanel-zone-panel",
            numero_evenement=str(fiche.evenement.numero) if fiche.evenement.numero else "non attribué",
            nb_related_objects=fiche.nb_fiches_detection,
        )

    @classmethod
    def from_fiche_detection(cls, fiche: FicheDetection):
        return cls(
            type="D",
            numero=fiche.numero,
            organisme_nuisible=fiche.evenement.organisme_nuisible,
            is_ac_notified=fiche.evenement.is_ac_notified,
            date_creation=fiche.date_creation.strftime("%d/%m/%Y"),
            createur=str(fiche.createur),
            etat=fiche.evenement.etat,
            readable_etat=fiche.evenement.get_etat_display(),
            visibilite=str(fiche.evenement.visibilite),
            communes_list=fiche.lieux_list_with_commune,
            get_absolute_url=fiche.get_absolute_url() + f"?detection={fiche.pk}",
            numero_evenement=str(fiche.evenement.numero) if fiche.evenement.numero else "non attribué",
            nb_related_objects=1 if fiche.evenement.fiche_zone_delimitee_id else 0,
        )
