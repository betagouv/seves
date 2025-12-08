import abc
import typing

from django.utils.safestring import mark_safe

if typing.TYPE_CHECKING:
    from ssa.models import EvenementProduit, EvenementInvestigationCasHumain


class EvenementDisplay(abc.ABC):
    def __new__(cls, evenement):
        from ssa.models import EvenementInvestigationCasHumain, EvenementProduit

        if isinstance(evenement, EvenementProduit):
            return super().__new__(EvenementProduitDisplay)
        elif isinstance(evenement, EvenementInvestigationCasHumain):
            return super().__new__(InvestigationCasHumainDisplay)
        raise TypeError(f"Unexpected type {type(evenement)}")

    def __init__(self, evenement):
        self.evenement = evenement

    @property
    def date_creation(self):
        return self.evenement.date_creation

    @property
    def numero(self):
        return self.evenement.numero

    @property
    def createur(self):
        return self.evenement.createur

    @property
    def description(self):
        return self.evenement.description

    @property
    def etat(self):
        if not hasattr(self, "_etat"):
            self._init_etat_data()
        return self._etat

    @property
    def readable_etat(self):
        if not hasattr(self, "_readable_etat"):
            self._init_etat_data()
        return self._readable_etat

    @abc.abstractmethod
    def get_absolute_url(self): ...

    @abc.abstractmethod
    def get_categorie_produit_display(self): ...

    @abc.abstractmethod
    def get_categorie_danger_display(self): ...

    @abc.abstractmethod
    def get_type_evenement_display(self): ...

    def _init_etat_data(self):
        etat_data = self.evenement.get_etat_data_from_fin_de_suivi(self.evenement.has_fin_de_suivi)
        self._etat = etat_data["etat"]
        self._readable_etat = etat_data["readable_etat"]


class EvenementProduitDisplay(EvenementDisplay):
    def __init__(self, evenement: "EvenementProduit"):
        super().__init__(evenement)

    def get_absolute_url(self):
        return self.evenement.get_absolute_url()

    def get_categorie_produit_display(self):
        return self.evenement.get_categorie_produit_display()

    def get_categorie_danger_display(self):
        return self.evenement.get_categorie_danger_display()

    def get_type_evenement_display(self):
        return self.evenement.get_type_evenement_display()


class InvestigationCasHumainDisplay(EvenementDisplay):
    def __init__(self, evenement: "EvenementInvestigationCasHumain"):
        super().__init__(evenement)

    def get_absolute_url(self):
        return self.evenement.get_absolute_url()

    def get_categorie_produit_display(self):
        # language=html
        return mark_safe("<em>Non applicable</em>")

    def get_categorie_danger_display(self):
        # language=html
        return mark_safe("<em>Non applicable</em>")

    def get_type_evenement_display(self):
        # language=html
        return mark_safe("<em>Non applicable</em>")
