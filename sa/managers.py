from django.db import models
from django.db.models import Q

from core.managers import EvenementManagerMixin


class EvenementAnimalManager(models.Manager):
    def get_queryset(self):
        return EvenementAnimalQuerySet(self.model, using=self._db).filter(is_deleted=False)


class EvenementAnimalQuerySet(EvenementManagerMixin, models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def optimized_for_list(self):
        return self.select_related("maladie", "espece", "createur")

    def get_user_can_view(self, user):
        from sa.models import EvenementAnimal

        return self.filter(Q(createur=user.agent.structure) | ~Q(etat=EvenementAnimal.Etat.BROUILLON))
