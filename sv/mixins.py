from django.db import models


# TODO move this to core ?
class WithEtatMixin(models.Model):
    class Etat(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        EN_COURS = "en_cours", "En cours"
        CLOTURE = "cloture", "Clôturé"

    etat = models.CharField(max_length=100, choices=Etat, verbose_name="État de l'événement", default=Etat.BROUILLON)

    class Meta:
        abstract = True

    def cloturer(self):
        self.etat = self.Etat.CLOTURE
        self.save()

    def publish(self):
        self.etat = self.Etat.EN_COURS
        self.save()

    @property
    def is_draft(self):
        return self.etat == self.Etat.BROUILLON

    def can_publish(self, user):
        return user.agent.is_in_structure(self.createur) if self.is_draft else False

    def can_be_cloturer_by(self, user):
        return not self.is_draft and not self.is_already_cloturer() and user.agent.structure.is_ac

    def is_already_cloturer(self):
        return self.etat == self.Etat.CLOTURE
