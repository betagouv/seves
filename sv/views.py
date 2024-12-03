from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    FormView,
)

from core.mixins import (
    WithDocumentUploadFormMixin,
    WithDocumentListInContextMixin,
    WithMessagesListInContextMixin,
    WithContactListInContextMixin,
    WithFreeLinksListInContextMixin,
)
from core.models import Visibilite
from core.redirect import safe_redirect
from sv.forms import (
    FicheDetectionVisibiliteUpdateForm,
    FicheZoneDelimiteeForm,
    ZoneInfesteeFormSet,
    ZoneInfesteeFormSetUpdate,
    RattachementDetectionForm,
    RattachementChoices,
    FicheZoneDelimiteeVisibiliteUpdateForm,
    FicheDetectionForm,
    LieuFormSet,
    PrelevementForm,
)
from .display import DisplayedFiche
from .export import FicheDetectionExport
from .filters import FicheFilter
from .models import (
    FicheDetection,
    Lieu,
    Prelevement,
    FicheZoneDelimitee,
    ZoneInfestee,
)
from .view_mixins import FicheDetectionContextMixin, WithPrelevementHandlingMixin


class FicheListView(ListView):
    model = FicheDetection
    paginate_by = 100
    context_object_name = "fiches"
    template_name = "sv/fiche_list.html"

    def dispatch(self, request, *args, **kwargs):
        self.list_of_zones = self.request.GET.get("type_fiche") == "zone"
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.list_of_zones:
            queryset = FicheZoneDelimitee.objects.all().optimized_for_list().order_by_numero_fiche()
        else:
            queryset = FicheDetection.objects.all().get_fiches_user_can_view(self.request.user)
            queryset = (
                queryset.with_list_of_lieux().with_first_region_name().optimized_for_list().order_by_numero_fiche()
            )
        self.filter = FicheFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
        method = DisplayedFiche.from_fiche_zone if self.list_of_zones else DisplayedFiche.from_fiche_detection
        context["fiches"] = [method(fiche) for fiche in context["page_obj"]]
        return context


class FicheDetectionDetailView(
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessagesListInContextMixin,
    WithContactListInContextMixin,
    WithFreeLinksListInContextMixin,
    UserPassesTestMixin,
    DetailView,
):
    model = FicheDetection
    queryset = FicheDetection.objects.all().optimized_for_details().with_fiche_zone_delimitee_numero()

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        self.object = super().get_object(queryset)
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lieux"] = (
            Lieu.objects.filter(fiche_detection=self.get_object())
            .order_by("id")
            .select_related("departement__region", "site_inspection")
        )
        prelevement = Prelevement.objects.filter(lieu__fiche_detection=self.get_object())
        context["prelevements"] = prelevement.select_related(
            "structure_preleveur",
            "lieu",
            "matrice_prelevee",
            "espece_echantillon",
            "laboratoire_agree",
        )
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        contacts_not_in_fin_suivi = FicheDetection.objects.all().get_contacts_structures_not_in_fin_suivi(
            self.get_object()
        )
        context["contacts_not_in_fin_suivi"] = contacts_not_in_fin_suivi
        context["can_cloturer_fiche"] = len(contacts_not_in_fin_suivi) == 0
        context["can_update_visibilite"] = self.get_object().can_update_visibilite(self.request.user)
        context["visibilite_form"] = FicheDetectionVisibiliteUpdateForm(obj=self.get_object())
        context["rattachement_detection_form"] = RattachementDetectionForm()
        context["fiche_zone_delimitee"] = self.get_object().get_fiche_zone_delimitee()
        return context

    def test_func(self) -> bool | None:
        """Vérifie si l'utilisateur peut accéder à la vue (cf. UserPassesTestMixin)."""
        return self.get_object().can_user_access(self.request.user)

    def handle_no_permission(self):
        """Affiche une erreur 403 Forbidden si l'utilisateur n'a pas la permission d'accéder à la vue. (cf. UserPassesTestMixin)."""
        raise PermissionDenied()


