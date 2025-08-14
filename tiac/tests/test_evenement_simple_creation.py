from playwright.sync_api import Page, expect

from core.models import LienLibre
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from tiac.factories import EvenementSimpleFactory
from .pages import EvenementSimpleFormPage
from ..models import EvenementSimple


def test_can_create_evenement_simple_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = EvenementSimpleFactory.build()
    creation_page = EvenementSimpleFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    evenement = EvenementSimple.objects.get()
    assert evenement.createur == mocked_authentification_user.agent.structure
    assert evenement.follow_up == input_data.follow_up
    assert evenement.contenu == input_data.contenu
    assert evenement.numero is not None
    assert evenement.is_draft is True

    expect(creation_page.page.get_by_text("L’évènement a été créé avec succès.")).to_be_visible()
    expect(creation_page.page.get_by_text(input_data.contenu)).to_be_visible()
    expect(creation_page.page.get_by_text(input_data.get_follow_up_display())).to_be_visible()


def test_can_create_evenement_simple_with_all_fields(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal, choice_js_fill
):
    input_data = EvenementSimpleFactory.build()
    other_evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    evenement_produit = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)

    creation_page = EvenementSimpleFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.evenement_origin.select_option(input_data.evenement_origin)
    creation_page.date_reception.fill(input_data.date_reception.strftime("%Y-%m-%d"))
    creation_page.set_modalites_declaration(input_data.modalites_declaration)
    creation_page.set_notify_ars(input_data.notify_ars)
    creation_page.nb_sick_persons.fill(str(input_data.nb_sick_persons))
    creation_page.add_free_link(other_evenement.numero, choice_js_fill)
    creation_page.add_free_link(evenement_produit.numero, choice_js_fill, link_label="Évenement produit : ")
    creation_page.submit_as_draft()

    evenement = EvenementSimple.objects.last()
    assert_models_are_equal(input_data, evenement, to_exclude=["id", "_state", "numero_annee", "date_creation"])
    assert LienLibre.objects.count() == 2
