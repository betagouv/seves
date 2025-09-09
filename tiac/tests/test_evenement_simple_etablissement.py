import re

from playwright.sync_api import Page

from tiac.factories import EvenementSimpleFactory, EtablissementFactory
from .pages import EvenementSimpleFormPage
from ..models import Etablissement, EvenementSimple

FIELD_TO_EXCLUDE_ETABLISSEMENT = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "code_insee",
    "evenement_simple_id",
    "siret",
]


def test_can_add_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    evenement = EvenementSimpleFactory()

    etablissement_1, etablissement_2 = EtablissementFactory.build_batch(
        2, evenement_simple=evenement, departement=departement
    )

    creation_page = EvenementSimpleFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)
    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 2
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_etablissement_card(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    evenement = EvenementSimpleFactory()

    etablissement: Etablissement = EtablissementFactory.build(evenement_simple=evenement, departement=departement)

    creation_page = EvenementSimpleFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement)

    content = [it for it in re.split(r"\s*\n\s*", creation_page.get_etablissement_card(0).text_content()) if it]

    assert content == [
        etablissement.raison_sociale,
        f"{etablissement.departement} | {etablissement.commune}",
        etablissement.type_etablissement,
        f"Voir les informations de l'établissement {etablissement.raison_sociale}",
        f"Modifier l'établissement {etablissement.raison_sociale}",
        f"Supprimer l'établissement {etablissement.raison_sociale}",
    ]

    # Check that modifying the form modifies the card
    raison_sociale = "Ascaponts"
    creation_page.edit_etablissement(0, raison_sociale=raison_sociale)

    content = [it for it in re.split(r"\s*\n\s*", creation_page.get_etablissement_card(0).text_content()) if it]

    assert content == [
        raison_sociale,
        f"{etablissement.departement} | {etablissement.commune}",
        etablissement.type_etablissement,
        f"Voir les informations de l'établissement {raison_sociale}",
        f"Modifier l'établissement {raison_sociale}",
        f"Supprimer l'établissement {raison_sociale}",
    ]


def test_can_delete_etablissements(live_server, page: Page, ensure_departements, assert_models_are_equal):
    departement, *_ = ensure_departements("Paris")
    evenement = EvenementSimpleFactory()

    etablissement_1, etablissement_2 = EtablissementFactory.build_batch(
        2, evenement_simple=evenement, departement=departement
    )

    creation_page = EvenementSimpleFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement_1)
    creation_page.add_etablissement(etablissement_2)

    creation_page.get_etablissement_card(1).locator(".delete-button").click()

    modal = creation_page.page.locator(".delete-modal").locator("visible=true")
    modal.locator(".delete-confirmation").click()
    modal.wait_for(state="hidden")
    assert 1 == page.locator(".modal-etablissement-container .etablissement-card").locator("visible=true").count()

    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 1
    etablissements = Etablissement.objects.all()

    assert_models_are_equal(etablissements[0], etablissement_1, to_exclude=FIELD_TO_EXCLUDE_ETABLISSEMENT)


def test_show_etablissement_detail(live_server, page: Page, ensure_departements):
    departement, *_ = ensure_departements("Paris")
    evenement: EvenementSimple = EvenementSimpleFactory()

    etablissement: Etablissement = EtablissementFactory.build(evenement_simple=evenement, departement=departement)

    creation_page = EvenementSimpleFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement)

    assert creation_page.get_detail_modal_content(0) == [
        etablissement.raison_sociale,
        "Type d'établissement",
        etablissement.type_etablissement,
        "SIRET",
        "Enseigne usuelle",
        etablissement.raison_sociale,
        "Adresse",
        etablissement.adresse_lieu_dit,
        "Commune",
        etablissement.commune,
        "Departement",
        str(etablissement.departement),
        "Numéro Résytal",
        *([etablissement.numero_resytal] if etablissement.numero_resytal else []),
        "Évaluation globale",
        *([etablissement.get_evaluation_display()] if etablissement.evaluation else []),
        "Commentaire",
        *([etablissement.commentaire] if etablissement.commentaire else []),
    ]

    # Check that the detail modal gets updated
    raison_sociale = "Ascaponts"
    creation_page.edit_etablissement(0, raison_sociale=raison_sociale)

    assert creation_page.get_detail_modal_content(0) == [
        raison_sociale,
        "Type d'établissement",
        etablissement.type_etablissement,
        "SIRET",
        "Enseigne usuelle",
        raison_sociale,
        "Adresse",
        etablissement.adresse_lieu_dit,
        "Commune",
        etablissement.commune,
        "Departement",
        str(etablissement.departement),
        "Numéro Résytal",
        *([etablissement.numero_resytal] if etablissement.numero_resytal else []),
        "Évaluation globale",
        *([etablissement.get_evaluation_display()] if etablissement.evaluation else []),
        "Commentaire",
        *([etablissement.commentaire] if etablissement.commentaire else []),
    ]


def test_cancel_add_etablissement(live_server, page: Page, ensure_departements):
    departement, *_ = ensure_departements("Paris")
    evenement: EvenementSimple = EvenementSimpleFactory()

    etablissement: Etablissement = EtablissementFactory.build(evenement_simple=evenement, departement=departement)

    # Create a first etablissment
    creation_page = EvenementSimpleFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(etablissement)

    # Open the modal to create a new etablissement but cancel before saving
    modal = creation_page.open_etablissement_modal()
    modal.get_by_role("button", name="Annuler").click()
    modal.wait_for(state="hidden")
    assert not page.locator(".modal-etablissement-container").all()[1].is_visible()

    # Check that empty forms aren't saved
    creation_page.submit_as_draft()

    assert Etablissement.objects.count() == 1
