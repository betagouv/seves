from playwright.sync_api import Page

from core.mixins import WithEtatMixin
from core.models import LienLibre
from ssa.factories import EvenementProduitFactory
from tiac.factories import EvenementSimpleFactory, EtablissementFactory, InvestigationTiacFactory
from .pages import EvenementSimpleEditFormPage
from ..models import EvenementSimple

FIELD_TO_EXCLUDE_ETABLISSEMENT = [
    "_prefetched_objects_cache",
    "_state",
    "id",
    "code_insee",
    "evenement_simple_id",
    "siret",
]


def test_can_modify_evenement_simple(
    live_server, mocked_authentification_user, page: Page, faker, ensure_departements, assert_models_are_equal
):
    departement, *_ = ensure_departements("Paris")
    evenement: EvenementSimple = EvenementSimpleFactory(with_etablissements=3)
    LienLibre.objects.create(
        related_object_1=evenement, related_object_2=InvestigationTiacFactory(etat=WithEtatMixin.Etat.EN_COURS)
    )
    LienLibre.objects.create(
        related_object_1=evenement, related_object_2=EvenementProduitFactory(etat=WithEtatMixin.Etat.EN_COURS)
    )

    creation_page = EvenementSimpleEditFormPage(page, live_server.url, evenement)
    creation_page.navigate()
    creation_page.delete_etablissement(2)
    creation_page.delete_evenement_lie(-1)

    previous_evenements_lies = list(LienLibre.objects.for_object(evenement).all())
    previous_etablissements = list(evenement.etablissements.order_by("pk").all())
    previous_contenu = evenement.contenu
    new_contenu = faker.paragraph()
    new_etablissement = EtablissementFactory.build(departement=departement)

    evenement.contenu = new_contenu
    creation_page.fill_required_fields(evenement)
    creation_page.add_etablissement(new_etablissement)

    creation_page.submit_as_draft()
    evenement.refresh_from_db()

    assert evenement.contenu != previous_contenu
    assert evenement.contenu == new_contenu
    assert list(LienLibre.objects.for_object(evenement).all()) == previous_evenements_lies[:-1]

    [actual_first, actual_second, actual_third] = evenement.etablissements.order_by("pk").all()
    [expected_first, expected_second, expected_third] = [*previous_etablissements[:-1], new_etablissement]

    assert_models_are_equal(actual_first, expected_first, to_exclude=("_state", "id"))
    assert_models_are_equal(actual_second, expected_second, to_exclude=("_state", "id"))
    assert_models_are_equal(
        actual_third,
        expected_third,
        to_exclude=("_state", "id", "evenement_simple_id", "departement_id", "code_insee", "siret"),
    )
