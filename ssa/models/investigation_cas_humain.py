import reversion
from django.db import models

from core.mixins import WithFreeLinkIdsMixin, AllowModificationMixin
from core.soft_delete_mixins import AllowsSoftDeleteMixin
from ssa.models.mixins import WithEvenementInformationMixin, WithEvenementRisqueMixin


@reversion.register(follow=("contacts",))
class EvenementInvestigationCasHumain(
    AllowsSoftDeleteMixin,
    WithEvenementInformationMixin,
    WithEvenementRisqueMixin,
    AllowModificationMixin,
    WithFreeLinkIdsMixin,
    models.Model,
): ...
