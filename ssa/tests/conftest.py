import pytest
from playwright.sync_api import expect


@pytest.fixture
def assert_etablissement_card_is_correct():
    def _assert_etablissement_card_is_correct(locator, expected_values):
        expect(locator.get_by_text(expected_values.raison_sociale, exact=True)).to_be_visible()
        expect(locator.get_by_text(expected_values.pays.name, exact=True)).to_be_visible()
        expect(locator.get_by_text(expected_values.type_exploitant, exact=True)).to_be_visible()
        expect(locator.get_by_text(f"{expected_values.departement}")).to_be_visible()
        expect(locator.get_by_text(expected_values.get_position_dossier_display(), exact=True)).to_be_visible()

    return _assert_etablissement_card_is_correct
