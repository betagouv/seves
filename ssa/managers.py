from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, Exists, OuterRef, Func, F, Subquery

from core.models import FinSuiviContact, LienLibre


class EvenementProduitManager(models.Manager):
    def get_queryset(self):
        return EvenementProduitQueryset(self.model, using=self._db).filter(is_deleted=False)


class EvenementProduitQueryset(models.QuerySet):
    def order_by_numero(self):
        return self.order_by("-numero_annee", "-numero_evenement")

    def get_user_can_view(self, user):
        from ssa.models import EvenementProduit

        return self.filter(Q(createur=user.agent.structure) | ~Q(etat=EvenementProduit.Etat.BROUILLON))

    def with_fin_de_suivi(self, contact):
        from ssa.models import EvenementProduit

        content_type = ContentType.objects.get_for_model(EvenementProduit)
        return self.annotate(
            has_fin_de_suivi=Exists(
                FinSuiviContact.objects.filter(content_type=content_type, object_id=OuterRef("pk"), contact=contact)
            )
        )

    def with_nb_liens_libres(self):
        from ssa.models import EvenementProduit

        content_type = ContentType.objects.get_for_model(EvenementProduit)

        liens = (
            LienLibre.objects.filter(
                Q(content_type_1=content_type, object_id_1=OuterRef("pk"))
                | Q(content_type_2=content_type, object_id_2=OuterRef("pk"))
            )
            .annotate(count=Func(F("id"), function="Count"))
            .values("count")
        )
        return self.annotate(nb_liens_libre=Subquery(liens))
