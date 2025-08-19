import pytest
from playwright.sync_api import expect


@pytest.fixture
def assert_etablissement_card_is_correct():
    def _assert_etablissement_card_is_correct(locator, expected_values):
        expect(locator.get_by_text(expected_values.raison_sociale, exact=True)).to_be_visible()
        expect(locator.get_by_text(f"Siret : {expected_values.siret}")).to_be_visible()
        expect(locator.get_by_text(expected_values.type_etablissement, exact=True)).to_be_visible()
        expect(locator.get_by_text(f"{expected_values.departement.nom}")).to_be_visible()
        expect(locator.get_by_text(expected_values.commune)).to_be_visible()

    return _assert_etablissement_card_is_correct
