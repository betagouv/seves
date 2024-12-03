from django.core.exceptions import ValidationError

from sv.forms import (
    PrelevementForm,
)
from .constants import KNOWN_OEPPS, KNOWN_OEPP_CODES_FOR_STATUS_REGLEMENTAIRES
from .models import (
    Prelevement,
    OrganismeNuisible,
    StatutReglementaire,
)


class FicheDetectionContextMixin:
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
        # TODO clean this mess
        # TODO review this to "filter" data for each prelvements
        prelevement_ids = [key.removeprefix("prelevements-") for key in data.keys() if key.startswith("prelevements-")]
        prelevement_ids = set([id.split("-")[0] for id in prelevement_ids])
        for i in prelevement_ids:
            prefix = f"prelevements-{i}-"
            form_data = {key: value for key, value in data.items() if key.startswith(prefix)}
            form_is_empty = not any(form_data.values())
            if form_is_empty:
                continue

            print(form_data)
            prelevement_id = form_data.pop(prefix + "id", None)
            form_is_empty = not any(form_data.values())

            if prelevement_id:
                prelevement = Prelevement.objects.get(id=prelevement_id)
                if form_is_empty:
                    prelevement.delete()
                    return
                else:
                    prelevement_form = PrelevementForm(form_data, instance=prelevement, prefix=f"prelevements-{i}")
            else:
                prelevement_form = PrelevementForm(form_data, prefix=f"prelevements-{i}")

            prelevement_form.fields["lieu"].queryset = allowed_lieux

            if prelevement_form.is_valid():
                prelevement_form.save()
            else:
                raise ValidationError(prelevement_form.errors)
