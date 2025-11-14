from django.core.exceptions import PermissionDenied
from django.db import models


class AllowsSoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False)

    def can_user_delete(self, user):
        raise NotImplementedError

    def can_be_deleted(self, user):
        return self.can_user_delete(user)

    def soft_delete(self, user):
        if not self.can_be_deleted(user):
            raise PermissionDenied
        self.is_deleted = True
        self.save()

    def get_soft_delete_success_message(self):
        return "L'objet a bien été supprimé"

    def get_soft_delete_permission_error_message(self):
        return "Vous n'avez pas les droits pour supprimer cet objet"

    def get_soft_delete_attribute_error_message(self):
        return "Ce type d'objet ne peut pas être supprimé"

    def get_soft_delete_confirm_title(self):
        return "Supprimer cet objet"

    def get_soft_delete_confirm_message(self):
        return "Cette action est irréversible. Confirmez-vous la suppression de cet objet ?"

    class Meta:
        abstract = True
