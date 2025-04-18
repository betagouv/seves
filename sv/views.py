from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from reversion.models import Version

from core.forms import MessageForm, MessageDocumentForm, StructureAddForm, AgentAddForm
from core.mixins import (
    WithDocumentUploadFormMixin,
    WithDocumentListInContextMixin,
    WithMessagesListInContextMixin,
    WithContactListInContextMixin,
    CanUpdateVisibiliteRequiredMixin,
    WithFreeLinksListInContextMixin,
    WithSireneTokenMixin,
    WithFormErrorsAsMessagesMixin,
)
from core.models import Visibilite
from core.redirect import safe_redirect
from core.validators import AUTHORIZED_EXTENSIONS, MAX_UPLOAD_SIZE_MEGABYTES
from sv.forms import (
    FicheZoneDelimiteeForm,
    ZoneInfesteeFormSet,
    ZoneInfesteeFormSetUpdate,
    FicheDetectionForm,
    LieuFormSet,
    PrelevementForm,
    EvenementForm,
    EvenementVisibiliteUpdateForm,
    EvenementUpdateForm,
    StructureSelectionForVisibiliteForm,
)
from .export import FicheDetectionExport
from .filters import EvenementFilter
from .models import (
    FicheDetection,
    Lieu,
    Prelevement,
    FicheZoneDelimitee,
    StructurePreleveuse,
    Laboratoire,
    Evenement,
)
from .view_mixins import (
    WithPrelevementHandlingMixin,
    WithStatusToOrganismeNuisibleMixin,
    WithAddUserContactsMixin,
    WithPrelevementResultatsMixin,
    WithClotureContextMixin,
)


class EvenementListView(ListView):
    model = Evenement
    paginate_by = 100

    def get_queryset(self):
        contact = self.request.user.agent.structure.contact_set.get()
        queryset = (
            Evenement.objects.all()
            .get_user_can_view(self.request.user)
            .with_list_of_lieux_with_commune()
            .with_fin_de_suivi(contact)
            .with_nb_fiches_detection()
            .optimized_for_list()
            .order_by_numero()
        )
        self.filter = EvenementFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter

        for evenement in context["evenement_list"]:
            etat_data = evenement.get_etat_data_from_fin_de_suivi(evenement.has_fin_de_suivi)
            evenement.etat = etat_data["etat"]
            evenement.readable_etat = etat_data["readable_etat"]

            evenement.all_lieux_with_commune = []
            for detection in evenement.detections.all():
                if hasattr(detection, "lieux_list_with_commune"):
                    evenement.all_lieux_with_commune.extend(detection.lieux_list_with_commune)

        return context


