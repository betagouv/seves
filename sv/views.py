import json
from datetime import datetime
import uuid

from django.contrib.contenttypes.models import ContentType
from django.views import View
from django.shortcuts import redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    FormView,
)
from django.urls import reverse, reverse_lazy
from django.db.models import F
from django.db import transaction, IntegrityError
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin


from core.mixins import (
    WithDocumentUploadFormMixin,
    WithDocumentListInContextMixin,
    WithMessagesListInContextMixin,
    WithContactListInContextMixin,
    WithFreeLinksListInContextMixin,
)
from core.redirect import safe_redirect
from sv.forms import (
    FreeLinkForm,
    FicheDetectionVisibiliteUpdateForm,
    FicheZoneDelimiteeForm,
    ZoneInfesteeFormSet,
    RattachementDetectionForm,
    RattachementChoices,
)
from .export import FicheDetectionExport
from .filters import FicheDetectionFilter
from .models import (
    FicheDetection,
    Lieu,
    Prelevement,
    StatutEvenement,
    OrganismeNuisible,
    StatutReglementaire,
    Contexte,
    StructurePreleveur,
    SiteInspection,
    MatricePrelevee,
    LaboratoireAgree,
    LaboratoireConfirmationOfficielle,
    NumeroFiche,
    Departement,
    TypeExploitant,
    PositionChaineDistribution,
    FicheZoneDelimitee,
)
from core.models import Visibilite


