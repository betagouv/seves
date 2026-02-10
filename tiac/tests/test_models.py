import random

from django.db import IntegrityError
import pytest

from ssa.constants import CategorieDanger
from tiac.constants import DangersSyndromiques, SuspicionConclusion
from tiac.factories import AlimentSuspectFactory, InvestigationTiacFactory, RepasSuspectFactory
from tiac.models import Analyses


def test_investigation_tiac_selected_hazard_constraints(db):
    def choices(choice_enum):
        return random.choices(choice_enum.values, k=random.randint(2, len(choice_enum)))

    for suspicion_conclusion, selected_hazard in (
        (SuspicionConclusion.CONFIRMED, choices(DangersSyndromiques)),
        (SuspicionConclusion.CONFIRMED, []),
        (SuspicionConclusion.SUSPECTED, choices(CategorieDanger)),
        (SuspicionConclusion.SUSPECTED, []),
        (random.choice(SuspicionConclusion.no_clue), choices(DangersSyndromiques)),
        (random.choice(SuspicionConclusion.no_clue), choices(CategorieDanger)),
        ("", choices(DangersSyndromiques)),
        ("", choices(CategorieDanger)),
    ):
        with pytest.raises(IntegrityError):
            InvestigationTiacFactory(suspicion_conclusion=suspicion_conclusion, selected_hazard=selected_hazard)
            pytest.fail(
                f"InvestigationTiac did not raise IntegrityError for parameters: {suspicion_conclusion=}, {selected_hazard=}"
            )

    # Test I can create InvestigationTiacFactory with multiple selected_hazard values
    for suspicion_conclusion, selected_hazard in (
        (SuspicionConclusion.CONFIRMED, choices(CategorieDanger)),
        (SuspicionConclusion.SUSPECTED, choices(DangersSyndromiques)),
        (random.choice(SuspicionConclusion.no_clue), []),
    ):
        try:
            InvestigationTiacFactory(suspicion_conclusion=suspicion_conclusion, selected_hazard=selected_hazard)
        except IntegrityError:
            pytest.fail(
                f"InvestigationTiac raised exception for parameters: {suspicion_conclusion=}, {selected_hazard=}"
            )


def test_investigation_tiac_conclusion_constraints(db):
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(
            suspicion_conclusion=SuspicionConclusion.UNKNOWN, conclusion_repas=RepasSuspectFactory()
        )
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(
            suspicion_conclusion=SuspicionConclusion.UNKNOWN, conclusion_repas=AlimentSuspectFactory()
        )


def test_investigation_tiac_etiogie_constraints(db):
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(analyses_sur_les_malades=Analyses.NON, precisions="Test")
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(analyses_sur_les_malades=Analyses.INCONNU, precisions="Test")
