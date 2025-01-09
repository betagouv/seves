import pytest
from model_bakery import baker

from sv.factories import EvenementFactory
from sv.models import Etat, Structure, Evenement
from django.utils.timezone import now, timedelta
from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import Page, expect
from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.models import Contact, FinSuiviContact


@pytest.fixture
def contact_ac(db):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    return Contact.objects.create(structure=ac_structure)


def _add_contacts(evenement, mocked_authentification_user):
    """Ajoute l'agent et la structure de l'agent connecté aux contacts."""
    user_contact_agent = Contact.objects.get(agent=mocked_authentification_user.agent)
    user_contact_structure = Contact.objects.get(structure=mocked_authentification_user.agent.structure)
    evenement.contacts.add(user_contact_agent)
    evenement.contacts.add(user_contact_structure)


def test_etat_initial():
    """Test que l'état initial d'un evenement est bien 'nouveau' lors de sa création."""
    etat_nouveau = Etat.objects.get_or_create(libelle=Etat.NOUVEAU)[0]
    evenement = EvenementFactory()
    assert evenement.etat == etat_nouveau


def test_command_updates_evenement_status():
    """Test que la commande update_evenement_etat met à jour l'état de l'événement à 'en cours'
    si elles ont été créées il y a plus de 15 jours."""
    EvenementFactory(date_creation=(now() - timedelta(days=15)))
    call_command("update_evenement_etat")
    assert Evenement.objects.first().etat.libelle == Etat.EN_COURS


def test_element_suivi_fin_suivi_creates_etat_fin_suivi(live_server, page: Page, mocked_authentification_user):
    """Test que l'ajout d'un élément de suivi de type 'fin de suivi' ajoute l'état 'fin de suivi'
    à la structure de l'agent connecté sur l'événement."""
    evenement = EvenementFactory()
    _add_contacts(evenement, mocked_authentification_user)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Fil de suivi").click()
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Signaler la fin de suivi").click()
    page.get_by_label("Message").fill("test")
    page.get_by_test_id("fildesuivi-add-submit").click()
    page.get_by_test_id("contacts").click()
    expect(page.get_by_label("Contacts").get_by_text("Fin de suivi")).to_be_visible()


def test_element_suivi_fin_suivi_already_exists(live_server, page: Page, mocked_authentification_user):
    """Test l'impossibilité de créer un élément de suivi de type 'fin de suivi' s'il en existe déjà un pour la structure de l'agent connecté."""
    evenement = EvenementFactory()
    _add_contacts(evenement, mocked_authentification_user)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    for _ in range(2):
        page.get_by_role("tab", name="Fil de suivi").click()
        page.get_by_test_id("element-actions").click()
        page.get_by_role("link", name="Signaler la fin de suivi").click()
        page.get_by_label("Message").fill("test")
        page.get_by_test_id("fildesuivi-add-submit").click()

    expect(page.locator("body")).to_contain_text(
        "Un objet Fin suivi contact avec ces champs Content type, Object id et Contact existe déjà."
    )
    rows = page.locator("table.fil-de-suivi tbody tr")
    expect(rows).to_have_count(1)


def test_cannot_create_fin_suivi_if_structure_not_in_contacts(live_server, page: Page, mocked_authentification_user):
    """Test l'impossibilité de créer un élément de suivi de type 'fin de suivi' si la structure de l'agent connecté n'est pas dans les contacts de l'évenement."""
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Fil de suivi").click()
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Signaler la fin de suivi").click()
    page.get_by_label("Message").fill("test")
    page.get_by_test_id("fildesuivi-add-submit").click()
    expect(page.locator("body")).to_contain_text(
        "Vous ne pouvez pas signaler la fin de suivi pour cette fiche car votre structure n'est pas dans la liste des contacts."
    )
    rows = page.locator("table.fil-de-suivi tbody tr")
    expect(rows).to_have_count(0)


