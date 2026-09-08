import pytest

from sa.models import Espece
from sa.tests.factories import EspeceFactory, MaladieFactory


def _labels(group):
    return [item.label for item in group.choices]


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_with_especes_concernees():
    bovin = EspeceFactory(name="Bovin (Bos taurus)")
    ovin = EspeceFactory(name="Ovin (Ovis aries)")
    autre = EspeceFactory(name="Zébu")
    maladie = MaladieFactory(especes_concernees=[bovin, ovin])

    frequent, other = Espece.treeselect_choices_for_maladie(maladie)

    assert _labels(frequent) == ["Bovin (Bos taurus)", "Ovin (Ovis aries)"]
    assert autre.name in _labels(other)
    assert not set(_labels(frequent)) & set(_labels(other))


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_falls_back_to_default_list_when_no_especes_concernees():
    highlighted = EspeceFactory(name="Chien (Canis lupus familiaris)", is_highlighted=True)
    other_highlighted = EspeceFactory(name="Chat domestique (Felis catus)", is_highlighted=True)
    non_highlighted = EspeceFactory(name="Zébu", is_highlighted=False)
    maladie = MaladieFactory()

    frequent, other = Espece.treeselect_choices_for_maladie(maladie)

    frequent_labels = _labels(frequent)
    assert {highlighted.name, other_highlighted.name}.issubset(frequent_labels)
    assert frequent_labels.index(other_highlighted.name) < frequent_labels.index(highlighted.name)
    assert non_highlighted.name in _labels(other)
    assert non_highlighted.name not in frequent_labels


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_none_uses_default_list():
    highlighted = EspeceFactory(name="Porc (Sus scrofa domesticus)", is_highlighted=True)
    non_highlighted = EspeceFactory(name="Zébu", is_highlighted=False)

    frequent, other = Espece.treeselect_choices_for_maladie(None)

    frequent_labels = _labels(frequent)
    assert highlighted.name in frequent_labels
    assert non_highlighted.name in _labels(other)
    assert non_highlighted.name not in frequent_labels
    assert len(frequent_labels) == Espece.objects.filter(is_highlighted=True).count()


@pytest.mark.django_db
def test_treeselect_choices_for_maladie_no_duplicates_and_no_missing_especes():
    bovin = EspeceFactory(name="Bovin (Bos taurus)")
    EspeceFactory(name="Zébu")
    maladie = MaladieFactory(especes_concernees=[bovin])

    frequent, other = Espece.treeselect_choices_for_maladie(maladie)

    frequent_labels = _labels(frequent)
    other_labels = _labels(other)
    assert not set(frequent_labels) & set(other_labels)
    assert len(frequent_labels) + len(other_labels) == Espece.objects.count()
