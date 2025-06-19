from unittest.mock import patch

import pytest
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.contrib.auth.models import Group

from core.factories import StructureFactory, ContactStructureFactory, ContactAgentFactory
from seves import settings
from sv.factories import EvenementFactory, FicheDetectionFactory
from core.models import Structure, Visibilite
from core.constants import BSV_STRUCTURE, MUS_STRUCTURE, AC_STRUCTURE
from sv.models import Evenement


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCALE, Visibilite.NATIONALE])
@pytest.mark.parametrize("etat_libelle", [Evenement.Etat.BROUILLON, Evenement.Etat.EN_COURS, Evenement.Etat.CLOTURE])
def test_agent_in_structure_createur_can_view_evenement(
    live_server, page: Page, mocked_authentification_user, visibilite_libelle: str, etat_libelle
):
    fiche_detection = FicheDetectionFactory(evenement__visibilite=visibilite_libelle, evenement__etat=etat_libelle)
    response = page.goto(f"{live_server.url}{fiche_detection.evenement.get_absolute_url()}")
    assert response.status == 200
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text(str(fiche_detection.evenement.numero), exact=True)).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("etat_libelle", [Evenement.Etat.BROUILLON, Evenement.Etat.EN_COURS, Evenement.Etat.CLOTURE])
def test_agent_in_structure_createur_can_view_evenement_limitee(
    live_server, page: Page, mocked_authentification_user, etat_libelle
):
    fiche_detection = FicheDetectionFactory(evenement__etat=etat_libelle)
    evenement = fiche_detection.evenement
    evenement.allowed_structures.set([StructureFactory()])
    evenement.visibilite = Visibilite.LIMITEE
    evenement.save()

    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert response.status == 200
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text(str(evenement.numero), exact=True)).to_be_visible()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_cannot_view_evenement_locale(
    live_server, page: Page, mocked_authentification_user
):
    evenement = EvenementFactory(visibilite=Visibilite.LOCALE)
    mocked_authentification_user.agent.structure = StructureFactory()
    mocked_authentification_user.agent.save()

    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert response.status == 403
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_role("link", name=str(evenement.numero))).not_to_be_visible()


@pytest.mark.django_db
def test_agent_not_in_structure_createur_can_view_evenement_national(
    live_server, page: Page, mocked_authentification_user
):
    evenement = EvenementFactory(visibilite=Visibilite.NATIONALE)
    FicheDetectionFactory(evenement=evenement)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Événement {str(evenement.numero)}")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_role("link", name=str(evenement.numero))).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_cannot_view_evenement_brouillon(
    live_server, page: Page, mocked_authentification_user, structure_ac: str
):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)
    mocked_authentification_user.agent.structure, _ = Structure.objects.get_or_create(
        niveau1=AC_STRUCTURE, niveau2=structure_ac
    )
    mocked_authentification_user.agent.save()
    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert response.status == 403


@pytest.mark.django_db
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_view_own_evenement_brouillon(
    live_server, page: Page, mocked_authentification_user, structure_ac: str
):
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=structure_ac)
    ContactStructureFactory(structure=structure)
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON, createur=structure)
    mocked_authentification_user.agent.structure = structure
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Événement {str(evenement.numero)}")).to_be_visible()


@pytest.mark.django_db
@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCALE, Visibilite.LIMITEE, Visibilite.NATIONALE])
@pytest.mark.parametrize("structure_ac", [MUS_STRUCTURE, BSV_STRUCTURE])
def test_agent_ac_can_view_evenement(
    live_server,
    page: Page,
    mocked_authentification_user,
    visibilite_libelle: str,
    structure_ac: str,
):
    evenement = EvenementFactory()
    if visibilite_libelle == Visibilite.LIMITEE:
        evenement.allowed_structures.set([StructureFactory()])
    evenement.visibilite = visibilite_libelle
    evenement.save()
    FicheDetectionFactory(evenement=evenement)
    structure, _ = Structure.objects.get_or_create(niveau1=AC_STRUCTURE, niveau2=structure_ac)
    ContactStructureFactory(structure=structure)
    mocked_authentification_user.agent.structure = structure
    mocked_authentification_user.agent.save()
    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert response.status == 200
    expect(page.get_by_role("heading", name=f"Événement {str(evenement.numero)}")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_role("link", name=str(evenement.numero))).to_be_visible()


@pytest.mark.django_db
def test_agent_can_see_visibilite_limitee_if_in_list(live_server, page: Page, mocked_authentification_user):
    structure = StructureFactory()
    ContactStructureFactory(structure=structure)
    evenement = EvenementFactory()
    evenement.allowed_structures.set([structure])
    evenement.visibilite = Visibilite.LIMITEE
    evenement.save()
    mocked_authentification_user.agent.structure = structure
    mocked_authentification_user.agent.save()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("heading", name=f"Événement {str(evenement.numero)}")).to_be_visible()


@pytest.mark.django_db
def test_agent_cant_see_visibilite_limitee_if_not_in_list(live_server, page: Page, mocked_authentification_user):
    structure = StructureFactory()
    other_structure = StructureFactory()

    evenement = EvenementFactory()
    evenement.allowed_structures.set([other_structure])
    evenement.visibilite = Visibilite.LIMITEE
    evenement.save()

    mocked_authentification_user.agent.structure = structure
    mocked_authentification_user.agent.save()
    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert response.status == 403


def test_agent_with_referent_national_group_cannot_view_evenement_brouillon(
    live_server, page: Page, mocked_authentification_user
):
    referent_national_group, _ = Group.objects.get_or_create(name=settings.REFERENT_NATIONAL_GROUP)
    mocked_authentification_user.groups.add(referent_national_group)
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON, createur=StructureFactory())
    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    assert response.status == 403


