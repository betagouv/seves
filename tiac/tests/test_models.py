import random
import threading
import time

from django.db import IntegrityError, connection, transaction
import pytest

from ssa.constants import CategorieDanger
from tiac.constants import DangersSyndromiques, SuspicionConclusion
from tiac.factories import (
    AlimentSuspectFactory,
    EvenementSimpleFactory,
    InvestigationTiacFactory,
    RepasSuspectFactory,
)
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
            suspicion_conclusion=SuspicionConclusion.DISCARDED, conclusion_repas=RepasSuspectFactory()
        )
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(
            suspicion_conclusion=SuspicionConclusion.DISCARDED, conclusion_repas=AlimentSuspectFactory()
        )


def test_investigation_tiac_etiogie_constraints(db):
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(analyses_sur_les_malades=Analyses.NON, precisions="Test")
    with pytest.raises(IntegrityError):
        InvestigationTiacFactory(analyses_sur_les_malades=Analyses.INCONNU, precisions="Test")


@pytest.mark.parametrize("factory", [EvenementSimpleFactory, InvestigationTiacFactory])
def test_numero_is_unique(db, factory):
    evenement = factory()
    with pytest.raises(IntegrityError):
        factory(numero_annee=evenement.numero_annee, numero_evenement=evenement.numero_evenement)


@pytest.mark.django_db(transaction=True)
def test_concurrent_creations_get_different_numeros():
    first_saved, commit_first = threading.Event(), threading.Event()
    evenements = []

    def create_first():
        try:
            with transaction.atomic():
                evenements.append(EvenementSimpleFactory(numero_annee=None, numero_evenement=None))
                first_saved.set()
                commit_first.wait(timeout=10)
        finally:
            connection.close()

    def create_second():
        try:
            evenements.append(InvestigationTiacFactory(numero_annee=None, numero_evenement=None))
        finally:
            connection.close()

    first_thread = threading.Thread(target=create_first)
    first_thread.start()
    first_saved.wait(timeout=10)

    second_thread = threading.Thread(target=create_second)
    second_thread.start()

    try:
        # The first creation is not committed yet: the second one must wait for the lock
        for _ in range(100):
            with connection.cursor() as cursor:
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_locks WHERE locktype = 'advisory' AND NOT granted)")
                if cursor.fetchone()[0]:
                    break
            time.sleep(0.05)
        else:
            pytest.fail("La seconde création n'a pas attendu la fin de la première")
    finally:
        commit_first.set()
        first_thread.join()
        second_thread.join()

    first, second = evenements
    assert (second.numero_annee, second.numero_evenement) == (first.numero_annee, first.numero_evenement + 1)
