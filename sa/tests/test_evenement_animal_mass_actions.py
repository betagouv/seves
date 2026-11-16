from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import Page, expect

from core.models import FinSuiviContact
from sa.models import EvenementAnimal
from sa.tests.factories import EvenementAnimalFactory
from sa.tests.pages import EvenementListPage


def _evenement_en_cours(user, *, with_fin_de_suivi=False):
    evenement = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)
    contact = user.agent.structure.contact_set.get()
    evenement.contacts.add(contact)
    if with_fin_de_suivi:
        FinSuiviContact.objects.create(
            contact=contact,
            object_id=evenement.id,
            content_type=ContentType.objects.get_for_model(evenement),
        )
    return evenement


def test_master_checkbox_checks_all_rows(live_server, page: Page, mocked_authentification_user):
    evenements = [_evenement_en_cours(mocked_authentification_user) for _ in range(3)]

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()

    for evenement in evenements:
        expect(list_page.checkbox_for(evenement)).not_to_be_checked()

    list_page.select_all()
    for evenement in evenements:
        expect(list_page.checkbox_for(evenement)).to_be_checked()

    list_page.unselect_all()
    for evenement in evenements:
        expect(list_page.checkbox_for(evenement)).not_to_be_checked()


def test_mass_actions_button_is_disabled_until_a_checkbox_is_checked(
    live_server, page: Page, mocked_authentification_user
):
    evenement = _evenement_en_cours(mocked_authentification_user)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()

    expect(list_page.mass_actions_button).to_be_disabled()

    list_page.select(evenement)
    expect(list_page.mass_actions_button).to_be_enabled()

    list_page.checkbox_for(evenement).uncheck(force=True)
    expect(list_page.mass_actions_button).to_be_disabled()


def test_mass_fin_de_suivi_when_all_evenements_are_ok(live_server, page: Page, mocked_authentification_user):
    evenements = [_evenement_en_cours(mocked_authentification_user) for _ in range(3)]

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_fin_de_suivi_modal()

    expect(list_page.fin_de_suivi_modal_content).to_contain_text(
        "Vous êtes sur le point de signaler la fin de suivi de 3 événements."
    )
    expect(list_page.fin_de_suivi_submit_button).to_be_visible()
    list_page.confirm_fin_de_suivi()

    expect(page.get_by_text("Fin(s) de suivi réalisée(s) avec succès.")).to_be_visible()
    assert FinSuiviContact.objects.count() == 3
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    for evenement in evenements:
        assert FinSuiviContact.objects.filter(
            contact=contact,
            object_id=evenement.id,
            content_type=ContentType.objects.get_for_model(evenement),
        ).exists()


def test_mass_fin_de_suivi_when_no_evenement_is_ok(live_server, page: Page, mocked_authentification_user):
    for _ in range(3):
        _evenement_en_cours(mocked_authentification_user, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_fin_de_suivi_modal()

    expect(list_page.fin_de_suivi_modal_content).to_contain_text("Action impossible")
    expect(list_page.fin_de_suivi_submit_button).to_be_hidden()
    expect(list_page.fin_de_suivi_close_button).to_be_visible()

    assert FinSuiviContact.objects.count() == 3


def test_mass_fin_de_suivi_when_only_some_evenements_are_ok(live_server, page: Page, mocked_authentification_user):
    eligibles = [_evenement_en_cours(mocked_authentification_user) for _ in range(2)]
    for _ in range(3):
        _evenement_en_cours(mocked_authentification_user, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_fin_de_suivi_modal()

    expect(list_page.fin_de_suivi_modal_content).to_contain_text(
        "2 événements sur 5 peuvent faire l'objet de cette action."
    )
    expect(list_page.fin_de_suivi_submit_button).to_be_visible()

    list_page.confirm_fin_de_suivi()

    expect(page.get_by_text("Fin(s) de suivi réalisée(s) avec succès.")).to_be_visible()
    assert FinSuiviContact.objects.count() == 5
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    for evenement in eligibles:
        assert FinSuiviContact.objects.filter(
            contact=contact,
            object_id=evenement.id,
            content_type=ContentType.objects.get_for_model(evenement),
        ).exists()