class FicheDetectionListView(ListView):
    model = FicheDetection
    paginate_by = 100
    context_object_name = "fiches"

    def get_queryset(self):
        queryset = FicheDetection.objects.all().get_fiches_user_can_view(self.request.user)
        queryset = queryset.with_list_of_lieux().with_first_region_name().optimized_for_list().order_by_numero_fiche()
        self.filter = FicheDetectionFilter(self.request.GET, queryset=queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filter
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
    queryset = FicheDetection.objects.select_related(
        "statut_reglementaire", "etat", "numero", "contexte", "createur", "statut_evenement", "organisme_nuisible"
    )

    def get_object(self, queryset=None):
        if hasattr(self, "object"):
            return self.object

        self.object = super().get_object(queryset)
        return self.object

    def get_object_linked_to_document(self):
        return self.get_object()

    def _get_free_link_form(self):
        return FreeLinkForm(
            content_type_1=ContentType.objects.get_for_model(self.get_object()).pk, object_id_1=self.get_object().pk
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lieux"] = (
            Lieu.objects.filter(fiche_detection=self.get_object()).order_by("id").select_related("departement__region")
        )
        prelevement = Prelevement.objects.filter(lieu__fiche_detection=self.get_object())
        context["prelevements"] = prelevement.select_related(
            "structure_preleveur",
            "lieu",
            "matrice_prelevee",
            "site_inspection",
            "espece_echantillon",
            "laboratoire_agree",
        )
        context["free_link_form"] = self._get_free_link_form()
        context["content_type"] = ContentType.objects.get_for_model(self.get_object())
        contacts_not_in_fin_suivi = FicheDetection.objects.all().get_contacts_structures_not_in_fin_suivi(
            self.get_object()
        )
        context["contacts_not_in_fin_suivi"] = contacts_not_in_fin_suivi
        context["can_cloturer_fiche"] = len(contacts_not_in_fin_suivi) == 0
        context["can_update_visibilite"] = self.get_object().can_update_visibilite(self.request.user)
        context["visibilite_form"] = FicheDetectionVisibiliteUpdateForm(obj=self.get_object())
        context["rattachement_detection_form"] = RattachementDetectionForm()
        return context

    def test_func(self) -> bool | None:
        """Vérifie si l'utilisateur peut accéder à la vue (cf. UserPassesTestMixin)."""
        return self.get_object().can_user_access(self.request.user)

    def handle_no_permission(self):
        """Affiche une erreur 403 Forbidden si l'utilisateur n'a pas la permission d'accéder à la vue. (cf. UserPassesTestMixin)."""
        raise PermissionDenied()


class FicheDetectionContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuts_evenement"] = StatutEvenement.objects.all()
        context["organismes_nuisibles"] = OrganismeNuisible.objects.all()
        context["statuts_reglementaires"] = StatutReglementaire.objects.all()
        context["contextes"] = Contexte.objects.all()
        context["structures_preleveurs"] = list(StructurePreleveur.objects.values("id", "nom").order_by("nom"))
        context["sites_inspections"] = list(SiteInspection.objects.values("id", "nom").order_by("nom"))
        context["matrices_prelevees"] = MatricePrelevee.objects.all().order_by("libelle")
        if self.allows_inactive_laboratoires_agrees_values:
            context["laboratoires_agrees"] = LaboratoireAgree._base_manager.order_by("nom")
        else:
            context["laboratoires_agrees"] = LaboratoireAgree.objects.all().order_by("nom")
        if self.allows_inactive_laboratoires_confirmation_values:
            queryset = LaboratoireConfirmationOfficielle._base_manager.order_by("nom")
        else:
            queryset = LaboratoireConfirmationOfficielle.objects.all().order_by("nom")
        context["laboratoires_confirmation_officielle"] = queryset
        context["resultats_prelevement"] = Prelevement.Resultat.choices
        context["types_etablissement"] = TypeExploitant.objects.all().order_by("libelle")
        context["positions_chaine_distribution"] = PositionChaineDistribution.objects.all().order_by("libelle")
        return context


class FicheDetectionCreateView(FicheDetectionContextMixin, CreateView):
    allows_inactive_laboratoires_agrees_values = False
    allows_inactive_laboratoires_confirmation_values = False
    model = FicheDetection
    fields = [
        "statut_evenement",
        "organisme_nuisible",
        "statut_reglementaire",
        "contexte",
        "date_premier_signalement",
        "commentaire",
        "mesures_conservatoires_immediates",
        "mesures_consignation",
        "mesures_phytosanitaires",
        "mesures_surveillance_specifique",
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_creation"] = True
        return context

    def post(self, request):
        # Récupération des données du formulaire
        data = request.POST
        lieux = json.loads(data["lieux"])
        prelevements = json.loads(data["prelevements"])

        # Validation des données
        errors = self.validate_data(data, lieux, prelevements)
        if errors:
            for error in errors:
                messages.error(request, error)
            return HttpResponseBadRequest(json.dumps(errors))

        # Création des objets en base de données
        with transaction.atomic():
            fiche = self.create_fiche_detection(data, request.user.agent.structure)
            self.create_lieux(lieux, fiche)
            self.create_prelevements(prelevements, lieux)

        return HttpResponseRedirect(reverse("fiche-detection-vue-detaillee", args=[fiche.pk]))

    def validate_data(self, data, lieux, prelevements):
        errors = []

        # Validation des lieux (nom du lieu obligatoire)
        for lieu in lieux:
            if not lieu["nomLieu"]:
                errors.append("Le champ nom du lieu est obligatoire")
            if lieu["departementNom"]:
                try:
                    lieu["departement"] = Departement.objects.get(nom=lieu["departementNom"])
                except Departement.DoesNotExist:
                    errors.append("Le champ département est invalide")

        # Validation des prélèvements
        lieu_ids = [lieu["id"] for loc in lieux]
        for prelevement in prelevements:
            # chaque prélèvement doit être associé à un lieu
            if prelevement["lieuId"] not in lieu_ids:
                errors.append(f"Le prélèvement avec l'id {prelevement['id']} n'est relié à aucun lieu")
            # structure preleveur doit être valide (existe en base de données)
            if (
                prelevement["structurePreleveurId"]
                and not StructurePreleveur.objects.filter(pk=prelevement["structurePreleveurId"]).exists()
            ):
                errors.append("Le champ structure preleveur est invalide")
            # site inspection doit être valide (existe en base de données)
            if (
                prelevement["siteInspectionId"]
                and not SiteInspection.objects.filter(pk=prelevement["siteInspectionId"]).exists()
            ):
                errors.append("Le champ site inspection est invalide")
            # matrice prelevée doit être valide (existe en base de données)
            if (
                prelevement["matricePreleveeId"]
                and not MatricePrelevee.objects.filter(pk=prelevement["matricePreleveeId"]).exists()
            ):
                errors.append("Le champ matrice prelevée est invalide")
            # si c'est un prélèvement officiel, laboratoire agréé et/ou laboratoireConfirmationOfficielleId doit être valide (existe en base de données)
            if prelevement["isOfficiel"]:
                if (
                    prelevement["laboratoireAgreeId"]
                    and not LaboratoireAgree.objects.filter(pk=prelevement["laboratoireAgreeId"]).exists()
                ):
                    errors.append("Le champ laboratoire agréé est invalide")
                if (
                    prelevement["laboratoireConfirmationOfficielleId"]
                    and not LaboratoireConfirmationOfficielle.objects.filter(
                        pk=prelevement["laboratoireConfirmationOfficielleId"]
                    ).exists()
                ):
                    errors.append("Le champ laboratoire confirmation officielle est invalide")
        return errors

    def create_fiche_detection(self, data, user_structure):
        # format de la date de premier signalement
        date_premier_signalement = data["datePremierSignalement"]
        try:
            datetime.strptime(date_premier_signalement, "%Y-%m-%d")
        except ValueError:
            date_premier_signalement = None

        # Création de la fiche de détection en base de données
        fiche = FicheDetection(
            numero=NumeroFiche.get_next_numero(),
            createur=user_structure,
            statut_evenement_id=data["statutEvenementId"],
            organisme_nuisible_id=data["organismeNuisibleId"],
            statut_reglementaire_id=data["statutReglementaireId"],
            contexte_id=data["contexteId"],
            date_premier_signalement=date_premier_signalement,
            commentaire=data["commentaire"],
            mesures_conservatoires_immediates=data["mesuresConservatoiresImmediates"],
            mesures_consignation=data["mesuresConsignation"],
            mesures_phytosanitaires=data["mesuresPhytosanitaires"],
            mesures_surveillance_specifique=data["mesuresSurveillanceSpecifique"],
        )

        if data["action"] == "publier":
            fiche.visibilite = Visibilite.LOCAL

        fiche.save()
        fiche.contacts.add(self.request.user.agent.contact_set.get())
        fiche.contacts.add(self.request.user.agent.structure.contact_set.get())
        return fiche

    def create_lieux(self, lieux, fiche):
        # Création des lieux en base de données
        for lieu in lieux:
            wgs84_longitude = lieu["coordGPSWGS84Longitude"] if lieu["coordGPSWGS84Longitude"] != "" else None
            wgs84_latitude = lieu["coordGPSWGS84Latitude"] if lieu["coordGPSWGS84Latitude"] != "" else None
            lambert93_longitude = (
                lieu["coordGPSLambert93Longitude"] if lieu["coordGPSLambert93Longitude"] != "" else None
            )
            lambert93_latitude = lieu["coordGPSLambert93Latitude"] if lieu["coordGPSLambert93Latitude"] != "" else None

            lieu_instance = Lieu(
                fiche_detection=fiche,
                nom=lieu["nomLieu"],
                wgs84_longitude=wgs84_longitude,
                wgs84_latitude=wgs84_latitude,
                lambert93_longitude=lambert93_longitude,
                lambert93_latitude=lambert93_latitude,
                adresse_lieu_dit=lieu["adresseLieuDit"],
                commune=lieu["commune"],
                code_insee=lieu.get("codeINSEE"),
                departement=lieu.get("departement"),
                is_etablissement=lieu["isEtablissement"],
                nom_etablissement=lieu["nomEtablissement"],
                activite_etablissement=lieu["activiteEtablissement"],
                pays_etablissement=lieu["paysEtablissement"],
                raison_sociale_etablissement=lieu["raisonSocialeEtablissement"],
                adresse_etablissement=lieu["adresseEtablissement"],
                siret_etablissement=lieu["siretEtablissement"],
                code_inpp_etablissement=lieu["codeInppEtablissement"],
                type_exploitant_etablissement_id=lieu["typeEtablissementId"],
                position_chaine_distribution_etablissement_id=lieu["positionEtablissementId"],
            )
            lieu_instance.save()
            lieu["lieu_pk"] = lieu_instance.pk
        return lieux

    def create_prelevements(self, prelevements, lieux):
        # Création des prélèvements en base de données
        for prel in prelevements:
            # format de la date de prélèvement
            try:
                datetime.strptime(prel["datePrelevement"], "%Y-%m-%d")
            except ValueError:
                prel["datePrelevement"] = None

            # recupérer le lieu_pk associé à chaque prélèvement prel
            prel["lieu_pk"] = next(
                (loc["lieu_pk"] for loc in lieux if loc["id"] == prel["lieuId"]),
                None,
            )
            prelevement = Prelevement(
                lieu_id=prel["lieu_pk"],
                structure_preleveur_id=prel["structurePreleveurId"],
                numero_echantillon=prel["numeroEchantillon"],
                date_prelevement=prel["datePrelevement"],
                site_inspection_id=prel["siteInspectionId"],
                matrice_prelevee_id=prel["matricePreleveeId"],
                espece_echantillon_id=prel["especeEchantillonId"],
                is_officiel=prel["isOfficiel"],
                numero_phytopass=prel["numeroPhytopass"],
                numero_resytal=prel["numeroResytal"],
                laboratoire_agree_id=prel["laboratoireAgreeId"],
                laboratoire_confirmation_officielle_id=prel["laboratoireConfirmationOfficielleId"],
                resultat=prel["resultat"],
            )
            prelevement.save()


class FicheDetectionUpdateView(FicheDetectionContextMixin, UpdateView):
    model = FicheDetection
    fields = [
        "statut_evenement",
        "organisme_nuisible",
        "statut_reglementaire",
        "contexte",
        "date_premier_signalement",
        "commentaire",
        "mesures_conservatoires_immediates",
        "mesures_consignation",
        "mesures_phytosanitaires",
        "mesures_surveillance_specifique",
    ]
    success_message = "La fiche détection a été modifiée avec succès."

    @property
    def allows_inactive_laboratoires_agrees_values(self):
        actual_ids = Prelevement.objects.filter(lieu__fiche_detection__pk=self.object.pk).values_list(
            "laboratoire_agree_id", flat=True
        )
        inactive_ids = LaboratoireAgree._base_manager.filter(is_active=False).values_list("id", flat=True)
        return any([pk in inactive_ids for pk in actual_ids if pk])

    @property
    def allows_inactive_laboratoires_confirmation_values(self):
        actual_ids = Prelevement.objects.filter(lieu__fiche_detection__pk=self.object.pk).values_list(
            "laboratoire_confirmation_officielle_id", flat=True
        )
        inactive_ids = LaboratoireConfirmationOfficielle._base_manager.filter(is_active=False).values_list(
            "id", flat=True
        )
        return any([pk in inactive_ids for pk in actual_ids if pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Lieux associés à la fiche de détection
        lieux = (
            Lieu.objects.filter(fiche_detection=self.object).values().annotate(departement_nom=F("departement__nom"))
        )

        # Prélèvements associés à chaque lieu
        prelevements = (
            Prelevement.objects.filter(lieu__fiche_detection=self.object)
            .values()
            .annotate(espece_echantillon_name=F("espece_echantillon__libelle"))
        )
        for prelevement in prelevements:
            prelevement["uuid"] = str(uuid.uuid4())

        context["is_creation"] = False
        context["lieux"] = list(lieux)
        context["prelevements"] = list(prelevements)

        return context

    def update_fiche_detection(self, data, fiche_detection):
        # Format de la date de premier signalement
        date_premier_signalement = data["datePremierSignalement"]
        try:
            datetime.strptime(date_premier_signalement, "%Y-%m-%d")
        except ValueError:
            date_premier_signalement = None

        # Mise à jour des champs de l'objet FicheDetection
        fiche_detection.statut_evenement_id = data.get("statutEvenementId")
        fiche_detection.organisme_nuisible_id = data.get("organismeNuisibleId")
        fiche_detection.statut_reglementaire_id = data.get("statutReglementaireId")
        fiche_detection.contexte_id = data.get("contexteId")
        fiche_detection.date_premier_signalement = date_premier_signalement
        fiche_detection.commentaire = data.get("commentaire")
        fiche_detection.mesures_conservatoires_immediates = data.get("mesuresConservatoiresImmediates")
        fiche_detection.mesures_consignation = data.get("mesuresConsignation")
        fiche_detection.mesures_phytosanitaires = data.get("mesuresPhytosanitaires")
        fiche_detection.mesures_surveillance_specifique = data.get("mesuresSurveillanceSpecifique")

        try:
            fiche_detection.full_clean()
        except ValidationError as e:
            return fiche_detection, e

        return fiche_detection, None

    def update_lieux(self, lieux, fiche_detection):
        # Suppression des lieux qui ne sont plus dans la liste
        lieux_a_supprimer = Lieu.objects.filter(fiche_detection=fiche_detection).exclude(
            pk__in=[loc["pk"] for loc in lieux if "pk" in loc]
        )
        lieux_a_supprimer.delete()

        # Création ou mise à jour des lieux
        for loc in lieux:
            # Création ou récupération de l'objet Lieu
            # si pk -> update
            # si pas de pk -> création
            lieu = Lieu.objects.get(pk=loc["pk"]) if loc.get("pk") else Lieu(fiche_detection=fiche_detection)
            departement = None
            if loc["departementNom"]:
                departement = Departement.objects.get(nom=loc["departementNom"])
            lieu.nom = loc["nomLieu"]
            lieu.wgs84_longitude = loc["coordGPSWGS84Longitude"] if loc["coordGPSWGS84Longitude"] != "" else None
            lieu.wgs84_latitude = loc["coordGPSWGS84Latitude"] if loc["coordGPSWGS84Latitude"] != "" else None
            lieu.lambert93_latitude = (
                loc["coordGPSLambert93Latitude"] if loc["coordGPSLambert93Latitude"] != "" else None
            )
            lieu.lambert93_longitude = (
                loc["coordGPSLambert93Longitude"] if loc["coordGPSLambert93Longitude"] != "" else None
            )
            lieu.adresse_lieu_dit = loc["adresseLieuDit"]
            lieu.commune = loc.get("commune")
            lieu.code_insee = loc.get("codeINSEE")
            lieu.departement = departement
            lieu.is_etablissement = loc["isEtablissement"]
            if loc["isEtablissement"]:
                lieu.nom_etablissement = loc["nomEtablissement"]
                lieu.activite_etablissement = loc["activiteEtablissement"]
                lieu.pays_etablissement = loc["paysEtablissement"]
                lieu.raison_sociale_etablissement = loc["raisonSocialeEtablissement"]
                lieu.adresse_etablissement = loc["adresseEtablissement"]
                lieu.siret_etablissement = loc["siretEtablissement"]
                lieu.code_inpp_etablissement = loc["codeInppEtablissement"]
                lieu.type_exploitant_etablissement_id = loc["typeEtablissementId"]
                lieu.position_chaine_distribution_etablissement_id = loc["positionEtablissementId"]
            else:
                lieu.nom_etablissement = ""
                lieu.activite_etablissement = ""
                lieu.pays_etablissement = ""
                lieu.raison_sociale_etablissement = ""
                lieu.adresse_etablissement = ""
                lieu.siret_etablissement = ""
                lieu.type_exploitant_etablissement_id = None
                lieu.position_chaine_distribution_etablissement_id = None
            lieu.save()
            loc["lieu_pk"] = lieu.pk

    def update_prelevements(self, prelevements, lieux, fiche_detection):
        # Suppression des prélèvements qui ne sont plus dans la liste
        prelevements_a_supprimer = Prelevement.objects.filter(lieu__fiche_detection=fiche_detection).exclude(
            pk__in=[prel["pk"] for prel in prelevements if "pk" in prel]
        )
        prelevements_a_supprimer.delete()

        for prel in prelevements:
            # recupérer le lieu_pk associé à chaque prélèvement prel
            prel["lieu_pk"] = next(
                (loc["lieu_pk"] for loc in lieux if loc["id"] == prel["lieuId"]),
                None,
            )

            # Création ou récupération de l'objet Prelevement
            # si pk -> update
            # si pas de pk -> création
            prelevement = Prelevement.objects.get(pk=prel["pk"]) if prel.get("pk") else Prelevement()
            prelevement.lieu_id = prel["lieu_pk"]
            prelevement.structure_preleveur_id = prel["structurePreleveurId"]
            prelevement.numero_echantillon = prel["numeroEchantillon"] if prel["numeroEchantillon"] else ""
            prelevement.date_prelevement = prel["datePrelevement"]
            prelevement.site_inspection_id = prel["siteInspectionId"]
            prelevement.matrice_prelevee_id = prel["matricePreleveeId"]
            prelevement.espece_echantillon_id = prel["especeEchantillonId"]
            prelevement.is_officiel = prel["isOfficiel"]
            prelevement.numero_phytopass = (
                prel["numeroPhytopass"] if prel["isOfficiel"] and prel["numeroPhytopass"] else ""
            )
            prelevement.numero_resytal = prel["numeroResytal"] if prel["isOfficiel"] and prel["numeroResytal"] else ""
            prelevement.laboratoire_agree_id = prel["laboratoireAgreeId"] if prel["isOfficiel"] else None
            prelevement.laboratoire_confirmation_officielle_id = (
                prel["laboratoireConfirmationOfficielleId"] if prel["isOfficiel"] else None
            )
            prelevement.resultat = prel["resultat"]
            prelevement.save()

    def post(self, request, pk):
        data = request.POST
        lieux = json.loads(data["lieux"])
        prelevements = json.loads(data["prelevements"])

        # Mise à jour des objets en base de données
        with transaction.atomic():
            fiche_detection, error = self.update_fiche_detection(data, self.get_object())
            if error:
                return HttpResponseBadRequest(str(error))
            fiche_detection.save()

            self.update_lieux(lieux, fiche_detection)
            self.update_prelevements(prelevements, lieux, fiche_detection)

        messages.success(request, self.success_message)
        return redirect(reverse("fiche-detection-vue-detaillee", args=[fiche_detection.pk]))


class FreeLinkCreateView(FormView):
    form_class = FreeLinkForm

    def post(self, request, *args, **kwargs):
        form = FreeLinkForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Ce lien existe déjà.")
            return safe_redirect(self.request.POST.get("next"))

        try:
            form.save()
        except IntegrityError:
            messages.error(request, "Vous ne pouvez pas lier un objet à lui même.")
            return safe_redirect(self.request.POST.get("next"))

        messages.success(request, "Le lien a été créé avec succès.")
        return safe_redirect(self.request.POST.get("next"))


class FicheDetectionExportView(View):
    http_method_names = ["post"]

    def post(self, request):
        response = HttpResponse(content_type="text/csv")
        FicheDetectionExport().export(stream=response)
        response["Content-Disposition"] = "attachment; filename=export_fiche_detection.csv"
        return response


class FicheDetecionCloturerView(View):
    redirect_url_name = "fiche-detection-vue-detaillee"

    def get_redirect_url(self, fiche_pk):
        return reverse(self.redirect_url_name, args=[fiche_pk])

    def post(self, request, pk):
        fiche = FicheDetection.objects.get(pk=pk)
        redirect_url = self.get_redirect_url(pk)

        if not fiche.can_be_cloturer_by(request.user):
            messages.error(request, "Vous n'avez pas les droits pour clôturer une fiche de détection.")
            return redirect(redirect_url)

        if fiche.is_already_cloturer():
            messages.error(request, f"La fiche de détection n° {fiche.numero} est déjà clôturée.")
            return redirect(redirect_url)

        contacts_not_in_fin_suivi = FicheDetection.objects.all().get_contacts_structures_not_in_fin_suivi(fiche)
        if contacts_not_in_fin_suivi:
            messages.error(
                request,
                f"La fiche de détection n° {fiche.numero} ne peut pas être clôturée car les structures suivantes n'ont pas signalées la fin de suivi : {', '.join([str(contact) for contact in contacts_not_in_fin_suivi])}",
            )
            return redirect(redirect_url)

        fiche.cloturer()
        messages.success(request, f"La fiche de détection n° {fiche.numero} a bien été clôturée.")
        return redirect(redirect_url)


class FicheDetectionVisibiliteUpdateView(UpdateView):
    model = FicheDetection
    form_class = FicheDetectionVisibiliteUpdateForm
    http_method_names = ["post"]

    def get_success_url(self):
        return reverse("fiche-detection-vue-detaillee", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "La visibilité de la fiche détection a bien été modifiée.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "La visibilité de la fiche détection n'a pas pu être modifiée.")
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
    success_url = reverse_lazy("fiche-detection-list")

    def get(self, request, *args, **kwargs):
        self.object = None

        fiche_detection = FicheDetection.objects.get(pk=self.request.GET.get("fiche_detection_id"))

        if fiche_detection.is_linked_to_fiche_zone_delimitee:
            return HttpResponseBadRequest("La fiche de détection est déjà rattachée à une fiche zone délimitée.")

        self.on = fiche_detection.organisme_nuisible
        match self.request.GET.get("rattachement"):
            case RattachementChoices.HORS_ZONE_INFESTEE:
                self.hors_zone_infestee_detection = [fiche_detection]
            case RattachementChoices.ZONE_INFESTEE:
                self.zone_infestee_detection = fiche_detection

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["zone_infestee_formset"] = ZoneInfesteeFormSet(self.request.POST)
        else:
            context["zone_infestee_formset"] = ZoneInfesteeFormSet(
                organisme_nuisible=self.on, detection=getattr(self, "zone_infestee_detection", None)
            )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["detections_zones_infestees_formset"] = getattr(self, "detections_zones_infestees_formset", set())
        return kwargs

    def get_initial(self):
        if self.request.GET:
            fiche_detection = FicheDetection.objects.get(pk=self.request.GET.get("fiche_detection_id"))
            return {
                "organisme_nuisible": fiche_detection.organisme_nuisible,
                "statut_reglementaire": fiche_detection.statut_reglementaire,
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
