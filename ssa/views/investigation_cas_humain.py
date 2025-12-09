from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.views.generic import DetailView

from core.mixins import (
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    WithBlocCommunPermission,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessageMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    WithFinDeSuiviMixin,
)
from ..models import EvenementInvestigationCasHumain


class InvestigationCasHumainDetailView(
    UserPassesTestMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    WithBlocCommunPermission,
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessageMixin,
    WithContactFormsInContextMixin,
    WithContactListInContextMixin,
    WithFinDeSuiviMixin,
    DetailView,
):
    model = EvenementInvestigationCasHumain
    template_name = "ssa/investigation_cas_humain_detail.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return (
            EvenementInvestigationCasHumain.objects.all()
            .select_related("createur")
            .prefetch_related("etablissements__departement")
            .prefetch_related("etablissements__departement__region")
        )

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            self.object = queryset.get(pk=self.kwargs["pk"])
            return self.object
        except (ValueError, EvenementInvestigationCasHumain.DoesNotExist):
            raise Http404("Fiche produit non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.agent.structure.contact_set.get()
        context["etat"] = self.get_object().get_etat_data_for_contact(contact)
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["can_be_modified"] = self.get_object().can_be_modified(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        return context
