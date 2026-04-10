from collections import defaultdict
import json

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.http import Http404
from django.utils import timezone
import reversion
from reversion.models import Version

from core.mixins import WithOrderingMixin
from sv.forms import (
    PrelevementForm,
)

from .constants import KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES, KNOWN_OEPPS
from .filters import EvenementFilter
from .models import (
    Evenement,
    FicheDetection,
    Laboratoire,
    OrganismeNuisible,
    Prelevement,
    StatutReglementaire,
    StructurePreleveuse,
)


class WithStatusToOrganismeNuisibleMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_code_to_id = {s.code: s.id for s in StatutReglementaire.objects.all()}
        oeep_to_nuisible_id = {
            organisme.code_oepp: organisme.id
            for organisme in OrganismeNuisible.objects.filter(code_oepp__in=KNOWN_OEPPS)
        }
        context["status_to_organisme_nuisible"] = [
            {"statusID": status_code_to_id[code], "nuisibleIds": [oeep_to_nuisible_id.get(oepp) for oepp in oepps]}
            for code, oepps in KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES.items()
        ]
        return context


class WithPrelevementHandlingMixin:
    def _save_prelevement_if_not_empty(self, data, allowed_lieux, check_for_inactive_values=False, detection=None):
        sub_dicts = defaultdict(dict)
        for key, value in data.items():
            if key.startswith("prelevements-"):
                form_id = key.split("-")[1]
                sub_dicts[form_id][key] = value

        for form_id, form_data in sub_dicts.items():
            form_is_empty = not any(form_data.values())
            if form_is_empty:
                continue

            prelevement_id = form_data.pop("prelevements-" + form_id + "-id", None)
            form_is_empty = not any(form_data.values())

            if form_is_empty and prelevement_id:
                try:
                    # Cas 1 : Suppression d'un prélèvement uniquement (le lieu n'est pas supprimé)
                    prelevement = Prelevement.objects.get(id=prelevement_id)
                    prelevement.delete()
                except Prelevement.DoesNotExist:
                    # Cas 2 : Le prélèvement a déjà été supprimé car son lieu a été supprimé (cascade)
                    pass
                continue

            if prelevement_id:
                prelevement = Prelevement.objects.get(id=prelevement_id)
                if check_for_inactive_values:
                    labos = self._handle_inactive_values(Laboratoire, "laboratoire", detection.pk)
                    structure = self._handle_inactive_values(StructurePreleveuse, "structure_preleveuse", detection.pk)
                    prelevement_form = PrelevementForm(
                        form_data,
                        instance=prelevement,
                        prefix=f"prelevements-{form_id}",
                        labo_values=labos,
                        structure_values=structure,
                    )
                else:
                    prelevement_form = PrelevementForm(
                        form_data, instance=prelevement, prefix=f"prelevements-{form_id}"
                    )
            else:
                prelevement_form = PrelevementForm(form_data, prefix=f"prelevements-{form_id}")

            prelevement_form.fields["lieu"].queryset = allowed_lieux

            if prelevement_form.is_valid():
                with reversion.create_revision():
                    prelevement = prelevement_form.save()
                    lieu = prelevement.lieu
                    reversion.add_to_revision(lieu)
                    reversion.set_user(self.request.user)

                last_version = Version.objects.get_for_object(lieu).first()
                if last_version:
                    data = json.loads(last_version.serialized_data)
                    if isinstance(data, list) and len(data) > 0:
                        data[0]["fields"]["_forced_update_trigger"] = str(timezone.now())
                        last_version.serialized_data = json.dumps(data)
                        last_version.save(update_fields=["serialized_data"])
            else:
                error_msg = ""
                for field, error in prelevement_form.errors.items():
                    error_msg += f"{field.title()}: {error.as_text()}\n"
                raise ValidationError(error_msg)


class WithPrelevementResultatsMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["prelevement_resultats"] = dict(Prelevement.Resultat.choices)
        return context


class EvenementDetailMixin(UserPassesTestMixin):
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


class WithFilteredListMixin(WithOrderingMixin):
    def get_ordering_fields(self):
        return {
            "ac_notified": "is_ac_notified",
            "numero_evenement": ("numero_annee", "numero_evenement"),
            "organisme": "organisme_nuisible__libelle_court",
            "publication": "date_publication",
            "maj": "date_derniere_mise_a_jour_globale",
            "createur": "createur__libelle",
            "etat": "etat",
            "visibilite": "visibilite",
            "detections": "nb_fiches_detection",
            "zone": "fiche_zone_delimitee__id",
        }

    def get_default_order_by(self):
        return "maj"

    def get_raw_queryset(self):
        contact = self.request.user.agent.structure.contact_set.get()
        return (
            Evenement.objects.all()
            .get_user_can_view(self.request.user)
            .with_list_of_lieux_with_commune()
            .with_fin_de_suivi(contact)
            .with_nb_fiches_detection()
            .optimized_for_list()
            .with_date_derniere_mise_a_jour()
        )

    def get_queryset(self):
        queryset = self.apply_ordering(self.get_raw_queryset())
        self.filter = EvenementFilter(self.request.GET, queryset=queryset)
        return self.filter.qs
