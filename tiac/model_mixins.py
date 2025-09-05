import datetime

from core.mixins import WithNumeroMixin


class WithSharedNumeroMixin(WithNumeroMixin):
    @classmethod
    def _get_annee_and_numero(cls):
        from .models import EvenementSimple, InvestigationTiac

        annee_courante = datetime.datetime.now().year

        def last_num(model):
            fiche = (
                model._base_manager.filter(numero_annee=annee_courante)
                .select_for_update()
                .order_by("-numero_evenement")
                .first()
            )
            return fiche.numero_evenement if fiche else 0

        numero = max(last_num(EvenementSimple), last_num(InvestigationTiac)) + 1
        return annee_courante, numero

    class Meta:
        abstract = True


# TODO admin