class FicheDetectionCreateView(FicheDetectionContextMixin, WithPrelevementHandlingMixin, CreateView):
    allows_inactive_laboratoires_agrees_values = False
    allows_inactive_laboratoires_confirmation_values = False
    allows_inactive_structure_preleveur_values = False
    form_class = FicheDetectionForm
    template_name = "sv/fichedetection_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_creation"] = True
        formset = LieuFormSet()
        formset.custom_kwargs = {"convert_required_to_data_required": True}
        context["lieu_formset"] = formset
        forms = [PrelevementForm(convert_required_to_data_required=True, prefix=f"prelevements-{i}") for i in range(10)]
        context["prelevement_forms"] = forms
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        lieu_formset = LieuFormSet(request.POST)

        if not form.is_valid():
            return self.form_invalid(form)

        if not lieu_formset.is_valid():
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            if request.POST["action"] == "Publier":
                self.object.visibilite = Visibilite.LOCAL
                self.object.save()
            lieu_formset.instance = self.object
            allowed_lieux = lieu_formset.save()
            allowed_lieux = Lieu.objects.filter(pk__in=[lieu.id for lieu in allowed_lieux])
            self._save_prelevement_if_not_empty(request.POST.copy(), allowed_lieux)
            self.object.contacts.add(self.request.user.agent.contact_set.get())
            self.object.contacts.add(self.request.user.agent.structure.contact_set.get())

        return HttpResponseRedirect(self.get_success_url())


class FicheDetectionUpdateView(FicheDetectionContextMixin, WithPrelevementHandlingMixin, UpdateView):
    model = FicheDetection
    form_class = FicheDetectionForm
    context_object_name = "fichedetection"

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        self.object = super().get_object(queryset)
        return self.object

    def _get_existing_prelevement_forms(self, existing_prelevements):
        lieux = self.object.lieux.all()
        existing_prelevements_forms = []
        for existing_prelevement in existing_prelevements:
            form = PrelevementForm(
                instance=existing_prelevement,
                convert_required_to_data_required=True,
                prefix=f"prelevements-{existing_prelevement.pk}",
            )
            form.fields["lieu"].queryset = lieux
            existing_prelevements_forms.append(form)
        return existing_prelevements_forms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_creation"] = False
        existing_prelevements = Prelevement.objects.filter(lieu__fiche_detection=self.object)

        existing_prelevements_ids = [p.id for p in existing_prelevements]
        possible_ids = list(range(100))
        possible_ids = [i for i in possible_ids if i not in existing_prelevements_ids][:20]
        forms = [
            PrelevementForm(convert_required_to_data_required=True, prefix=f"prelevements-{i}") for i in possible_ids
        ]
        context["prelevement_forms"] = forms

        # TODO handle espece echantillon

        context["existing_prelevements"] = self._get_existing_prelevement_forms(existing_prelevements)
        formset = LieuFormSet(
            instance=self.get_object(), queryset=Lieu.objects.filter(fiche_detection=self.get_object())
        )
        formset.custom_kwargs = {"convert_required_to_data_required": True}
        context["lieu_formset"] = formset
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
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

        with transaction.atomic():
            self.object = form.save()

            if not lieu_formset.is_valid():
                return self.form_invalid(form)

            lieu_formset.save()
            allowed_lieux = self.object.lieux.all()
            self._save_prelevement_if_not_empty(request.POST.copy(), allowed_lieux)
        messages.success(self.request, "La fiche détection a été modifiée avec succès.")
        return HttpResponseRedirect(self.get_success_url())


class FicheDetectionExportView(View):
    http_method_names = ["post"]

    def post(self, request):
        response = HttpResponse(content_type="text/csv")
        FicheDetectionExport().export(stream=response, user=request.user)
        response["Content-Disposition"] = "attachment; filename=export_fiche_detection.csv"
        return response


