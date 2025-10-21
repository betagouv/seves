import itertools

import pytest
from django.db import IntegrityError

from ssa.models import CategorieDanger
from tiac.constants import SuspicionConclusion, DangersSyndromiques
from tiac.factories import InvestigationTiacFactory

test_data = [
    *itertools.product([SuspicionConclusion.CONFIRMED], [*DangersSyndromiques.values, ""]),
    *itertools.product([SuspicionConclusion.SUSPECTED], [*CategorieDanger.values, ""]),
    *itertools.product([*SuspicionConclusion.no_clue, ""], [*DangersSyndromiques.values, *CategorieDanger.values]),
]


@pytest.mark.parametrize("suspicion_conclusion,selected_hazard", test_data)
def test_investigation_tiac_selected_hazard_constraints(db, suspicion_conclusion, selected_hazard):
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(suspicion_conclusion=suspicion_conclusion, selected_hazard=[selected_hazard])

    InvestigationTiacFactory(
        suspicion_conclusion=SuspicionConclusion.CONFIRMED, selected_hazard=[CategorieDanger.VIBRIO]
    )
    InvestigationTiacFactory(
        suspicion_conclusion=SuspicionConclusion.SUSPECTED, selected_hazard=[DangersSyndromiques.AUTRE]
    )
    InvestigationTiacFactory(suspicion_conclusion=SuspicionConclusion.UNKNOWN, selected_hazard=[])
