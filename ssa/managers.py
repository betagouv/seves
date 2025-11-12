from django.db import models
from django.db.models import Q

from core.managers import EvenementManagerMixin


class EvenementProduitManager(models.Manager):
    def get_queryset(self):
        return EvenementProduitQueryset(self.model, using=self._db).filter(is_deleted=False)

    def with_departement_prefetched(self):
        return (
            self.get_queryset()
            .prefetch_related("etablissements__departement")
            .prefetch_related("etablissements__departement__region")
        )


class EvenementProduitQueryset(EvenementManagerMixin, models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def get_user_can_view(self, user):
        from ssa.models import EvenementProduit

        return self.filter(Q(createur=user.agent.structure) | ~Q(etat=EvenementProduit.Etat.BROUILLON))

    def with_fin_de_suivi(self, contact):
        from ssa.models import EvenementProduit

        return self._with_fin_de_suivi(contact, EvenementProduit)

    def search(self, query):
        fields = [
            "description",
            "denomination",
            "marque",
            "etablissements__raison_sociale",
            "evaluation",
            "lots",
            "description_complementaire",
        ]
        query_object = Q()
        for f in fields:
            query_object |= Q(**{f"{f}__unaccent__icontains": query})
        return self.filter(query_object)