class FicheCloturerView(View):
    def post(self, request, pk):
        data = self.request.POST
        content_type = ContentType.objects.get(pk=data["content_type_id"]).model_class()
        fiche = content_type.objects.get(pk=pk)
        redirect_url = fiche.get_absolute_url()

        if not fiche.can_be_cloturer_by(request.user):
            messages.error(request, "Vous n'avez pas les droits pour clôturer cette fiche.")
            return redirect(redirect_url)

        if fiche.is_already_cloturer():
            messages.error(request, f"La fiche n° {fiche.numero} est déjà clôturée.")
            return redirect(redirect_url)

        contacts_not_in_fin_suivi = content_type.objects.all().get_contacts_structures_not_in_fin_suivi(fiche)
        if contacts_not_in_fin_suivi:
            messages.error(
                request,
                f"La fiche  n° {fiche.numero} ne peut pas être clôturée car les structures suivantes n'ont pas signalées la fin de suivi : {', '.join([str(contact) for contact in contacts_not_in_fin_suivi])}",
            )
            return redirect(redirect_url)

        fiche.cloturer()
        messages.success(request, f"La fiche n° {fiche.numero} a bien été clôturée.")
        return redirect(redirect_url)


class FicheDetectionVisibiliteUpdateView(SuccessMessageMixin, UpdateView):
    model = FicheDetection
    form_class = FicheDetectionVisibiliteUpdateForm
    http_method_names = ["post"]
    success_message = "La visibilité de la fiche détection a bien été modifiée."

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_invalid(self, form):
        messages.error(self.request, "La visibilité de la fiche détection n'a pas pu être modifiée.")
        return super().form_invalid(form)


class FicheZoneDelimiteeVisibiliteUpdateView(SuccessMessageMixin, UpdateView):
    model = FicheZoneDelimitee
    form_class = FicheZoneDelimiteeVisibiliteUpdateForm
    http_method_names = ["post"]
    success_message = "La visibilité de la fiche zone délimitée a bien été modifiée."

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_invalid(self, form):
        messages.error(self.request, "La visibilité de la fiche zone délimitée n'a pas pu être modifiée.")
        return super().form_invalid(form)


class RattachementDetectionView(FormView):
    form_class = RattachementDetectionForm

    def form_valid(self, form):
        fiche_detection_id = self.kwargs.get("pk")
        rattachement = form.cleaned_data["rattachement"]
        return safe_redirect(
            f"{reverse('fiche-zone-delimitee-creation')}?fiche_detection_id={fiche_detection_id}&rattachement={rattachement}"
        )


