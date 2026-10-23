import datetime
from functools import cached_property
import io

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.forms import Media
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.http import urlencode
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from django.views.generic.edit import ModelFormMixin, ProcessFormView
from docxtpl import DocxTemplate

from core.mixins import (
    MediaDefiningMixin,
    WithAddUserContactsMixin,
    WithBlocCommunMixin,
    WithClotureContextMixin,
    WithDocumentExportContextMixin,
    WithFinDeSuiviMixin,
    WithFormErrorsAsMessagesMixin,
    WithFormsetInvalidMixin,
    WithFreeLinksListInContextMixin,
)
from sa.forms.evenement import EvenementAnimalForm
from sa.formsets import AnalyseFormSet, EspeceConcerneeFormSet, VeterinaireFormSet
from sa.models import Espece, EvenementAnimal, Maladie
from sa.models.evenement import StatutAnimal, TypeDetenteur

from .mixins import WithFilteredListMixin


class EvenementListView(WithFilteredListMixin, MediaDefiningMixin, ListView):
    model = EvenementAnimal
    paginate_by = 100

    def get_media(self, **context_data) -> Media:
        return context_data["filter"].form.media if "filter" in context_data else Media()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        context["total_object_count"] = self.get_raw_queryset().count()

        for evenement in context["evenementanimal_list"]:
            etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)
            evenement.etat = etat_data["etat"]
            evenement.readable_etat = etat_data["readable_etat"]

        return context


