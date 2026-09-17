from django.core.exceptions import ValidationError
import pytest

from sa.models import Espece
from sa.referentiels import situation_unite
from sa.tests.factories import EspeceConcerneeFactory


@pytest.mark.django_db
def test_tree_is_not_empty():
    assert len(situation_unite.build_tree()) > 0


@pytest.mark.django_db
def test_every_species_in_tree_exists_in_database():
    missing = [name for name in situation_unite.build_tree() if not Espece.objects.filter(name=name).exists()]
    assert missing == []


@pytest.mark.django_db
def test_bovin_valid_combination():
    assert situation_unite.is_valid_combination(
        "Bovin (Bos taurus)", "Élevage", "Bâtiment ouvert (en partie)", "Atelier laitier"
    )


@pytest.mark.django_db
def test_bovin_partial_combination_is_invalid():
    assert not situation_unite.is_valid_combination("Bovin (Bos taurus)", "Élevage", "Bâtiment ouvert (en partie)")
    assert not situation_unite.is_valid_combination("Bovin (Bos taurus)", "Élevage")


@pytest.mark.django_db
def test_bovin_leaf_without_children_is_valid():
    assert situation_unite.is_valid_combination("Bovin (Bos taurus)", "Abattoir")


@pytest.mark.django_db
def test_sanglier_four_level_combination():
    assert situation_unite.is_valid_combination(
        "Sanglier (Sus scrofa)",
        "Élevage",
        "Bâtiment ouvert (en partie)",
        "Production",
        "Sanglier cat. A (repeuplement)",
    )
    assert not situation_unite.is_valid_combination(
        "Sanglier (Sus scrofa)",
        "Élevage",
        "Bâtiment ouvert (en partie)",
        "Production",
        "Naisseur",
    )


@pytest.mark.django_db
def test_species_absent_from_tableur_is_invalid():
    assert not situation_unite.is_valid_combination("NotASpecies", "Abattoir")


@pytest.mark.django_db
def test_build_tree_json_for_especes_only_includes_tableur_species():
    Espece.objects.get_or_create(name="Bovin (Bos taurus)")
    other = Espece.objects.create(name="Espèce hors tableur pour ce test")

    tree_json = situation_unite.build_tree_json_for_especes()

    bovin = Espece.objects.get(name="Bovin (Bos taurus)")
    assert str(bovin.pk) in tree_json
    assert str(other.pk) not in tree_json


@pytest.mark.django_db
def test_saving_an_invalid_combination_outside_the_form_is_rejected():
    espece, _ = Espece.objects.get_or_create(name="Bovin (Bos taurus)")
    espece_concernee = EspeceConcerneeFactory.build(espece=espece, type_lieu="Élevage")

    with pytest.raises(ValidationError):
        espece_concernee.save()


@pytest.mark.django_db
def test_saving_a_valid_combination_outside_the_form_succeeds():
    espece, _ = Espece.objects.get_or_create(name="Bovin (Bos taurus)")
    espece_concernee = EspeceConcerneeFactory.create(
        espece=espece,
        type_lieu="Élevage",
        mode_elevage="Bâtiment ouvert (en partie)",
        type_production="Atelier laitier",
    )

    espece_concernee.refresh_from_db()
    assert espece_concernee.type_production == "Atelier laitier"
