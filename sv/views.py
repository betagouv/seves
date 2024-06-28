from typing import Optional, Union, Tuple
import json
from datetime import datetime, time
import uuid
from django.utils import timezone
from django.shortcuts import redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
)
from django.urls import reverse
from django.db.models import OuterRef, Subquery, Prefetch
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib import messages
from django import forms
from .models import (
    FicheDetection,
    Lieu,
    Prelevement,
    Unite,
    StatutEvenement,
    OrganismeNuisible,
    StatutReglementaire,
    Contexte,
    StructurePreleveur,
    SiteInspection,
    MatricePrelevee,
    EspeceEchantillon,
    LaboratoireAgree,
    LaboratoireConfirmationOfficielle,
    NumeroFiche,
    Departement,
    Region,
    Etat,
)
from common.mixins import DSFRFormMixin


class FicheDetectionSearchForm(forms.Form, DSFRFormMixin):
    numero = forms.CharField(
        label="Numéro",
        required=False,
        widget=forms.TextInput(attrs={"pattern": "^[0-9]{4}\\.[0-9]+$", "title": "Format attendu : ANNEE.NUMERO"}),
    )
    region = forms.ModelChoiceField(label="Région", queryset=Region.objects.all(), required=False)
    organisme_nuisible = forms.ModelChoiceField(
        label="Organisme", queryset=OrganismeNuisible.objects.all(), required=False
    )
    date_debut = forms.DateField(label="Période du", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    date_fin = forms.DateField(label="Au", widget=forms.DateInput(attrs={"type": "date"}), required=False)
    etat = forms.ModelChoiceField(label="État", queryset=Etat.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_form_css_classes()

    def clean_numero(self) -> Optional[Union[Tuple[int, int], str]]:
        """Vérifie que le champ 'numero' est au format 'annee.numero' et le retourne sous forme de tuple (annee, numero)."""
        numero = self.cleaned_data["numero"]
        if numero:
            try:
                annee, numero = map(int, numero.split("."))
                return annee, numero
            except ValueError:
                raise forms.ValidationError("Format 'numero' invalide. Il devrait être 'annee.numero'")
        return numero


class FicheDetectionListView(ListView):
    model = FicheDetection
    ordering = ["-numero"]
    paginate_by = 10

    def get_queryset(self):
        # Pour chaque fiche de détection, on récupère la liste des lieux associés
        lieux_prefetch = Prefetch("lieux", queryset=Lieu.objects.order_by("id"), to_attr="lieux_list")
        queryset = super().get_queryset().prefetch_related(lieux_prefetch)

        # Pour chaque fiche de détection, on récupère le nom de la région du premier lieu associé
        first_lieu = Lieu.objects.filter(fiche_detection=OuterRef("pk")).order_by("id")
        queryset = queryset.annotate(
            region=Subquery(first_lieu.values("departement__region__nom")[:1]),
        )

        form = FicheDetectionSearchForm(self.request.GET)

        if not form.is_valid():
            return queryset

        if form.cleaned_data["numero"]:
            annee, numero = form.cleaned_data["numero"]
            return queryset.filter(numero__annee=annee, numero__numero=numero)

        if form.cleaned_data["region"]:
            queryset = queryset.filter(lieux__departement__region=form.cleaned_data["region"])

        if form.cleaned_data["organisme_nuisible"]:
            queryset = queryset.filter(organisme_nuisible=form.cleaned_data["organisme_nuisible"])

        if form.cleaned_data["date_debut"] and form.cleaned_data["date_fin"]:
            # Ajustement des dates de début et de fin pour inclure les fiches créées le jour même.
            # La date de début est définie à minuit (00:00:00) et la date de fin à la dernière seconde de la journée (23:59:59).
            # Cela permet d'inclure toutes les fiches créées dans la plage de dates spécifiée.
            # Si ces dates ne sont pas ajustées, les valeurs de date_debut et date_fin serait égales à 2024-06-19 00:00:00 et 2024-06-19 00:00:00 respectivement
            # donc les fiches créées le 2024-06-19 à 00:00:01 et après ne seraient pas incluses dans les résultats.
            date_debut = timezone.make_aware(datetime.combine(form.cleaned_data["date_debut"], time.min))
            date_fin = timezone.make_aware(datetime.combine(form.cleaned_data["date_fin"], time.max))
            queryset = queryset.filter(date_creation__range=(date_debut, date_fin))

        if form.cleaned_data["etat"]:
            queryset = queryset.filter(etat=form.cleaned_data["etat"])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = FicheDetectionSearchForm(self.request.GET)
        return context


class FicheDetectionDetailView(DetailView):
    model = FicheDetection

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ajout des lieux associés à la fiche de détection
        context["lieux"] = Lieu.objects.filter(fiche_detection=self.get_object())

        # Ajout des prélèvements associés à chaque lieu
        context["prelevements"] = Prelevement.objects.filter(lieu__fiche_detection=self.get_object())

        return context


class FicheDetectionContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["departements"] = list(Departement.objects.values("id", "numero", "nom"))
        context["unites"] = list(Unite.objects.values("id", "nom"))
        context["statuts_evenement"] = list(StatutEvenement.objects.values("id", "libelle"))
        context["organismes_nuisibles"] = list(OrganismeNuisible.objects.values("id", "libelle_court"))
        context["statuts_reglementaires"] = list(StatutReglementaire.objects.values("id", "libelle"))
        context["contextes"] = list(Contexte.objects.values("id", "nom"))
        context["structures_preleveurs"] = list(StructurePreleveur.objects.values("id", "nom").order_by("nom"))
        context["sites_inspections"] = list(SiteInspection.objects.values("id", "nom").order_by("nom"))
        context["matrices_prelevees"] = list(MatricePrelevee.objects.values("id", "libelle").order_by("libelle"))
        context["especes_echantillon"] = list(EspeceEchantillon.objects.values("id", "libelle").order_by("libelle"))
        context["laboratoires_agrees"] = list(LaboratoireAgree.objects.values("id", "nom").order_by("nom"))
        context["laboratoires_confirmation_officielle"] = list(
            LaboratoireConfirmationOfficielle.objects.values("id", "nom").order_by("nom")
        )
        return context


class FicheDetectionCreateView(FicheDetectionContextMixin, CreateView):
    model = FicheDetection
    fields = [
        "createur",
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
            return HttpResponseBadRequest(json.dumps(errors))

        # Création des objets en base de données
        with transaction.atomic():
            fiche = self.create_fiche_detection(data)
            self.create_lieux(lieux, fiche)
            self.create_prelevements(prelevements, lieux)

        return HttpResponseRedirect(reverse("fiche-detection-vue-detaillee", args=[fiche.pk]))

    def validate_data(self, data, lieux, prelevements):
        errors = []

        # createur est obligatoire
        if not data["createurId"]:
            errors.append("Le champ createur est obligatoire")
        elif not Unite.objects.filter(pk=data["createurId"]).exists():
            errors.append("Le champ createur est invalide")

        # Validation des lieux (nom du lieu obligatoire)
        for lieu in lieux:
            if not lieu["nomLieu"]:
                errors.append("Le champ nom du lieu est obligatoire")
            if lieu["departementId"] and not Departement.objects.filter(pk=lieu["departementId"]).exists():
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

    def create_fiche_detection(self, data):
        # format de la date de premier signalement
        date_premier_signalement = data["datePremierSignalement"]
        try:
            datetime.strptime(date_premier_signalement, "%Y-%m-%d")
        except ValueError:
            date_premier_signalement = None

        # Création de la fiche de détection en base de données
        fiche = FicheDetection(
            numero=NumeroFiche.get_next_numero(),
            createur_id=data["createurId"],
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
        fiche.save()

        return fiche

    def create_lieux(self, lieux, fiche):
        # Création des lieux en base de données
        for lieu in lieux:
            wgs84_longitude = lieu["coordGPSWGS84Longitude"] if lieu["coordGPSWGS84Longitude"] != "" else None
            wgs84_latitude = lieu["coordGPSWGS84Latitude"] if lieu["coordGPSWGS84Latitude"] != "" else None

            # lieu = Lieu(fiche_detection=fiche, **lieu)
            lieu_instance = Lieu(
                fiche_detection=fiche,
                nom=lieu["nomLieu"],
                wgs84_longitude=wgs84_longitude,
                wgs84_latitude=wgs84_latitude,
                adresse_lieu_dit=lieu["adresseLieuDit"],
                commune=lieu["commune"],
                code_insee=lieu["codeINSEE"],
                departement_id=lieu["departementId"],
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
                laboratoire_agree_id=prel["laboratoireAgreeId"],
                laboratoire_confirmation_officielle_id=prel["laboratoireConfirmationOfficielleId"],
            )
            prelevement.save()


class FicheDetectionUpdateView(FicheDetectionContextMixin, UpdateView):
    model = FicheDetection
    fields = [
        "createur",
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Lieux associés à la fiche de détection
        lieux = Lieu.objects.filter(fiche_detection=self.object).values()

        # Prélèvements associés à chaque lieu
        prelevements = Prelevement.objects.filter(lieu__fiche_detection=self.object).values()
        for prelevement in prelevements:
            prelevement["uuid"] = str(uuid.uuid4())

        context["is_creation"] = False
        context["lieux"] = list(lieux)
        context["prelevements"] = list(prelevements)

        return context

    def validate_data(self, data):
        errors = []
        if not data["createurId"]:
            errors.append("Le champ createur est obligatoire")
        elif not Unite.objects.filter(pk=data["createurId"]).exists():
            errors.append("Le champ createur est invalide")
        return errors

    def update_fiche_detection(self, data, fiche_detection):
        # Format de la date de premier signalement
        date_premier_signalement = data["datePremierSignalement"]
        try:
            datetime.strptime(date_premier_signalement, "%Y-%m-%d")
        except ValueError:
            date_premier_signalement = None

        # Mise à jour des champs de l'objet FicheDetection
        fiche_detection.createur_id = data.get("createurId")
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
            lieu.commune = loc["commune"]
            lieu.code_insee = loc["codeINSEE"]
            lieu.departement_id = loc["departementId"]
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
            prelevement.numero_phytopass = prel["numeroPhytopass"] if prel["isOfficiel"] else ""
            prelevement.laboratoire_agree_id = prel["laboratoireAgreeId"] if prel["isOfficiel"] else None
            prelevement.laboratoire_confirmation_officielle_id = (
                prel["laboratoireConfirmationOfficielleId"] if prel["isOfficiel"] else None
            )
            prelevement.save()

    def post(self, request, pk):
        data = request.POST
        lieux = json.loads(data["lieux"])
        prelevements = json.loads(data["prelevements"])

        # Validation
        errors = self.validate_data(data)
        if errors:
            return HttpResponseBadRequest(json.dumps(errors))

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
