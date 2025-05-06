from django.core.exceptions import ValidationError
from collections import defaultdict

from sv.forms import (
    PrelevementForm,
)
from .constants import KNOWN_OEPPS, KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES
from .models import (
    Prelevement,
    OrganismeNuisible,
    StatutReglementaire,
    Laboratoire,
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
                prelevement_form.save()
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


class WithClotureContextMixin:
    """
    Mixin qui ajoute au contexte les informations relatives à la clôture d'un événement.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        evenement = self.get_object()
        user = self.request.user
        context["contacts_not_in_fin_suivi"] = contacts_structures_not_in_fin_suivi = (
            evenement.get_contacts_structures_not_in_fin_suivi()
        )
        context["is_evenement_can_be_cloturer"], _ = evenement.can_be_cloturer(user)
        context["is_the_only_remaining_structure"] = evenement.is_the_only_remaining_structure(
            user, contacts_structures_not_in_fin_suivi
        )
        return context
