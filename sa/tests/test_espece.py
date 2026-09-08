import pytest

from sa.models import Espece
from sa.tests.factories import EspeceFactory, MaladieFactory


def _labels(group):
    return [item.label for item in group.choices]


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_splits_especes_concernees_by_is_highlighted():
    bovin = EspeceFactory(name="Bovin de test", is_highlighted=True)
    ovin = EspeceFactory(name="Ovin de test", is_highlighted=True)
    porc = EspeceFactory(name="Porc de test", is_highlighted=False)
    non_concernee = EspeceFactory(name="Zébu de test", is_highlighted=True)
    maladie = MaladieFactory(especes_concernees=[bovin, ovin, porc])

    frequent, other = Espece.treeselect_choices_for_maladie(maladie)

    assert _labels(frequent) == ["Bovin de test", "Ovin de test"]
    assert _labels(other) == ["Porc de test"]
    # An espèce not concerned by this maladie must not appear at all, even when highlighted.
    assert non_concernee.name not in _labels(frequent)
    assert non_concernee.name not in _labels(other)


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_falls_back_to_default_list_when_no_especes_concernees():
    highlighted = EspeceFactory(name="Chien de test", is_highlighted=True)
    other_highlighted = EspeceFactory(name="Chat de test", is_highlighted=True)
    non_highlighted = EspeceFactory(name="Zébu de test", is_highlighted=False)
    maladie = MaladieFactory(name="Maladie de test sans espèce concernée")

    frequent, other = Espece.treeselect_choices_for_maladie(maladie)

    frequent_labels = _labels(frequent)
    assert {highlighted.name, other_highlighted.name}.issubset(frequent_labels)
    assert frequent_labels.index(other_highlighted.name) < frequent_labels.index(highlighted.name)
    assert _labels(other) == []
    assert non_highlighted.name not in frequent_labels


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_none_is_empty():
    highlighted = EspeceFactory(name="Porc de test", is_highlighted=True)

    frequent, other = Espece.treeselect_choices_for_maladie(None)

    assert _labels(frequent) == []
    assert _labels(other) == []
    assert highlighted.name not in _labels(frequent)


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_no_duplicates():
    bovin = EspeceFactory(name="Bovin de test", is_highlighted=True)
    ovin = EspeceFactory(name="Ovin de test", is_highlighted=False)
    EspeceFactory(name="Zébu de test")
    maladie = MaladieFactory(especes_concernees=[bovin, ovin])

    frequent, other = Espece.treeselect_choices_for_maladie(maladie)

    frequent_labels = _labels(frequent)
    other_labels = _labels(other)
    assert not set(frequent_labels) & set(other_labels)
    assert len(frequent_labels) + len(other_labels) == 2
