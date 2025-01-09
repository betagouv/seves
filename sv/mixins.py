class WithEtatMixin:
    def cloturer(self):
        from sv.models import Etat

        self.etat = Etat.get_etat_cloture()
        self.save()

    def can_be_cloturer_by(self, user):
        return not self.is_draft and not self.etat.is_cloture() and user.agent.structure.is_ac

    def is_already_cloturer(self):
        return self.etat.is_cloture()
