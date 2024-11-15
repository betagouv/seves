import json
from datetime import datetime
import uuid

from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.shortcuts import redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    FormView,
)
from django.urls import reverse
from django.db.models import F, Prefetch
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin

from core.content_types import content_type_str_to_obj
from core.mixins import (
    WithDocumentUploadFormMixin,
    WithDocumentListInContextMixin,
    WithMessagesListInContextMixin,
    WithContactListInContextMixin,
    WithFreeLinksListInContextMixin,
)
from core.redirect import safe_redirect
from sv.forms import (
    FicheDetectionVisibiliteUpdateForm,
    FicheZoneDelimiteeForm,
    ZoneInfesteeFormSet,
    ZoneInfesteeFormSetUpdate,
    RattachementDetectionForm,
    RattachementChoices,
    FicheZoneDelimiteeVisibiliteUpdateForm,
)
from .display import DisplayedFiche
from .export import FicheDetectionExport
from .filters import FicheFilter
from .constants import KNOWN_OEPPS, KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES
from .models import (
    FicheDetection,
    Lieu,
    Prelevement,
    StatutEvenement,
    OrganismeNuisible,
    StatutReglementaire,
    Contexte,
    StructurePreleveur,
    MatricePrelevee,
    LaboratoireAgree,
    LaboratoireConfirmationOfficielle,
    Departement,
    PositionChaineDistribution,
    FicheZoneDelimitee,
    ZoneInfestee,
    SiteInspection,
)
from core.models import Visibilite, LienLibre


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


class FicheDetectionContextMixin:
    def _add_status_to_organisme_nuisible(self, context, status):
        status_code_to_id = {s.code: s.id for s in status}
        oeep_to_nuisible_id = {
            organisme.code_oepp: organisme.id
            for organisme in OrganismeNuisible.objects.filter(code_oepp__in=KNOWN_OEPPS)
        }
        context["status_to_organisme_nuisible"] = [
            {"statusID": status_code_to_id[code], "nuisibleIds": [oeep_to_nuisible_id.get(oepp) for oepp in oepps]}
            for code, oepps in KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES.items()
        ]

    def _add_possible_links(self, context, user):
        possible_links = []

        content_type = ContentType.objects.get_for_model(FicheDetection)
        queryset = FicheDetection.objects.all().get_fiches_user_can_view(user).select_related("numero")
        possible_links.append((content_type.pk, "Fiche Détection", queryset))

        content_type = ContentType.objects.get_for_model(FicheZoneDelimitee)
        queryset = FicheZoneDelimitee.objects.all().get_fiches_user_can_view(user).select_related("numero")
        possible_links.append((content_type.pk, "Fiche zone délimitée", queryset))
        context["possible_links"] = possible_links

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuts_evenement"] = StatutEvenement.objects.all()
        context["organismes_nuisibles"] = OrganismeNuisible.objects.all()
        status = StatutReglementaire.objects.all()
        context["statuts_reglementaires"] = status
        context["contextes"] = Contexte.objects.all()
        if self.allows_inactive_structure_preleveur_values:
            queryset = StructurePreleveur._base_manager.values("id", "nom").order_by("nom")
        else:
            queryset = StructurePreleveur.objects.values("id", "nom").order_by("nom")
        context["structures_preleveurs"] = list(queryset)
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
        context["sites_inspections"] = list(SiteInspection.objects.all().values("id", "nom").order_by("nom"))
        context["positions_chaine_distribution"] = PositionChaineDistribution.objects.all().order_by("libelle")

        self._add_status_to_organisme_nuisible(context, status)
        self._add_possible_links(context, self.request.user)
        return context


