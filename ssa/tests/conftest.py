import pytest
from playwright.sync_api import expect

from core.models import Region, Departement
from core.constants import DEPARTEMENTS


DEPARTEMENTS_BY_NAME = {it[1]: it for it in DEPARTEMENTS}


@pytest.fixture
def ensure_departements(db):
    def _ensure_departements(*dpt_names):
        departements = []
        for dpt_name in dpt_names:
            numero, nom, region_name = DEPARTEMENTS_BY_NAME[dpt_name]
            region, _ = Region.objects.get_or_create(nom=region_name)
            dpt, _ = Departement.objects.get_or_create(numero=numero, defaults={"region": region, "nom": nom})
            departements.append(dpt)

        return departements

    return _ensure_departements


@pytest.fixture
def assert_models_are_equal():
    def _assert_models_are_equal(obj_1, obj_2, to_exclude=None):
        if not to_exclude:
            to_exclude = []

        obj_1_data = {k: v for k, v in obj_1.__dict__.items() if k not in to_exclude}
        obj_2_data = {k: v for k, v in obj_2.__dict__.items() if k not in to_exclude}
        assert obj_1_data == obj_2_data

    return _assert_models_are_equal


@pytest.fixture
def assert_etablissement_card_is_correct():
    def _assert_etablissement_card_is_correct(locator, expected_values):
        expect(locator.get_by_text(expected_values.raison_sociale, exact=True)).to_be_visible()
        expect(locator.get_by_text(expected_values.pays.name, exact=True)).to_be_visible()
        expect(locator.get_by_text(expected_values.get_type_exploitant_display(), exact=True)).to_be_visible()
        expect(locator.get_by_text(f"{expected_values.departement.get_num_name_display()}")).to_be_visible()
        expect(locator.get_by_text(expected_values.get_position_dossier_display(), exact=True)).to_be_visible()

    return _assert_etablissement_card_is_correct
