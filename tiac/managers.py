from django.db import models
from django.db.models import Q

from core.managers import EvenementManagerMixin


class EvenementSimpleQueryset(EvenementManagerMixin, models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def get_user_can_view(self, user):
        from tiac.models import EvenementSimple

        return self.filter(Q(createur=user.agent.structure) | ~Q(etat=EvenementSimple.Etat.BROUILLON))

    def with_fin_de_suivi(self, contact):
        from .models import EvenementSimple

        return self._with_fin_de_suivi(contact, EvenementSimple)


class EvenementSimpleManager(models.Manager):
    def get_queryset(self):
        return EvenementSimpleQueryset(self.model, using=self._db).filter(is_deleted=False)
