from django.db import models

from core.models import Structure, Document, LienLibre
from ssa.models.validators import validate_numero_rasff
from .categorie_danger import CategorieDanger


class BaseSSAEvenement(models.Model):
    createur = models.ForeignKey(Structure, on_delete=models.PROTECT, verbose_name="Structure créatrice")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    numero_rasff = models.CharField(
        max_length=9, verbose_name="N° RASFF/AAC", blank=True, validators=[validate_numero_rasff]
    )
    description = models.TextField(verbose_name="Description de l'événement")

    # Informations liées au risque
    categorie_danger = models.CharField(
        max_length=255, choices=CategorieDanger.choices, verbose_name="Catégorie de danger", blank=True
    )
    precision_danger = models.CharField(blank=True, max_length=255, verbose_name="Précision danger")
    reference_souches = models.CharField(max_length=255, verbose_name="Références souches", blank=True)
    reference_clusters = models.CharField(max_length=255, verbose_name="Références clusters", blank=True)
    evaluation = models.TextField(blank=True, verbose_name="Évaluation")

    @classmethod
    def danger_plus_courants(self):
        return [
            CategorieDanger.LISTERIA_MONOCYTOGENES,
            CategorieDanger.SALMONELLA_ENTERITIDIS,
            CategorieDanger.SALMONELLA_TYPHIMURIUM,
            CategorieDanger.E_COLI_NON_STEC,
            CategorieDanger.PESTICIDE_RESIDU,
        ]

    @property
    def list_of_linked_objects_as_str(self):
        links = LienLibre.objects.for_object(self)
        objects = [link.related_object_1 if link.related_object_2 == self else link.related_object_2 for link in links]
        return [str(o) for o in objects if not o.is_deleted]

    def can_user_access(self, user):
        if user.agent.is_in_structure(self.createur):
            return True
        return not self.is_draft

    def can_be_updated(self, user):
        return self._user_can_interact(user)

    def can_user_delete(self, user):
        return self.can_user_access(user)

    def _user_can_interact(self, user):
        return not self.is_cloture and self.can_user_access(user)

    def get_email_subject(self):
        return f"{self.get_type_evenement_display()} {self.numero}"

    def get_message_form(self):
        from ssa.forms import MessageForm

        return MessageForm

    def get_allowed_document_types(self):
        return [
            Document.TypeDocument.SIGNALEMENT_CERFA,
            Document.TypeDocument.SIGNALEMENT_RASFF,
            Document.TypeDocument.SIGNALEMENT_AUTRE,
            Document.TypeDocument.RAPPORT_ANALYSE,
            Document.TypeDocument.ANALYSE_RISQUE,
            Document.TypeDocument.TRACABILITE_INTERNE,
            Document.TypeDocument.TRACABILITE_AVAL_RECIPIENT,
            Document.TypeDocument.TRACABILITE_AVAL_AUTRE,
            Document.TypeDocument.TRACABILITE_AMONT,
            Document.TypeDocument.DSCE_CHED,
            Document.TypeDocument.ETIQUETAGE,
            Document.TypeDocument.SUITES_ADMINISTRATIVES,
            Document.TypeDocument.COMMUNIQUE_PRESSE,
            Document.TypeDocument.CERTIFICAT_SANITAIRE,
            Document.TypeDocument.COURRIERS_COURRIELS,
            Document.TypeDocument.COMPTE_RENDU,
            Document.TypeDocument.PHOTO,
            Document.TypeDocument.AFFICHETTE_RAPPEL,
            Document.TypeDocument.AUTRE,
        ]

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(produit_pret_a_manger="")
                    | models.Q(categorie_danger__in=CategorieDanger.dangers_bacteriens())
                ),
                name="pam_requires_danger_bacterien",
            ),
        ]
