import re

from playwright.sync_api import Page
import pytest

from tiac.factories import EtablissementFactory, InvestigationTiacFactory

from ..models import Etablissement, InvestigationTiac
from .pages import InvestigationTiacFormPage

FIELD_TO_EXCLUDE_ETABLISSEMENT = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "code_insee",
    "evenement_simple_id",
    "investigation_id",
    "siret",
]
pytestmark = pytest.mark.usefixtures("mus_contact")


def test_form_validation(live_server, page: Page, ensure_departements):
    departement, *_ = ensure_departements("Paris")
    investigation: InvestigationTiac = InvestigationTiacFactory.build()
    etablissement: Etablissement = EtablissementFactory.build(investigation=investigation, departement=departement)

    creation_page = InvestigationTiacFormPage(page, live_server.url)

    etablissement_count = Etablissement.objects.count()

    creation_page.navigate()
    creation_page.fill_required_fields(investigation)
    creation_page.open_etablissement_modal()
    creation_page.current_modal.locator(".save-btn").click()

    # Check form validity is correctly reported
    assert creation_page.current_modal.locator("[required]:invalid").count() > 0

    # Check Resytal number format is correctly checked
    creation_page.fill_etablissement(creation_page.current_modal, etablissement)
    creation_page.current_modal.locator('label[for$="has_inspection"]').click()
    creation_page.current_modal.locator('[id$="numero_resytal"]').fill("zz")
    creation_page.current_modal.locator(".save-btn").click()

    assert "Le numéro Resytal doit être au format AA-XXXXXX ; par exemple : 19-067409" == page.evaluate(
        # language=javascript
        """() => document.querySelector('[id$="numero_resytal"]').validationMessage"""
    )

    creation_page.current_modal.locator('[id$="numero_resytal"]').fill("25-000000")
    creation_page.current_modal.locator(".save-btn").click()
    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == etablissement_count + 1


def test_can_add_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    investigation: InvestigationTiac = InvestigationTiacFactory.build()

    etablissement_1, etablissement_2 = EtablissementFactory.build_batch(
        2, investigation=investigation, departement=departement
    )

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(investigation)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)
    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 2
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_etablissement_card(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    investigation: InvestigationTiac = InvestigationTiacFactory.build()

    etablissement: Etablissement = EtablissementFactory.build(investigation=investigation, departement=departement)

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(investigation)
    creation_page.add_etablissement(etablissement)

    content = [it for it in re.split(r"\s*\n\s*", creation_page.get_etablissement_card(0).text_content()) if it]

    assert content == [
        etablissement.raison_sociale,
        f"{etablissement.commune} | {etablissement.departement}",
        etablissement.type_etablissement,
        "Modifier",
        "Supprimer",
    ]

    # Check that modifying the form modifies the card
    raison_sociale = "Ascaponts"
    creation_page.edit_etablissement(0, raison_sociale=raison_sociale)

    content = [it for it in re.split(r"\s*\n\s*", creation_page.get_etablissement_card(0).text_content()) if it]

    assert content == [
        raison_sociale,
        f"{etablissement.commune} | {etablissement.departement}",
        etablissement.type_etablissement,
        "Modifier",
        "Supprimer",
    ]


def test_can_delete_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    investigation: InvestigationTiac = InvestigationTiacFactory.build()

    etablissement_1, etablissement_2 = EtablissementFactory.build_batch(
        2, investigation=investigation, departement=departement
    )

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(investigation)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)
    creation_page.delete_etablissement(1)
    assert 1 == page.locator(".modal-etablissement-container .etablissement-card").locator("visible=true").count()

    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 1
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_cancel_add_etablissement(live_server, page: Page, ensure_departements):
    departement, *_ = ensure_departements("Paris")
    investigation: InvestigationTiac = InvestigationTiacFactory.build()

    etablissement: Etablissement = EtablissementFactory.build(investigation=investigation, departement=departement)

    # Create a first etablissment
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(investigation)
    creation_page.add_etablissement(etablissement)

    # Open the modal to create a new etablissement but cancel before saving
    modal = creation_page.open_etablissement_modal()
    modal.get_by_role("button", name="Annuler").click()
    modal.wait_for(state="hidden")
    assert not page.locator(".modal-etablissement-container").all()[1].is_visible()

    # Check that empty forms aren't saved
    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 1
