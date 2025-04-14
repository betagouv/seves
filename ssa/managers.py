from django.db import models
from django.db.models import Q


class EvenementProduitManager(models.Manager):
    def get_queryset(self):
        return EvenementProduitQueryset(self.model, using=self._db).all()


class EvenementProduitQueryset(models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def get_user_can_view(self, user):
        from ssa.models import EvenementProduit

        return self.filter(Q(createur=user.agent.structure) | ~Q(etat=EvenementProduit.Etat.BROUILLON))