class EvenementAnimalBaseView(
    WithFormErrorsAsMessagesMixin,
    MediaDefiningMixin,
    WithFormsetInvalidMixin,
    WithAddUserContactsMixin,
    ModelFormMixin,
    ProcessFormView,
):
    template_name = "sa/evenement_animal_form.html"
    form_class = EvenementAnimalForm
    model = EvenementAnimal

    @cached_property
    def analyse_formset(self):
        return AnalyseFormSet(**self.get_analyse_formset_kwargs())

    def get_analyse_formset_kwargs(self):
        kwargs = {"form_kwargs": {"maladie_initial": self.request.GET.get("maladie")}}
        if self.object:
            kwargs["instance"] = self.object
        if self.request.POST:
            kwargs["data"] = self.request.POST
        return kwargs

    @cached_property
    def veterinaire_formset(self):
        return VeterinaireFormSet(**self.get_veterinaire_formset_kwargs())

    def get_veterinaire_formset_kwargs(self):
        kwargs = {"form_kwargs": {"espece_id": self.request.GET.get("espece")}}
        if self.object:
            kwargs["instance"] = self.object
        if self.request.POST:
            kwargs["data"] = self.request.POST
        return kwargs

    def get_especes_concernees_formset_kwargs(self):
        kwargs = {"prefix": "especes_concernees"}
        if self.object:
            kwargs["instance"] = self.object
        else:
            kwargs["initial"] = [{"espece": self.request.GET.get("espece")}]
        if self.request.method == "POST":
            kwargs["data"] = self.request.POST
        return kwargs

    @cached_property
    def especes_concernees_formset(self):
        return EspeceConcerneeFormSet(**self.get_especes_concernees_formset_kwargs())

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object
        if not self.kwargs.get(self.pk_url_kwarg):
            return None

        if queryset is None:
            queryset = self.get_queryset()
        try:
            self.object = queryset.select_related("maladie", "espece").get(pk=self.kwargs[self.pk_url_kwarg])
            return self.object
        except (ValueError, EvenementAnimal.DoesNotExist):
            raise Http404("Évènement animal non trouvé")

    def get_media(self, **context_data) -> Media:
        return (
            context_data["form"].media
            + self.analyse_formset.media
            + self.veterinaire_formset.media
            + self.especes_concernees_formset.media
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["analyse_formset"] = self.analyse_formset
        context["veterinaire_formset"] = self.veterinaire_formset
        context["especes_concernees_formset"] = self.especes_concernees_formset
        return context

    def post(self, request, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        if not self.analyse_formset.is_valid():
            return self.formset_invalid(
                self.analyse_formset,
                "Erreurs dans le(s) formulaire(s) Analyse",
                "Erreur dans le formulaire analyse",
            )

        if not self.veterinaire_formset.is_valid():
            return self.formset_invalid(
                self.veterinaire_formset,
                "Erreurs dans le(s) formulaire(s) Vétérinaire",
                "Erreur dans le formulaire vétérinaire",
            )

        if not self.especes_concernees_formset.is_valid():
            return self.formset_invalid(
                self.especes_concernees_formset,
                "Erreurs dans le(s) formulaire(s) espèces concernées et exposées",
                "Erreur dans le formulaire espèces concernées et exposées",
            )

        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)
        return self.form_valid(form)

    def form_valid(self, form):
        self.object = form.save()
        self.analyse_formset.instance = self.object
        self.analyse_formset.save()
        self.veterinaire_formset.instance = self.object
        self.veterinaire_formset.save()
        self.especes_concernees_formset.instance = self.object
        self.especes_concernees_formset.save()
        self.add_user_contacts(self.object)
        messages.success(self.request, self.get_success_message())
        return HttpResponseRedirect(self.object.get_absolute_url())


class EvenementAnimalCreationView(EvenementAnimalBaseView, CreateView):
    @cached_property
    def evenement_source(self):
        pk = self.request.GET.get("evenement_source")
        if not pk:
            return None
        try:
            evenement = EvenementAnimal.objects.get(pk=pk)
        except (ValueError, EvenementAnimal.DoesNotExist):
            raise Http404("Fiche non trouvée")
        if not evenement.can_user_access(self.request.user):
            raise Http404("Fiche non trouvée")
        return evenement

    @property
    def should_copy_evenement_source(self):
        return self.evenement_source is not None and self.request.method == "GET"

    def get_initial(self):
        initial = super().get_initial()
        if self.should_copy_evenement_source:
            source = self.evenement_source
            fields = [f for f in EvenementAnimalForm.Meta.fields if f not in ("maladie", "espece", "statut_animal")]
            initial.update({field: getattr(source, field) for field in fields})
            initial["type_detenteur"] = (
                TypeDetenteur.PARTICULIER if source.nom_particulier else TypeDetenteur.ETABLISSEMENT
            )
        return initial

    def get_analyse_formset_kwargs(self):
        kwargs = super().get_analyse_formset_kwargs()
        if self.should_copy_evenement_source:
            analyses = self.evenement_source.analyses.exclude(maladie=self.evenement_source.maladie)
            kwargs["initial"] = [model_to_dict(analyse, exclude=["id", "evenement"]) for analyse in analyses]
        return kwargs

    def get_veterinaire_formset_kwargs(self):
        kwargs = super().get_veterinaire_formset_kwargs()
        if self.should_copy_evenement_source:
            kwargs["initial"] = [
                {**model_to_dict(veterinaire, exclude=["id", "evenement"]), "departement": veterinaire.departement}
                for veterinaire in self.evenement_source.veterinaires.all()
            ]
        return kwargs

    def get_especes_concernees_formset_kwargs(self):
        kwargs = super().get_especes_concernees_formset_kwargs()
        if self.should_copy_evenement_source:
            # The first row is the one of the main espece, as its espece cannot be changed
            especes_concernees = sorted(
                self.evenement_source.especes_exposees.all(),
                key=lambda espece_concernee: espece_concernee.espece_id != self.evenement_source.espece_id,
            )
            kwargs["initial"] = [
                {
                    **model_to_dict(espece_concernee, exclude=["id", "evenement", "situation_unite_regle"]),
                    "type_lieu": espece_concernee.type_lieu,
                    "mode_elevage": espece_concernee.mode_elevage,
                    "type_production": espece_concernee.type_production,
                    "type_elevage": espece_concernee.type_elevage,
                }
                for espece_concernee in especes_concernees
            ] or kwargs["initial"]
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["maladie"] = self.request.GET.get("maladie")
        kwargs["espece"] = self.request.GET.get("espece")
        kwargs["statut_animal"] = self.request.GET.get("statut_animal")
        kwargs["structure"] = self.request.user.agent.structure
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["maladie"] = Maladie.objects.get(pk=self.request.GET.get("maladie"))
        context["espece"] = Espece.objects.get(pk=self.request.GET.get("espece"))
        context["statut_animal"] = StatutAnimal(self.request.GET.get("statut_animal"))
        if self.evenement_source:
            content_type = ContentType.objects.get_for_model(self.evenement_source)
            context["evenement_source_free_link"] = {
                "value": f"{content_type.pk}-{self.evenement_source.pk}",
                "label": str(self.evenement_source),
            }
        return context

    def form_valid(self, form):
        form.instance.evenement_source = self.evenement_source
        return super().form_valid(form)

    def get_success_message(self):
        return (
            "L’évènement a été publié avec succès."
            if self.object.is_published
            else "L’évènement a été créé avec succès."
        )


class EvenementAnimalUpdateView(UserPassesTestMixin, EvenementAnimalBaseView, UpdateView):
    def test_func(self):
        return self.get_object().can_be_modified(self.request.user)

    def get_object(self, queryset=None):
        if not hasattr(self, "object") or self.object is None:
            self.object = super().get_object(queryset)
        return self.object

    def get_initial(self):
        initial = super().get_initial()
        # Displays the correct type of detenteur when editing the evenement
        initial["type_detenteur"] = (
            TypeDetenteur.PARTICULIER if self.object.nom_particulier else TypeDetenteur.ETABLISSEMENT
        )
        return initial

    def get_analyse_formset_kwargs(self):
        kwargs = super().get_analyse_formset_kwargs()
        kwargs["form_kwargs"]["maladie_initial"] = self.object.maladie_id
        return kwargs

    def get_veterinaire_formset_kwargs(self):
        kwargs = super().get_veterinaire_formset_kwargs()
        kwargs["form_kwargs"]["espece_id"] = self.object.espece_id
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["maladie"] = self.object.maladie_id
        kwargs["espece"] = self.object.espece_id
        kwargs["statut_animal"] = self.object.statut_animal
        kwargs["structure"] = self.request.user.agent.structure
        kwargs["latest_version"] = self.object.latest_version.pk if self.object.latest_version else 0
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["maladie"] = self.object.maladie
        context["espece"] = self.object.espece
        context["statut_animal"] = StatutAnimal(self.object.statut_animal)
        return context

    def get_success_message(self):
        if self.request.POST.get("action") == "publish":
            return "L’évènement a été publié avec succès."
        return "L’évènement a bien été modifié."


class EvenementAnimalDetailsView(
    UserPassesTestMixin,
    WithBlocCommunMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    WithFinDeSuiviMixin,
    DetailView,
):
    model = EvenementAnimal
    template_name = "sa/evenement_animal_details.html"

    def test_func(self):
        return self.get_object().can_user_access(self.request.user)

    def get_queryset(self):
        return EvenementAnimal.objects.all()

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()
        try:
            self.object = queryset.get(pk=self.kwargs["pk"])
            return self.object
        except (ValueError, EvenementAnimal.DoesNotExist):
            raise Http404("Fiche non trouvée")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.agent.structure.contact_set.get()
        context["etat"] = self.object.get_etat_data_for_contact(contact)
        context["can_publish"] = self.get_object().can_publish(self.request.user)
        context["content_type"] = ContentType.objects.get_for_model(self.object)
        context["latest_version"] = self.object.latest_version
        context["can_be_deleted"] = self.get_object().can_be_deleted(self.request.user)
        context["can_be_modified"] = self.object.can_be_modified(self.request.user)
        context["display_warning_modification"] = self.object.display_warning_modification(self.request.user)
        context["detected_maladie_alerts"] = self.get_detected_maladie_alerts()
        return context

    def get_detected_maladie_alerts(self):
        creation_url = reverse("sa:evenement-animal-creation")
        return [
            {
                "maladie": maladie,
                "creation_url": f"{creation_url}?"
                + urlencode(
                    {
                        "maladie": maladie.pk,
                        "espece": self.object.espece_id,
                        "statut_animal": self.object.statut_animal,
                        "evenement_source": self.object.pk,
                    }
                ),
            }
            for maladie in self.object.detected_maladies_without_evenement_enfant
        ]


class EvenementAnimalDocumentExportView(WithDocumentExportContextMixin, UserPassesTestMixin, View):
    http_method_names = ["post"]

    def dispatch(self, request, pk=None, *args, **kwargs):
        self.object = get_object_or_404(EvenementAnimal, pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        doc = DocxTemplate("sa/doc_templates/evenement_animal.docx")
        sub_doc = doc.new_subdoc(self.create_document_bloc_commun())
        context = {
            "object": self.object,
            "free_links": self.get_free_links_numbers(),
            "bloc_commun": sub_doc,
            "now": datetime.datetime.now(),
        }
        doc.render(context)

        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)

        response = HttpResponse(
            file_stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f"attachment; filename=evenement_animal_{self.object.numero}.docx"
        return response

    def test_func(self):
        return self.object.can_user_access(self.request.user)
