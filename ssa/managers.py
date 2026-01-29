import abc
from typing import Iterable

from django.db import models
from django.db.models import Q

from core.managers import EvenementManagerMixin


class EvenementBaseQueryset(EvenementManagerMixin, models.QuerySet, abc.ABC):
    @property
    @abc.abstractmethod
    def search_fields(self) -> Iterable[str]:
        pass

    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def get_user_can_view(self, user):
        from core.mixins import WithEtatMixin

        return self.filter(Q(createur=user.agent.structure) | ~Q(etat=WithEtatMixin.Etat.BROUILLON))

    def with_fin_de_suivi(self, contact):
        return self._with_fin_de_suivi(contact, self.model)

    def search(self, query):
        query_object = Q()
        for f in self.search_fields:
            query_object |= Q(**{f"{f}__unaccent__icontains": query})
        return self.filter(query_object)


class EvenementProduitQueryset(EvenementBaseQueryset):
    @property
    def search_fields(self) -> Iterable[str]:
        return (
            "description",
            "denomination",
            "marque",
            "etablissements__raison_sociale",
            "etablissements__enseigne_usuelle",
            "evaluation",
            "lots",
            "description_complementaire",
            "precision_danger",
        )

    def optimized_for_list(self):
        return self.only(
            "id",
            "numero_annee",
            "numero_evenement",
            "createur_id",
            "description",
            "categorie_danger",
            "type_evenement",
            "date_creation",
            "etat",
            "categorie_produit",
        )


class EvenementProduitManager(models.Manager):
    def get_queryset(self):
        return EvenementProduitQueryset(self.model, using=self._db).filter(is_deleted=False)

    def with_departement_prefetched(self):
        return (
            self.get_queryset()
            .prefetch_related("etablissements__departement")
            .prefetch_related("etablissements__departement__region")
        )


class InvestigationCasHumainQueryset(EvenementBaseQueryset):
    @property
    def search_fields(self) -> Iterable[str]:
        return (
            "description",
            "precision_danger",
            "evaluation",
            "etablissements__raison_sociale",
            "etablissements__enseigne_usuelle",
        )

    def optimized_for_list(self):
        return self.only(
            "id",
            "numero_annee",
            "numero_evenement",
            "createur_id",
            "description",
            "categorie_danger",
            "date_creation",
            "etat",
        )


class InvestigationCasHumainManager(models.Manager):
    def get_queryset(self):
        return InvestigationCasHumainQueryset(self.model, using=self._db).filter(is_deleted=False)

    def with_departement_prefetched(self):
        return (
            self.get_queryset()
            .prefetch_related("etablissements__departement")
            .prefetch_related("etablissements__departement__region")
        )