def test_can_cloturer_evenement_if_creator_structure_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un événement si la structure du créateur (seule présente dans la liste des contacts) de la événement est en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    evenement.contacts.add(contact_ac)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Signaler la fin de suivi").click()
    page.get_by_label("Message").fill("a")
    page.get_by_test_id("fildesuivi-add-submit").click()
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()
    page.get_by_role("button", name="Confirmer la clôture").click()

    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
    expect(page.get_by_text("clôturé", exact=True)).to_be_visible()
    page.get_by_role("button", name="Actions").click()
    expect(page.get_by_role("link", name="Clôturer l'événement")).not_to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat.libelle == Etat.CLOTURE


def test_can_cloturer_evenement_if_contacts_structures_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un événement si toutes les structures de la liste des contacts sont en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    contact2 = Contact.objects.create(structure=baker.make(Structure, _fill_optional=True))

    evenement.contacts.add(contact2)
    evenement.contacts.add(contact_ac)

    content_type = ContentType.objects.get_for_model(evenement)
    FinSuiviContact.objects.create(content_type=content_type, object_id=evenement.id, contact=contact2)
    FinSuiviContact.objects.create(
        content_type=content_type,
        object_id=evenement.id,
        contact=contact_ac,
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()
    page.get_by_role("button", name="Confirmer la clôture").click()

    evenement.refresh_from_db()
    assert evenement.etat == Etat.objects.get(libelle=Etat.CLOTURE)


def test_cannot_cloturer_evenement_if_creator_structure_not_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté ne peut pas cloturer un evenement si la structure du créateur de l'événement n'est pas en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    evenement.contacts.add(contact_ac)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()

    cloturer_element = page.get_by_label("Clôturer un événement")
    expect(cloturer_element.get_by_role("paragraph")).to_contain_text(
        f"Vous ne pouvez pas clôturer l'événement n°{evenement.numero} car les structures suivantes n'ont pas signalées la fin de suivi :"
    )
    expect(cloturer_element.get_by_role("listitem")).to_contain_text(contact_ac.structure.libelle)
    evenement.refresh_from_db()
    assert evenement.etat.libelle == Etat.NOUVEAU


@pytest.mark.skip(reason="refacto evenement")
def test_cannot_cloturer_evenement_if_on_off_contacts_structures_not_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté ne peut pas cloturer un événement si une structure de la liste des contacts n'est pas en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    contact2 = Contact.objects.create(structure=baker.make(Structure, _fill_optional=True))

    evenement.contacts.add(contact2)
    evenement.contacts.add(contact_ac)

    content_type = ContentType.objects.get_for_model(evenement)
    FinSuiviContact.objects.create(
        content_type=content_type,
        object_id=evenement.id,
        contact=contact_ac,
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()

    expect(page.get_by_label("Clôturer un événement").get_by_role("paragraph")).to_contain_text(
        f"Vous ne pouvez pas clôturer l'événement n°{evenement.numero} car les structures suivantes n'ont pas signalées la fin de suivi :"
    )
    expect(page.get_by_label("Clôturer un événement").get_by_role("listitem")).to_contain_text(
        contact2.structure.libelle
    )
    evenement.refresh_from_db()
    assert evenement.etat == Etat.objects.get(libelle=Etat.NOUVEAU)


def test_cannot_cloturer_evenement_if_user_is_not_ac(live_server, page: Page, mocked_authentification_user):
    """Test qu'un agent connecté non membre de l'AC ne peut pas cloturer un événement même si la/les structure(s) de la liste des contacts sont en fin de suivi."""
    evenement = EvenementFactory()
    contact = Contact.objects.create(structure=baker.make(Structure, _fill_optional=True))
    evenement.contacts.add(contact)
    FinSuiviContact.objects.create(
        content_type=ContentType.objects.get_for_model(evenement), object_id=evenement.id, contact=contact
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()

    expect(page.get_by_role("link", name="Clôturer l'événement")).not_to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Etat.objects.get(libelle=Etat.NOUVEAU)
