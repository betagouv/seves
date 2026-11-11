from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import Page, expect
from reversion.models import Version

from core.models import FinSuiviContact
from sa.models import EvenementAnimal
from sa.tests.factories import EvenementAnimalFactory
from sa.tests.pages import EvenementListPage


def _evenement(user, *, etat=EvenementAnimal.Etat.EN_COURS, with_fin_de_suivi=False):
    evenement = EvenementAnimalFactory(etat=etat)
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
    evenements = [_evenement(mocked_authentification_user) for _ in range(3)]

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
    evenement = _evenement(mocked_authentification_user)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()

    expect(list_page.mass_actions_button).to_be_disabled()

    list_page.select(evenement)
    expect(list_page.mass_actions_button).to_be_enabled()

    list_page.checkbox_for(evenement).uncheck(force=True)
    expect(list_page.mass_actions_button).to_be_disabled()


def test_mass_fin_de_suivi_when_all_evenements_are_ok(live_server, page: Page, mocked_authentification_user):
    evenements = [_evenement(mocked_authentification_user) for _ in range(3)]

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_fin_de_suivi_modal()

    expect(list_page.mass_action_modal_content).to_contain_text(
        "Vous êtes sur le point de signaler la fin de suivi de 3 événements."
    )
    expect(list_page.mass_action_submit_button).to_be_visible()
    list_page.confirm_mass_action()

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
        _evenement(mocked_authentification_user, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_fin_de_suivi_modal()

    expect(list_page.mass_action_modal_content).to_contain_text("Action impossible")
    expect(list_page.mass_action_submit_button).to_be_hidden()
    expect(list_page.mass_action_close_button).to_be_visible()

    assert FinSuiviContact.objects.count() == 3


def test_mass_fin_de_suivi_when_only_some_evenements_are_ok(live_server, page: Page, mocked_authentification_user):
    eligibles = [_evenement(mocked_authentification_user) for _ in range(2)]
    for _ in range(3):
        _evenement(mocked_authentification_user, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_fin_de_suivi_modal()

    expect(list_page.mass_action_modal_content).to_contain_text(
        "2 événements sur 5 peuvent faire l'objet de cette action."
    )
    expect(list_page.mass_action_submit_button).to_be_visible()

    list_page.confirm_mass_action()

    expect(page.get_by_text("Fin(s) de suivi réalisée(s) avec succès.")).to_be_visible()
    assert FinSuiviContact.objects.count() == 5
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    for evenement in eligibles:
        assert FinSuiviContact.objects.filter(
            contact=contact,
            object_id=evenement.id,
            content_type=ContentType.objects.get_for_model(evenement),
        ).exists()


def test_mass_reprise_suivi_when_all_evenements_are_ok(live_server, page: Page, mocked_authentification_user):
    evenements = [_evenement(mocked_authentification_user, with_fin_de_suivi=True) for _ in range(3)]

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_reprise_suivi_modal()

    expect(list_page.mass_action_modal_content).to_contain_text(
        "Vous êtes sur le point de reprendre le suivi de 3 événements. Leur statut redeviendra « En cours »."
    )
    expect(list_page.mass_action_submit_button).to_be_visible()
    list_page.confirm_mass_action()

    expect(page.get_by_text("Suivi repris pour 3 événements.")).to_be_visible()
    assert FinSuiviContact.objects.count() == 0
    expect(page.locator(".evenements__list-row").get_by_text("En cours", exact=True)).to_have_count(3)
    expect(list_page.master_checkbox).not_to_be_checked()
    expect(list_page.mass_actions_button).to_be_disabled()

    structure = mocked_authentification_user.agent.structure
    for evenement in evenements:
        assert (
            Version.objects.get_for_object(evenement)
            .filter(revision__comment=f"La structure {structure} a repris le suivi sur cette fiche")
            .exists()
        )


def test_mass_reprise_suivi_when_no_evenement_is_ok(live_server, page: Page, mocked_authentification_user):
    _evenement(mocked_authentification_user)
    _evenement(mocked_authentification_user, etat=EvenementAnimal.Etat.CLOTURE, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_reprise_suivi_modal()

    expect(list_page.mass_action_modal_content).to_contain_text(
        "Action impossible : aucun des 2 événements sélectionnés n'est éligible."
    )
    expect(list_page.mass_action_submit_button).to_be_hidden()
    expect(list_page.mass_action_close_button).to_be_visible()

    assert FinSuiviContact.objects.count() == 1


def test_mass_reprise_suivi_when_only_some_evenements_are_ok(live_server, page: Page, mocked_authentification_user):
    eligibles = [_evenement(mocked_authentification_user, with_fin_de_suivi=True) for _ in range(2)]
    _evenement(mocked_authentification_user)
    cloture = _evenement(mocked_authentification_user, etat=EvenementAnimal.Etat.CLOTURE, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_reprise_suivi_modal()

    expect(list_page.mass_action_modal_content).to_contain_text(
        "2 événements sur 4 peuvent faire l'objet de cette action. 2 seront ignorés."
    )
    expect(list_page.mass_action_submit_button).to_be_visible()

    list_page.confirm_mass_action()

    expect(page.get_by_text("Suivi repris pour 2 événements.")).to_be_visible()
    assert FinSuiviContact.objects.get().object_id == cloture.id
    for evenement in eligibles:
        assert not evenement.fin_suivi.exists()


def test_mass_reprise_suivi_can_be_cancelled(live_server, page: Page, mocked_authentification_user):
    _evenement(mocked_authentification_user, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_reprise_suivi_modal()
    expect(list_page.mass_action_modal_content).to_contain_text(
        "Vous êtes sur le point de reprendre le suivi de 1 événement. Son statut redeviendra « En cours »."
    )

    list_page.mass_action_cancel_button.click()

    expect(list_page.mass_action_modal).to_be_hidden()
    assert FinSuiviContact.objects.count() == 1


def test_mass_reprise_suivi_messages_are_singular_for_one_evenement(
    live_server, page: Page, mocked_authentification_user
):
    eligible = _evenement(mocked_authentification_user, with_fin_de_suivi=True)
    non_eligible = _evenement(mocked_authentification_user)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select(eligible, non_eligible)
    list_page.open_reprise_suivi_modal()
    expect(list_page.mass_action_modal_content).to_contain_text(
        "1 événement sur 2 peut faire l'objet de cette action. 1 sera ignoré."
    )
    list_page.mass_action_cancel_button.click()
    expect(list_page.mass_action_modal).to_be_hidden()

    list_page.checkbox_for(eligible).uncheck(force=True)
    list_page.open_reprise_suivi_modal()
    expect(list_page.mass_action_modal_content).to_contain_text(
        "Action impossible : l'événement sélectionné n'est pas éligible."
    )
