import reversion
from django.db import models

from core.mixins import (
    AllowsSoftDeleteMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithNumeroMixin,
    WithFreeLinkIdsMixin,
)
from core.models import Structure
from tiac.constants import ModaliteDeclarationEvenement, EvenementOrigin, EvenementFollowUp


@reversion.register()
class EvenementSimple(
    AllowsSoftDeleteMixin,
    WithContactPermissionMixin,
    WithEtatMixin,
    WithNumeroMixin,
    WithFreeLinkIdsMixin,
    models.Model,
):
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_reception = models.DateTimeField(verbose_name="Date de réception à la DD(ETS)PP")
    evenement_origin = models.IntegerField(choices=EvenementOrigin.choices, verbose_name="Signalement déclaré par")
    modalites_declaration = models.IntegerField(
        choices=ModaliteDeclarationEvenement.choices,
        default=ModaliteDeclarationEvenement.SIGNAL_CONSO,
        verbose_name="Modalités de déclaration",
    )
    contenu = models.TextField(verbose_name="Contenu du signalement")
    notify_ars = models.BooleanField(default=False, verbose_name="ARS informée")
    nb_sick_persons = models.IntegerField(verbose_name="Nombre de malades total")

    follow_up = models.IntegerField(
        choices=EvenementFollowUp.choices, default=EvenementFollowUp.NONE, verbose_name="Suite donnée par la DD"
    )

    etablissements = models.ManyToManyField("ssa.Etablissement", verbose_name="Établissements impliqués")