class EvenementDetailView(
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessagesListInContextMixin,
    WithContactListInContextMixin,
    WithFreeLinksListInContextMixin,
    WithClotureContextMixin,
    UserPassesTestMixin,
    DetailView,
):
    model = Evenement

    def get_queryset(self):
        return (
            Evenement.objects.all()
            .select_related("createur", "organisme_nuisible", "statut_reglementaire")
            .prefetch_related(
                Prefetch(
                    "detections",
                    queryset=FicheDetection.objects.all()
                    .with_numero_detection_only()
                    .order_by("numero_detection_only"),
                ),
                "detections__createur",
                "detections__contexte",
                Prefetch(
                    "detections__lieux__prelevements",
                    queryset=Prelevement.objects.select_related(
                        "structure_preleveuse", "matrice_prelevee", "espece_echantillon", "laboratoire"
                    ),
                ),
                "detections__lieux__departement",
                "detections__lieux__departement__region",
                "detections__lieux__position_chaine_distribution_etablissement",
                "detections__lieux__site_inspection",
            )
        )

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        if queryset is None:
            queryset = self.get_queryset()

        try:
            annee, numero_evenement = self.kwargs["numero"].split(".")
            self.object = queryset.get(numero_annee=annee, numero_evenement=numero_evenement)
            return self.object
        except (ValueError, Evenement.DoesNotExist):
            raise Http404("Événement non trouvé")

    def test_func(self) -> bool | None:
        """Vérifie si l'utilisateur peut accéder à la vue (cf. UserPassesTestMixin)."""
        return self.get_object().can_user_access(self.request.user)

    def handle_no_permission(self):
        raise PermissionDenied()

    def get_permission_context(self):
        user = self.request.user
        return {
            "can_publish": self.get_object().can_publish(user),
            "can_update_visibilite": self.get_object().can_update_visibilite(user),
            "can_be_ac_notified": self.get_object().can_notifiy(user),
            "can_be_updated": self.get_object().can_be_updated(user),
            "can_be_deleted": self.get_object().can_be_deleted(user),
            "can_add_fiche_detection": self.get_object().can_add_fiche_detection(user),
            "can_delete_fiche_detection": self.get_object().can_delete_fiche_detection(),
            "can_update_fiche_detection": self.get_object().can_update_fiche_detection(user),
            "can_delete_fiche_zone_delimitee": self.get_object().can_delete_fiche_zone_delimitee(user),
            "can_update_fiche_zone_delimitee": self.get_object().can_update_fiche_zone_delimitee(user),
            "can_add_fiche_zone_delimitee": self.get_object().can_add_fiche_zone_delimitee(user),
            "can_add_agent": self.get_object().can_add_agent(user),
            "can_add_structure": self.get_object().can_add_structure(user),
            "can_delete_contact": self.get_object().can_delete_contact(user),
            "can_add_document": self.get_object().can_add_document(user),
            "can_update_document": self.get_object().can_update_document(user),
            "can_delete_document": self.get_object().can_delete_document(user),
            "can_download_document": self.get_object().can_download_document(user),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_permission_context())
        content_type = ContentType.objects.get_for_model(self.get_object())
        context["content_type"] = content_type
        context["fiche_detection_content_type"] = ContentType.objects.get_for_model(FicheDetection)
        context["fiche_zone_content_type"] = ContentType.objects.get_for_model(FicheZoneDelimitee)
        context["visibilite_form"] = EvenementVisibiliteUpdateForm(obj=self.get_object())
        context["latest_version"] = self.object.latest_version
        fiche_zone = self.get_object().fiche_zone_delimitee
        if fiche_zone:
            context["detections_hors_zone_infestee"] = fiche_zone.fichedetection_set.all()
            context["zones_infestees"] = [
                (zone_infestee, zone_infestee.fichedetection_set.all())
                for zone_infestee in fiche_zone.zoneinfestee_set.all()
            ]
        context["message_form"] = MessageForm(
            sender=self.request.user,
            obj=self.get_object(),
            next=self.get_object().get_absolute_url(),
        )
        context["add_document_form"] = MessageDocumentForm()
        context["allowed_extensions"] = AUTHORIZED_EXTENSIONS
        contact = self.request.user.agent.structure.contact_set.get()
        context["etat"] = self.get_object().get_etat_data_for_contact(contact)
        context["active_detection"] = (
            int(self.request.GET.get("detection"))
            if self.request.GET.get("detection")
            else getattr(self.object.detections.first(), "id", None)
        )
        context["max_upload_size_mb"] = MAX_UPLOAD_SIZE_MEGABYTES
        initial_data = {"content_id": self.get_object().id, "content_type_id": content_type.id}
        context["add_contact_structure_form"] = StructureAddForm(initial=initial_data, obj=self.get_object())
        context["add_contact_agent_form"] = AgentAddForm(initial=initial_data, obj=self.get_object())
        return context