@pytest.mark.parametrize("visibilite_libelle", [Visibilite.LOCALE, Visibilite.LIMITEE, Visibilite.NATIONALE])
def test_agent_with_referent_national_group_can_view_evenement(
    live_server, page: Page, mocked_authentification_user, visibilite_libelle
):
    referent_national_group, _ = Group.objects.get_or_create(name=settings.REFERENT_NATIONAL_GROUP)
    mocked_authentification_user.groups.add(referent_national_group)
    evenement = EvenementFactory(createur=StructureFactory())
    if visibilite_libelle == Visibilite.LIMITEE:
        evenement.allowed_structures.set([StructureFactory()])
    evenement.visibilite = visibilite_libelle
    evenement.save()
    FicheDetectionFactory(evenement=evenement)

    response = page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    assert response.status == 200
    expect(page.get_by_role("heading", name=f"Événement {str(evenement.numero)}")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_role("link", name=str(evenement.numero))).to_be_visible()


def test_agent_added_in_contacts_can_view_evenement(live_server, page: Page, client, choice_js_fill, goto_contacts):
    evenement = EvenementFactory()
    contact_structure = ContactStructureFactory()
    contact_agent = ContactAgentFactory(with_active_agent=True, agent__structure=contact_structure.structure)

    def mocked(self, request):
        request.user = contact_agent.agent.user
        return self.get_response(request)

    with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked):
        response = client.get(evenement.get_absolute_url())
        assert response.status_code == 403

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    choice_js_fill(
        page, "#add-contact-agent-form .choices", contact_agent.agent.nom, contact_agent.display_with_agent_unit
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    evenement.refresh_from_db()
    assert evenement.is_visibilite_limitee
    assert evenement.allowed_structures.get() == contact_structure.structure

    with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked):
        response = client.get(evenement.get_absolute_url())
        assert response.status_code == 200


@pytest.mark.django_db
def test_structure_added_in_contacts_can_view_evenement(live_server, page: Page, client, choice_js_fill, goto_contacts):
    evenement = EvenementFactory()
    contact_structure = ContactStructureFactory()
    contact_agent = ContactAgentFactory(with_active_agent=True, agent__structure=contact_structure.structure)

    def mocked(self, request):
        request.user = contact_agent.agent.user
        return self.get_response(request)

    with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked):
        response = client.get(evenement.get_absolute_url())
        assert response.status_code == 403

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    choice_js_fill(page, "#add-contact-structure-form .choices", str(contact_structure), str(contact_structure))
    page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()

    evenement.refresh_from_db()
    assert evenement.is_visibilite_limitee
    assert evenement.allowed_structures.count() == 1
    assert contact_structure.structure in evenement.allowed_structures.all()
    with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked):
        response = client.get(evenement.get_absolute_url())
        assert response.status_code == 200


@pytest.mark.django_db
def test_adding_contact_preserves_existing_allowed_structures(
    live_server, page: Page, mocked_authentification_user, client, choice_js_fill, goto_contacts
):
    contact_structure_1 = ContactStructureFactory(with_one_active_agent=True)
    contact_structure_2 = ContactStructureFactory(with_one_active_agent=True)
    evenement = EvenementFactory()
    evenement.allowed_structures.set([contact_structure_1.structure])
    evenement.visibilite = Visibilite.LIMITEE
    evenement.save()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    choice_js_fill(page, "#add-contact-structure-form .choices", str(contact_structure_2), str(contact_structure_2))
    page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()

    evenement.refresh_from_db()
    assert evenement.is_visibilite_limitee
    assert evenement.allowed_structures.count() == 2
    assert contact_structure_1.structure in evenement.allowed_structures.all()
    assert contact_structure_2.structure in evenement.allowed_structures.all()


@pytest.mark.django_db
def test_agent_referent_national_in_contacts_does_not_grant_access_to_other_agents_in_structure(
    live_server, page: Page, client, choice_js_fill, goto_contacts
):
    """
    Test que si un agent référent national est ajouté dans les contacts d'un événement,
    les autres agents de sa structure n'ont pas automatiquement accès à l'événement.
    """
    contact_structure = ContactStructureFactory()
    referent_national_group, _ = Group.objects.get_or_create(name=settings.REFERENT_NATIONAL_GROUP)
    agent_referent = ContactAgentFactory(with_active_agent=True, agent__structure=contact_structure.structure)
    agent_referent.agent.user.groups.add(referent_national_group)
    autre_agent = ContactAgentFactory(with_active_agent=True, agent__structure=contact_structure.structure)
    evenement = EvenementFactory()

    def mocked_autre_agent(self, request):
        request.user = autre_agent.agent.user
        return self.get_response(request)

    def mocked_referent(self, request):
        request.user = agent_referent.agent.user
        return self.get_response(request)

    with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked_autre_agent):
        response = client.get(evenement.get_absolute_url())
        assert response.status_code == 403

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    goto_contacts(page)
    choice_js_fill(
        page, "#add-contact-agent-form .choices", agent_referent.agent.nom, agent_referent.display_with_agent_unit
    )
    page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    evenement.refresh_from_db()
    assert evenement.is_visibilite_locale
    assert evenement.allowed_structures.count() == 0
    with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked_referent):
        response = client.get(evenement.get_absolute_url())
        assert response.status_code == 200
    with patch("seves.middlewares.LoginAndGroupRequiredMiddleware.__call__", mocked_autre_agent):
        response = client.get(evenement.get_absolute_url())
        assert response.status_code == 403
