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

    def search(self, query):
        fields = [
            "contenu",
            "etablissements__raison_sociale",
            "etablissements__enseigne_usuelle",
        ]
        query_object = Q()
        for f in fields:
            query_object |= Q(**{f"{f}__unaccent__icontains": query})
        return self.filter(query_object)


class InvestigationTiacQueryset(EvenementManagerMixin, models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def get_user_can_view(self, user):
        from tiac.models import InvestigationTiac

        return self.filter(Q(createur=user.agent.structure) | ~Q(etat=InvestigationTiac.Etat.BROUILLON))

    def with_fin_de_suivi(self, contact):
        from .models import InvestigationTiac

        return self._with_fin_de_suivi(contact, InvestigationTiac)

    def search(self, query):
        fields = [
            "contenu",
            "precisions",
            "etablissements__raison_sociale",
            "etablissements__enseigne_usuelle",
            "repas__denomination",
            "repas__menu",
            "aliments__denomination",
            "aliments__categorie_produit",
            "aliments__description_produit",
            "analyses_alimentaires__reference_prelevement",
            "analyses_alimentaires__comments",
        ]
        query_object = Q()
        for f in fields:
            query_object |= Q(**{f"{f}__unaccent__icontains": query})
        return self.filter(query_object)


class EvenementSimpleManager(models.Manager):
    def get_queryset(self):
        return EvenementSimpleQueryset(self.model, using=self._db).filter(is_deleted=False)


class InvestigationTiacManager(models.Manager):
    def get_queryset(self):
        return InvestigationTiacQueryset(self.model, using=self._db).filter(is_deleted=False)
