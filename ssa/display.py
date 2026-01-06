import dataclasses
import typing
from datetime import datetime


if typing.TYPE_CHECKING:
    from core.models import Structure
    from ssa.models import EvenementProduit, EvenementInvestigationCasHumain


@dataclasses.dataclass
class EvenementDisplay:
    date_creation: datetime
    numero: str
    createur: "Structure"
    description: str
    etat: str
    readable_etat: str
    absolute_url: str
    categorie_produit: str
    categorie_danger: str
    type_evenement: str

    @staticmethod
    def from_evenement(evenement: "EvenementProduit | EvenementInvestigationCasHumain"):
        from ssa.models import EvenementProduit

        if isinstance(evenement, EvenementProduit):
            categorie_produit = evenement.get_categorie_produit_display() or "-"
            categorie_danger = evenement.get_categorie_danger_display() or "-"
        else:
            categorie_produit = "-"
            categorie_danger = "-"

        etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)

        return EvenementDisplay(
            date_creation=evenement.date_creation,
            numero=evenement.numero,
            createur=evenement.createur,
            description=evenement.description,
            etat=etat_data["etat"],
            readable_etat=etat_data["readable_etat"],
            absolute_url=evenement.get_absolute_url(),
            categorie_produit=categorie_produit,
            categorie_danger=categorie_danger,
            type_evenement=evenement.get_type_evenement_display(),
        )