class FicheDetectionCreateView(FicheDetectionContextMixin, CreateView):
    allows_inactive_laboratoires_agrees_values = False
    allows_inactive_laboratoires_confirmation_values = False
    allows_inactive_structure_preleveur_values = False
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
        errors = self.validate_data(request.POST, lieux, prelevements)
        if errors:
            for error in errors:
                messages.error(request, error)
            return HttpResponseBadRequest(json.dumps(errors))

        # Création des objets en base de données
        with transaction.atomic():
            fiche = self.create_fiche_detection(data, request.user.agent.structure)
            self.create_lieux(lieux, fiche)
            self.create_prelevements(prelevements, lieux)
            self.create_free_links(data, fiche)

        return HttpResponseRedirect(reverse("fiche-detection-vue-detaillee", args=[fiche.pk]))

    def validate_data(self, data, lieux, prelevements):
        errors = []

        # Validation des liens libres
        for free_link in data.getlist("freeLinksIds"):
            try:
                content_type_str_to_obj(free_link)
            except ObjectDoesNotExist:
                errors.append(f"Impossible de créer le lien libre {free_link}")

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
        lieu_ids = [lieu["id"] for lieu in lieux]
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

    def create_free_links(self, data, fiche):
        for free_link in data.getlist("freeLinksIds"):
            target_obj = content_type_str_to_obj(free_link)
            LienLibre.objects.create(related_object_1=fiche, related_object_2=target_obj)

    def create_fiche_detection(self, data, user_structure):
        # format de la date de premier signalement
        date_premier_signalement = data["datePremierSignalement"]
        try:
            datetime.strptime(date_premier_signalement, "%Y-%m-%d")
        except ValueError:
            date_premier_signalement = None

        additionnal_data = {}
        if self.request.user.agent.structure.is_ac:
            additionnal_data = {
                "numero_europhyt": data["numeroEurophyt"],
                "numero_rasff": data["numeroRasff"],
            }

        fiche = FicheDetection(
            createur=user_structure,
            statut_evenement_id=data["statutEvenementId"],
            **additionnal_data,
            organisme_nuisible_id=data["organismeNuisibleId"],
            statut_reglementaire_id=data["statutReglementaireId"],
            contexte_id=data["contexteId"],
            date_premier_signalement=date_premier_signalement,
            commentaire=data["commentaire"],
            vegetaux_infestes=data["vegetauxInfestes"],
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
                site_inspection_id=lieu["siteInspectionId"],
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

    @property
    def allows_inactive_structure_preleveur_values(self):
        actual_ids = Prelevement.objects.filter(lieu__fiche_detection__pk=self.object.pk).values_list(
            "structure_preleveur_id", flat=True
        )
        inactive_ids = StructurePreleveur._base_manager.filter(is_active=False).values_list("id", flat=True)
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
        fiche_detection.vegetaux_infestes = data.get("vegetauxInfestes")
        fiche_detection.mesures_conservatoires_immediates = data.get("mesuresConservatoiresImmediates")
        fiche_detection.mesures_consignation = data.get("mesuresConsignation")
        fiche_detection.mesures_phytosanitaires = data.get("mesuresPhytosanitaires")
        fiche_detection.mesures_surveillance_specifique = data.get("mesuresSurveillanceSpecifique")
        if self.request.user.agent.structure.is_ac:
            fiche_detection.numero_europhyt = data.get("numeroEurophyt")
            fiche_detection.numero_rasff = data.get("numeroRasff")
        if data.get("action") == "publier":
            fiche_detection.visibilite = Visibilite.LOCAL

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
            lieu.site_inspection_id = loc["siteInspectionId"]
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
                lieu.position_chaine_distribution_etablissement_id = loc["positionEtablissementId"]
            else:
                lieu.nom_etablissement = ""
                lieu.activite_etablissement = ""
                lieu.pays_etablissement = ""
                lieu.raison_sociale_etablissement = ""
                lieu.adresse_etablissement = ""
                lieu.siret_etablissement = ""
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
            prelevement.date_prelevement = prel["datePrelevement"] if prel["datePrelevement"] else None
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

    def update_free_links(self, free_links_ids, fiche_detection):
        links_ids_to_keep = []
        for free_link_id in free_links_ids:
            obj = content_type_str_to_obj(free_link_id)
            if obj == fiche_detection:
                messages.error(self.request, "Vous ne pouvez pas lier une fiche a elle-même.")
                continue
            link = LienLibre.objects.for_both_objects(obj, fiche_detection)

            if link:
                links_ids_to_keep.append(link.id)
            else:
                link = LienLibre.objects.create(related_object_1=fiche_detection, related_object_2=obj)
                links_ids_to_keep.append(link.id)

        links_to_delete = LienLibre.objects.for_object(fiche_detection).exclude(id__in=links_ids_to_keep)
        links_to_delete.delete()

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
            self.update_free_links(request.POST.getlist("freeLinksIds"), fiche_detection)

        messages.success(request, self.success_message)
        return redirect(reverse("fiche-detection-vue-detaillee", args=[fiche_detection.pk]))


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