class EvenementUpdateView(
    WithStatusToOrganismeNuisibleMixin,
    UserPassesTestMixin,
    WithAddUserContactsMixin,
    WithFormErrorsAsMessagesMixin,
    UpdateView,
):
    form_class = EvenementUpdateForm

    def get_queryset(self):
        return Evenement.objects.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["latest_version"] = Version.objects.get_for_object(self.get_object()).first().pk
        return kwargs

    def test_func(self) -> bool | None:
        return self.get_object().can_be_updated(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.add_user_contacts(self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.request.user.agent.structure.contact_set.get()
        context["etat"] = self.get_object().get_etat_data_for_contact(contact)
        return context


class FicheDetectionCreateView(
    WithStatusToOrganismeNuisibleMixin,
    WithSireneTokenMixin,
    WithPrelevementHandlingMixin,
    WithPrelevementResultatsMixin,
    UserPassesTestMixin,
    CreateView,
):
    form_class = FicheDetectionForm
    template_name = "sv/fichedetection_form.html"

    def dispatch(self, request, *args, **kwargs):
        evenement_pk = request.GET.get("evenement") if request.method == "GET" else request.POST.get("evenement")

        self.evenement = None
        if evenement_pk:
            self.evenement = Evenement.objects.get(pk=evenement_pk)

        return super().dispatch(request, *args, **kwargs)

    def test_func(self):
        return True if not self.evenement else self.evenement.can_add_fiche_detection(self.request.user)

    def get_success_url(self):
        return f"{self.object.evenement.get_absolute_url()}?detection={self.object.pk}"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["latest_version"] = 0
        if self.request.GET.get("evenement"):
            kwargs["data"] = {"evenement": self.evenement}
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_creation"] = True
        formset = LieuFormSet()
        formset.custom_kwargs = {"convert_required_to_data_required": True}
        context["lieu_formset"] = formset
        forms = [
            PrelevementForm(
                convert_required_to_data_required=True,
                prefix=f"prelevements-{i}",
            )
            for i in range(0, 10)
        ]
        context["prelevement_forms"] = forms
        context["evenement"] = self.evenement
        return context

    def _get_or_create_evenement(self, request, evenement_form):
        if self.evenement:
            return self.evenement
        return evenement_form.save()

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        lieu_formset = LieuFormSet(request.POST)

        if self.evenement:
            evenement_data = {
                "organisme_nuisible": self.evenement.organisme_nuisible.pk,
                "statut_reglementaire": self.evenement.statut_reglementaire.pk,
            }
            evenement_form = EvenementForm(evenement_data, user=self.request.user)
        else:
            evenement_form = EvenementForm(request.POST, user=self.request.user)

        if not form.is_valid():
            return self.form_invalid(form)

        if not lieu_formset.is_valid():
            return self.form_invalid(form)

        if not evenement_form.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            evenement = self._get_or_create_evenement(request, evenement_form)

            self.object = form.save(commit=False)
            self.object.evenement = evenement
            self.object.save()

            lieu_formset.instance = self.object
            allowed_lieux = lieu_formset.save()
            allowed_lieux = Lieu.objects.filter(pk__in=[lieu.id for lieu in allowed_lieux])
            try:
                self._save_prelevement_if_not_empty(request.POST.copy(), allowed_lieux)
            except ValidationError as e:
                for message in e.messages:
                    messages.error(self.request, message)
                return self.form_invalid(form)

            evenement.contacts.add(self.request.user.agent.contact_set.get())
            evenement.contacts.add(self.request.user.agent.structure.contact_set.get())

        return HttpResponseRedirect(self.get_success_url())


class FicheDetectionUpdateView(
    WithStatusToOrganismeNuisibleMixin,
    WithPrelevementHandlingMixin,
    WithAddUserContactsMixin,
    WithPrelevementResultatsMixin,
    UserPassesTestMixin,
    WithSireneTokenMixin,
    WithFormErrorsAsMessagesMixin,
    UpdateView,
):
    model = FicheDetection
    form_class = FicheDetectionForm
    context_object_name = "fichedetection"

    def get_success_url(self):
        return f"{self.object.evenement.get_absolute_url()}?detection={self.object.pk}"

    def test_func(self):
        return self.get_object().evenement.can_update_fiche_detection(self.request.user)

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        self.object = super().get_object(queryset)
        return self.object

    def _handle_inactive_values(self, model, field_name, pk):
        actual_ids = Prelevement.objects.filter(lieu__fiche_detection__pk=pk)
        actual_ids = actual_ids.values_list(field_name + "_id", flat=True)
        inactive_ids = model._base_manager.filter(is_active=False).values_list("id", flat=True)
        has_inactive_value = any([pk in inactive_ids for pk in actual_ids])
        queryset = model._base_manager if has_inactive_value else model.objects
        return queryset.order_by("nom")

    def _get_existing_prelevement_forms(self, existing_prelevements):
        lieux = self.object.lieux.all()
        existing_prelevements_forms = []
        for existing_prelevement in existing_prelevements:
            labos = self._handle_inactive_values(Laboratoire, "laboratoire", self.object.pk)
            structure = self._handle_inactive_values(StructurePreleveuse, "structure_preleveuse", self.object.pk)
            form = PrelevementForm(
                instance=existing_prelevement,
                convert_required_to_data_required=True,
                prefix=f"prelevements-{existing_prelevement.pk}",
                labo_values=labos,
                structure_values=structure,
            )
            form.fields["lieu"].queryset = lieux
            existing_prelevements_forms.append(form)
        return existing_prelevements_forms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_creation"] = False
        existing_prelevements = Prelevement.objects.filter(lieu__fiche_detection=self.object)
        context["existing_prelevements"] = self._get_existing_prelevement_forms(existing_prelevements)

        existing_prelevements_ids = [p.id for p in existing_prelevements]
        possible_ids = list(range(100))
        possible_ids = [i for i in possible_ids if i not in existing_prelevements_ids][:20]
        forms = [
            PrelevementForm(convert_required_to_data_required=True, prefix=f"prelevements-{i}") for i in possible_ids
        ]
        context["prelevement_forms"] = forms
        formset = LieuFormSet(
            instance=self.get_object(), queryset=Lieu.objects.filter(fiche_detection=self.get_object())
        )
        formset.custom_kwargs = {"convert_required_to_data_required": True}
        context["lieu_formset"] = formset
        context["evenement"] = self.get_object().evenement
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["latest_version"] = Version.objects.get_for_object(self.get_object()).first().pk
        return kwargs

    def post(self, request, pk):
        self.object = self.get_object()
        form = self.get_form()
        lieu_formset = LieuFormSet(
            request.POST,
            instance=self.get_object(),
            queryset=Lieu.objects.filter(fiche_detection=self.get_object()),
        )

        if not form.is_valid():
            return self.form_invalid(form)

        if not lieu_formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            lieu_formset.save()
            allowed_lieux = self.object.lieux.all()
            try:
                self._save_prelevement_if_not_empty(
                    request.POST.copy(), allowed_lieux, check_for_inactive_values=True, detection=self.object
                )
            except ValidationError as e:
                for message in e.messages:
                    messages.error(self.request, message)
                return self.form_invalid(form)
            self.add_user_contacts(self.object.evenement)
        messages.success(self.request, "La fiche détection a été modifiée avec succès.")
        return HttpResponseRedirect(self.get_success_url())


class FicheDetectionExportView(View):
    http_method_names = ["post"]

    def post(self, request):
        response = HttpResponse(content_type="text/csv")
        FicheDetectionExport().export(stream=response, user=request.user)
        response["Content-Disposition"] = "attachment; filename=export_fiche_detection.csv"
        return response


class EvenementCloturerView(View):
    def post(self, request, pk):
        data = self.request.POST
        content_type = ContentType.objects.get(pk=data["content_type_id"])
        evenement = content_type.model_class().objects.get(pk=pk)
        redirect_url = evenement.get_absolute_url()

        can_cloturer, error_message = evenement.can_be_cloturer(request.user)
        if not can_cloturer:
            messages.error(request, error_message)
            return redirect(redirect_url)

        if evenement.is_the_only_remaining_structure(
            self.request.user, evenement.get_contacts_structures_not_in_fin_suivi()
        ):
            evenement.add_fin_suivi(self.request.user)

        evenement.cloturer()
        messages.success(request, f"L'événement n°{evenement.numero} a bien été clôturé.")
        return redirect(redirect_url)


class EvenementVisibiliteUpdateView(CanUpdateVisibiliteRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Evenement
    form_class = EvenementVisibiliteUpdateForm
    http_method_names = ["post"]
    success_message = "La visibilité de l'évenement a bien été modifiée."

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        if form.cleaned_data["visibilite"] == Visibilite.LIMITEE:
            return redirect(reverse("sv:structure-add-visibilite", kwargs={"pk": self.object.pk}))
        else:
            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.allowed_structures.set([])
                self.object.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "La visibilité de l'événement n'a pas pu être modifiée.")
        return super().form_invalid(form)


class FicheZoneDelimiteeCreateView(WithFormErrorsAsMessagesMixin, UserPassesTestMixin, CreateView):
    model = FicheZoneDelimitee
    form_class = FicheZoneDelimiteeForm
    context_object_name = "fiche"

    def test_func(self):
        return self.evenement.can_add_fiche_zone_delimitee(self.request.user)

    def get_success_url(self):
        return reverse("sv:evenement-details", args=[self.object.evenement.numero]) + "?tab=zone"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.evenement = Evenement.objects.select_related("organisme_nuisible", "statut_reglementaire").get(
                pk=self.request.GET.get("evenement") or self.request.POST.get("evenement")
            )
        except Evenement.DoesNotExist:
            return HttpResponseBadRequest("L'événement n'existe pas.")

        if self.evenement.fiche_zone_delimitee:
            return HttpResponseBadRequest("L'événement est déjà rattaché à une fiche zone délimitée.")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["evenement"] = self.evenement
        form_kwargs = {"evenement": self.evenement}
        if self.request.POST:
            context["zone_infestee_formset"] = ZoneInfesteeFormSet(
                data=self.request.POST,
                form_kwargs=form_kwargs,
            )
        else:
            context["zone_infestee_formset"] = ZoneInfesteeFormSet(
                form_kwargs=form_kwargs,
                initial=[{"detections": getattr(self, "zone_infestee_detection", None)}],
            )
        context["empty_form"] = context["zone_infestee_formset"].empty_form
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["latest_version"] = 0
        kwargs["detections_zones_infestees_formset"] = getattr(self, "detections_zones_infestees_formset", set())
        return kwargs

    def get_initial(self):
        if self.request.GET:
            return {
                "detections_hors_zone": getattr(self, "hors_zone_infestee_detection", None),
                "evenement": self.evenement,
            }
        return super().get_initial()

    def post(self, request, *args, **kwargs):
        self.object = None

        context = self.get_context_data()
        self.formset = context["zone_infestee_formset"]

        if not self.formset.is_valid():
            return self.formset_invalid()

        self.set_detections_zones_infestees_formset()

        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)
        return self.form_valid(form)

    def set_detections_zones_infestees_formset(self):
        """Récupère les fiches détection sélectionnées dans les formulaires de la formset
        pour vérifier les doublons entre Detection hors zone infestée et Zone infestée.
        La vérification des doublons est effectuée dans le form FicheZoneDelimiteeForm."""
        self.detections_zones_infestees_formset = {
            detection for f in self.formset for detection in f.cleaned_data.get("detections", [])
        }

    def form_valid(self, form):
        try:
            evenement = Evenement.objects.get(pk=self.request.POST.get("evenement"))
        except Evenement.DoesNotExist:
            return HttpResponseBadRequest("L'événement n'existe pas.")

        self.object = form.save()

        evenement.fiche_zone_delimitee = self.object
        evenement.save()

        self.formset.instance = self.object
        self.formset.save()
        messages.success(self.request, "La fiche zone délimitée a été créée avec succès.")
        return HttpResponseRedirect(self.get_success_url())

    def formset_invalid(self):
        messages.error(
            self.request,
            "Erreurs dans le(s) formulaire(s) Zones infestées",
        )
        return self.render_to_response(self.get_context_data())


class FicheZoneDelimiteeUpdateView(
    WithAddUserContactsMixin, UserPassesTestMixin, WithFormErrorsAsMessagesMixin, UpdateView
):
    model = FicheZoneDelimitee
    form_class = FicheZoneDelimiteeForm
    context_object_name = "fiche"

    def get_success_url(self):
        return self.get_object().get_absolute_url() + "?tab=zone"

    def test_func(self) -> bool | None:
        return self.get_object().can_be_updated(self.request.user)

    def get_object(self, queryset=None):
        return super().get_object(
            FicheZoneDelimitee.objects.select_related(
                "evenement__organisme_nuisible", "evenement__statut_reglementaire"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["evenement"] = self.get_object().evenement
        form_kwargs = {"evenement": self.get_object().evenement}
        if self.request.POST:
            context["zone_infestee_formset"] = ZoneInfesteeFormSetUpdate(
                data=self.request.POST,
                instance=self.object,
                form_kwargs=form_kwargs,
            )
        else:
            context["zone_infestee_formset"] = ZoneInfesteeFormSetUpdate(
                instance=self.object,
                form_kwargs=form_kwargs,
            )
        context["empty_form"] = context["zone_infestee_formset"].empty_form
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["evenement"] = self.object.evenement
        initial["detections_hors_zone"] = list(
            FicheDetection.objects.filter(hors_zone_infestee=self.object, zone_infestee__isnull=True).values_list(
                "id", flat=True
            )
        )
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["latest_version"] = Version.objects.get_for_object(self.get_object()).first().pk

        # Lors d'un POST, on utilise detections_zones_infestees_formset déjà défini
        if hasattr(self, "detections_zones_infestees_formset"):
            kwargs["detections_zones_infestees_formset"] = self.detections_zones_infestees_formset
        # Sinon (GET), on récupère les détections existantes en base
        else:
            kwargs["detections_zones_infestees_formset"] = set(
                FicheDetection.objects.filter(zone_infestee__fiche_zone_delimitee=self.object)
            )

        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        context = self.get_context_data()
        formset = context["zone_infestee_formset"]

        if not formset.is_valid():
            return self.formset_invalid()

        # Récupére les détections sélectionnées dans les zones infestées
        self.detections_zones_infestees_formset = {
            detection
            for form in formset
            for detection in form.cleaned_data.get("detections", [])
            if not form.cleaned_data.get("DELETE", False)
        }

        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)

        return self.form_valid(form, formset)

    def form_valid(self, form, formset):
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            self.add_user_contacts(self.object.evenement)

        messages.success(self.request, "La fiche zone délimitée a été modifiée avec succès.")
        return HttpResponseRedirect(self.get_success_url())

    def formset_invalid(self):
        messages.error(
            self.request,
            "Erreurs dans le(s) formulaire(s) Zones infestées",
        )
        return self.render_to_response(self.get_context_data())


class VisibiliteStructureView(UserPassesTestMixin, UpdateView):
    template_name = "sv/structure_add_to_visibilite_form.html"
    model = Evenement
    form_class = StructureSelectionForVisibiliteForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["evenement"] = self.object
        return context

    def form_valid(self, form):
        evenement = form.save()
        evenement.visibilite = Visibilite.LIMITEE
        evenement.save()
        messages.success(self.request, "Les droits d'accès ont été modifiés")
        return safe_redirect(self.object.get_absolute_url())

    def test_func(self):
        return self.get_object().can_update_visibilite(self.request.user)


class FicheZoneDelimiteeDeleteView(UserPassesTestMixin, DeleteView):
    model = FicheZoneDelimitee

    def test_func(self):
        return self.get_object().can_be_deleted(self.request.user)

    def handle_no_permission(self):
        raise PermissionDenied()

    def get_success_url(self):
        messages.success(self.request, "La zone a bien été supprimée")
        return self.request.POST.get("next")
