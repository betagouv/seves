import json

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import Page, expect
from reversion.models import Version

from core.factories import ContactStructureFactory
from core.models import FinSuiviContact
from sa.models import EvenementAnimal
from sa.tests.factories import EvenementAnimalFactory
from sa.tests.pages import EvenementListPage
from sa.views import EvenementListView


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


def _add_contact_structure(evenement, *, with_fin_de_suivi):
    contact = ContactStructureFactory()
    evenement.contacts.add(contact)
    if with_fin_de_suivi:
        FinSuiviContact.objects.create(
            contact=contact,
            object_id=evenement.id,
            content_type=ContentType.objects.get_for_model(evenement),
        )
    return contact


def test_cloture_is_not_available_for_non_ac_user(live_server, page: Page):
    evenement = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select(evenement)
    list_page.open_mass_actions()

    expect(list_page.mass_actions_dropdown.get_by_role("button", name="Signaler la fin de suivi")).to_be_visible()
    expect(list_page.mass_actions_dropdown.get_by_role("button", name="Clôturer")).to_have_count(0)
    expect(list_page.cloture_modal).to_have_count(0)


def test_non_ac_user_cannot_mass_cloturer(client):
    evenement = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)

    response = client.post(
        reverse("sa:mass-action-status"),
        data={"action": "cloture", "pks": [evenement.pk]},
        content_type="application/json",
    )
    assert response.status_code == 403

    client.post(
        reverse("cloturer-mass"),
        data={
            "pks": str(evenement.pk),
            "content_type": ContentType.objects.get_for_model(evenement).pk,
        },
    )
    evenement.refresh_from_db()
    assert evenement.etat == EvenementAnimal.Etat.EN_COURS


def test_mass_cloture_when_all_structures_are_in_fin_de_suivi(live_server, page: Page, ac_user, mailoutbox):
    evenements = [EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS) for _ in range(3)]
    for evenement in evenements:
        _add_contact_structure(evenement, with_fin_de_suivi=True)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    expect(list_page.selection_count).to_have_text("3 événements sélectionnés")
    list_page.open_cloture_modal()

    expect(list_page.cloture_modal_content).to_have_text(
        "Vous êtes sur le point de clôturer 3 événements. Confirmez-vous cette action ?"
    )
    list_page.confirm_cloture()

    expect(page.get_by_text("3 événements ont été clôturés avec succès.")).to_be_visible()
    for evenement in evenements:
        evenement.refresh_from_db()
        assert evenement.etat == EvenementAnimal.Etat.CLOTURE
        last_version = Version.objects.get_for_object(evenement).first()
        assert json.loads(last_version.serialized_data)[0]["fields"]["etat"] == EvenementAnimal.Etat.CLOTURE
    expect(page.locator(".evenements__list-row").get_by_text("Clôturé", exact=True)).to_have_count(3)
    for evenement in evenements:
        expect(list_page.checkbox_for(evenement)).not_to_be_checked()
    expect(list_page.selection_count).to_be_empty()
    expect(list_page.mass_actions_button).to_be_disabled()
    # Structures in fin de suivi are not notified
    assert len(mailoutbox) == 0


def test_mass_cloture_warns_when_structures_have_not_signaled_fin_de_suivi(
    live_server, page: Page, ac_user, mus_contact, mailoutbox
):
    with_structure_still_following = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)
    contact_still_following = _add_contact_structure(with_structure_still_following, with_fin_de_suivi=False)
    contact_in_fin_de_suivi = _add_contact_structure(with_structure_still_following, with_fin_de_suivi=True)
    with_fin_de_suivi = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)
    _add_contact_structure(with_fin_de_suivi, with_fin_de_suivi=True)
    # As for a single cloture, the structure of the user is not taken into account: its fin de suivi is added
    with_only_user_structure = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)
    with_only_user_structure.contacts.add(mus_contact)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_cloture_modal()

    expect(list_page.cloture_modal_content).to_contain_text(
        "Attention, pour 1 des 3 événements sélectionnés, une ou plusieurs structures concernées "
        "n'ont pas signalé la fin de leur suivi."
    )
    expect(list_page.cloture_modal_content).to_contain_text(
        "Souhaitez-vous tout de même procéder à la clôture de ces événements ?"
    )
    list_page.confirm_cloture()

    expect(page.get_by_text("3 événements ont été clôturés avec succès.")).to_be_visible()
    assert EvenementAnimal.objects.filter(etat=EvenementAnimal.Etat.CLOTURE).count() == 3
    assert with_only_user_structure.fin_suivi.filter(contact=mus_contact).exists()
    assert not with_structure_still_following.fin_suivi.filter(contact=contact_still_following).exists()

    cloture_mails = [mail for mail in mailoutbox if "Clôture de l’évènement" in mail.subject]
    assert [mail.to for mail in cloture_mails] == [[contact_still_following.email]]
    assert contact_in_fin_de_suivi.email not in cloture_mails[0].to