class FicheZoneDelimiteeCreateView(CreateView):
    model = FicheZoneDelimitee
    form_class = FicheZoneDelimiteeForm
    context_object_name = "fiche"

    def get_success_url(self):
        return reverse("fiche-zone-delimitee-detail", args=[self.object.pk])

    def get(self, request, *args, **kwargs):
        self.object = None

        try:
            fiche_detection = FicheDetection.objects.get(pk=self.request.GET.get("fiche_detection_id"))
        except FicheDetection.DoesNotExist:
            return HttpResponseBadRequest("La fiche de détection n'existe pas.")

        if fiche_detection.is_linked_to_fiche_zone_delimitee:
            return HttpResponseBadRequest("La fiche de détection est déjà rattachée à une fiche zone délimitée.")

        self.organisme_nuisible_libelle = fiche_detection.organisme_nuisible.libelle_court
        self.statut_reglementaire_libelle = fiche_detection.statut_reglementaire.libelle

        match self.request.GET.get("rattachement"):
            case RattachementChoices.HORS_ZONE_INFESTEE:
                self.hors_zone_infestee_detection = [fiche_detection]
            case RattachementChoices.ZONE_INFESTEE:
                self.zone_infestee_detection = fiche_detection

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["zone_infestee_formset"] = ZoneInfesteeFormSet(
                data=self.request.POST,
                form_kwargs={
                    "organisme_nuisible_libelle": self.request.POST.get("organisme_nuisible"),
                },
            )
        else:
            context["zone_infestee_formset"] = ZoneInfesteeFormSet(
                form_kwargs={
                    "organisme_nuisible_libelle": self.organisme_nuisible_libelle,
                },
                initial=[{"detections": getattr(self, "zone_infestee_detection", None)}],
            )
        context["empty_form"] = context["zone_infestee_formset"].empty_form
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["detections_zones_infestees_formset"] = getattr(self, "detections_zones_infestees_formset", set())
        return kwargs

    def get_initial(self):
        if self.request.GET:
            return {
                "organisme_nuisible": self.organisme_nuisible_libelle,
                "statut_reglementaire": self.statut_reglementaire_libelle,
                "detections_hors_zone": getattr(self, "hors_zone_infestee_detection", None),
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
        self.object = form.save()
        self.formset.instance = self.object
        self.formset.save()
        messages.success(self.request, "La fiche zone délimitée a été créée avec succès.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

    def formset_invalid(self):
        messages.error(
            self.request,
            "Erreurs dans le(s) formulaire(s) Zones infestées",
        )
        return self.render_to_response(self.get_context_data())


class FicheZoneDelimiteeDetailView(
    WithDocumentListInContextMixin,
    WithDocumentUploadFormMixin,
    WithMessagesListInContextMixin,
    WithContactListInContextMixin,
    WithFreeLinksListInContextMixin,
    UserPassesTestMixin,
    DetailView,
):
    model = FicheZoneDelimitee
    context_object_name = "fiche"

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        self.object = super().get_object(queryset)
        return self.object

    def get_queryset(self):
        zone_infestee_detections_prefetch = Prefetch(
            "fichedetection_set", queryset=FicheDetection.objects.select_related("numero")
        )
        zone_infestee_prefetch = Prefetch(
            "zoneinfestee_set",
            queryset=ZoneInfestee.objects.prefetch_related(zone_infestee_detections_prefetch),
        )
        return FicheZoneDelimitee.objects.select_related(
            "numero", "createur", "organisme_nuisible", "statut_reglementaire"
        ).prefetch_related(zone_infestee_prefetch)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fichezonedelimitee = self.get_object()
        context["can_update_visibilite"] = self.get_object().can_update_visibilite(self.request.user)
        context["visibilite_form"] = FicheDetectionVisibiliteUpdateForm(obj=self.get_object())
        context["detections_hors_zone_infestee"] = fichezonedelimitee.fichedetection_set.select_related("numero").all()
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        contacts_not_in_fin_suivi = FicheZoneDelimitee.objects.all().get_contacts_structures_not_in_fin_suivi(
            self.get_object()
        )
        context["contacts_not_in_fin_suivi"] = contacts_not_in_fin_suivi
        context["can_cloturer_fiche"] = len(contacts_not_in_fin_suivi) == 0
        context["zones_infestees"] = [
            (zone_infestee, zone_infestee.fichedetection_set.all())
            for zone_infestee in fichezonedelimitee.zoneinfestee_set.all()
        ]
        return context

    def test_func(self) -> bool | None:
        """Vérifie si l'utilisateur peut accéder à la vue (cf. UserPassesTestMixin)."""
        return self.get_object().can_user_access(self.request.user)


class FicheZoneDelimiteeUpdateView(UpdateView):
    model = FicheZoneDelimitee
    form_class = FicheZoneDelimiteeForm
    context_object_name = "fiche"

    def get_success_url(self):
        return self.get_object().get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["zone_infestee_formset"] = ZoneInfesteeFormSetUpdate(
                data=self.request.POST,
                instance=self.object,
                form_kwargs={
                    "fiche_zone_delimitee": self.object,
                    "organisme_nuisible_libelle": self.request.POST.get("organisme_nuisible"),
                },
            )
        else:
            context["zone_infestee_formset"] = ZoneInfesteeFormSetUpdate(
                instance=self.object,
                form_kwargs={
                    "fiche_zone_delimitee": self.object,
                    "organisme_nuisible_libelle": self.object.organisme_nuisible.libelle_court,
                },
            )
        context["empty_form"] = context["zone_infestee_formset"].empty_form
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["organisme_nuisible"] = self.object.organisme_nuisible
        initial["statut_reglementaire"] = self.object.statut_reglementaire
        initial["detections_hors_zone"] = list(
            FicheDetection.objects.filter(hors_zone_infestee=self.object, zone_infestee__isnull=True).values_list(
                "id", flat=True
            )
        )
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user

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

        messages.success(self.request, "La fiche zone délimitée a été modifiée avec succès.")
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

    def formset_invalid(self):
        messages.error(
            self.request,
            "Erreurs dans le(s) formulaire(s) Zones infestées",
        )
        return self.render_to_response(self.get_context_data())
