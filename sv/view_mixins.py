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
    def _save_prelevement_if_not_empty(self, data, allowed_lieux):
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
                prelevement_form = PrelevementForm(form_data, instance=prelevement, prefix=f"prelevements-{form_id}")
            else:
                prelevement_form = PrelevementForm(form_data, prefix=f"prelevements-{form_id}")

            prelevement_form.fields["lieu"].queryset = allowed_lieux

            if prelevement_form.is_valid():
                prelevement_form.save()
            else:
                raise ValidationError(prelevement_form.errors)