def test_mass_cloture_only_cloture_eligible_evenements(live_server, page: Page, ac_user, mus_contact):
    en_cours = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)
    brouillon = EvenementAnimalFactory(etat=EvenementAnimal.Etat.BROUILLON, createur=mus_contact.structure)
    cloture = EvenementAnimalFactory(etat=EvenementAnimal.Etat.CLOTURE)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select_all()
    list_page.open_cloture_modal()

    expect(list_page.cloture_modal_content).to_contain_text(
        "1 des 3 événements sélectionnés est éligible à la clôture. "
        "Les autres (1 brouillon, 1 déjà clôturé) ne seront pas modifiés."
    )
    expect(list_page.cloture_modal_content).to_contain_text(
        "Vous êtes sur le point de clôturer 1 événement. Confirmez-vous cette action ?"
    )
    list_page.confirm_cloture()

    expect(page.get_by_text("1 événement a été clôturé avec succès.")).to_be_visible()
    for evenement, etat in (
        (en_cours, EvenementAnimal.Etat.CLOTURE),
        (brouillon, EvenementAnimal.Etat.BROUILLON),
        (cloture, EvenementAnimal.Etat.CLOTURE),
    ):
        evenement.refresh_from_db()
        assert evenement.etat == etat
    assert not Version.objects.get_for_object(cloture).exists()


def test_mass_cloture_when_no_evenement_is_eligible(live_server, page: Page, ac_user):
    evenements = [EvenementAnimalFactory(etat=EvenementAnimal.Etat.CLOTURE) for _ in range(2)]

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select(*evenements)
    list_page.open_cloture_modal()

    expect(list_page.cloture_modal_content).to_have_text(
        "Action impossible : aucun des 2 événements sélectionnés n'est éligible (2 déjà clôturés). "
        "Seuls les événements en cours ou en fin de suivi peuvent être clôturés."
    )
    expect(list_page.cloture_submit_button).to_be_hidden()
    expect(list_page.cloture_cancel_button).to_be_hidden()
    expect(list_page.cloture_close_button).to_be_visible()


def test_can_cancel_mass_cloture(live_server, page: Page, ac_user):
    evenement = EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)

    list_page = EvenementListPage(page, live_server.url)
    list_page.navigate()
    list_page.select(evenement)
    list_page.open_cloture_modal()
    list_page.cloture_cancel_button.click()

    expect(list_page.cloture_modal).to_be_hidden()
    evenement.refresh_from_db()
    assert evenement.etat == EvenementAnimal.Etat.EN_COURS


def test_mass_cloture_from_a_page_that_no_longer_exists_afterwards(live_server, page: Page, ac_user, monkeypatch):
    monkeypatch.setattr(EvenementListView, "paginate_by", 2)
    for _ in range(3):
        EvenementAnimalFactory(etat=EvenementAnimal.Etat.EN_COURS)

    list_page = EvenementListPage(page, live_server.url)
    page.goto(f"{live_server.url}{reverse('sa:evenement-liste')}?etat=en_cours&page=2")
    list_page.select_all()
    list_page.open_cloture_modal()
    list_page.confirm_cloture()

    expect(page.get_by_text("1 événement a été clôturé avec succès.")).to_be_visible()
    assert "etat=en_cours" in page.url
    assert "page=" not in page.url
    expect(list_page.row_checkboxes).to_have_count(2)


def test_having_structures_not_in_fin_suivi(mus_contact):
    contact = ContactStructureFactory()
    following = EvenementAnimalFactory()
    in_fin_de_suivi = EvenementAnimalFactory()
    only_excluded_structure = EvenementAnimalFactory()
    without_contact = EvenementAnimalFactory()
    following.contacts.add(contact)
    in_fin_de_suivi.contacts.add(contact)
    only_excluded_structure.contacts.add(mus_contact)
    FinSuiviContact.objects.create(
        contact=contact,
        object_id=in_fin_de_suivi.id,
        content_type=ContentType.objects.get_for_model(in_fin_de_suivi),
    )

    queryset = EvenementAnimal.objects.all()
    assert set(queryset.having_structures_not_in_fin_suivi()) == {following, only_excluded_structure}
    assert set(queryset.having_structures_not_in_fin_suivi(excluded_structure=mus_contact.structure)) == {following}
    assert without_contact not in queryset.having_structures_not_in_fin_suivi()
