from django.utils import timezone


class WithDerniereMiseAJourManagerMixin:
    def update_date_derniere_mise_a_jour(self, object_id):
        return self.filter(pk=object_id).update(date_derniere_mise_a_jour=timezone.now())
