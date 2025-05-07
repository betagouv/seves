import pytest
from django.urls import reverse

from core.factories import ContactStructureFactory, StructureFactory
from sv.factories import EvenementFactory, FicheDetectionFactory
from sv.models import Structure, Evenement
from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import Page, expect
from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.models import Contact, FinSuiviContact, Message


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


def test_element_suivi_fin_suivi_creates_etat_fin_suivi(live_server, page: Page, mocked_authentification_user):
    """Test que l'ajout d'un élément de suivi de type 'fin de suivi' ajoute l'état 'fin de suivi'
    à la structure de l'agent connecté sur l'événement."""
    evenement = EvenementFactory()
    FicheDetectionFactory(evenement=evenement)
    _add_contacts(evenement, mocked_authentification_user)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("tab", name="Fil de suivi").click()
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Signaler la fin de suivi").click()
    page.get_by_label("Message").fill("test")
    page.get_by_test_id("fildesuivi-add-submit").click()
    page.get_by_test_id("contacts").click()
    expect(page.get_by_test_id("contacts-structures").get_by_text("Fin de suivi")).to_be_visible()
    expect(page.get_by_test_id("evenement-header").get_by_text("Fin de suivi", exact=True)).to_be_visible()

    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_role("cell", name="Fin de suivi")).to_be_visible()


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
    contact_structure = ContactStructureFactory()
    evenement.contacts.add(contact_structure)
    FinSuiviContact(
        content_type=ContentType.objects.get_for_model(evenement), object_id=evenement.id, contact=contact_structure
    ).save()
    mocked_authentification_user.agent.structure = contact_ac.structure

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()
    page.get_by_role("button", name="Clôturer").click()

    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
    expect(page.get_by_text("Clôturé", exact=True)).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE


def test_can_cloturer_evenement_if_contacts_structures_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un événement si toutes les structures de la liste des contacts sont en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    contact2 = ContactStructureFactory()

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
    page.get_by_role("button", name="Clôturer").click()

    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE


def test_can_cloturer_evenement_if_creator_structure_not_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un evenement si la structure du créateur de l'événement n'est pas en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    evenement.contacts.add(contact_ac)
    evenement.contacts.add(ContactStructureFactory(structure=evenement.createur))

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()

    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            "Pour information, les structures suivantes n’ont pas signalé la fin de suivi :"
        )
    ).to_be_visible()
    expect(page.get_by_label("Clôturer l'événement").get_by_text(contact_ac.structure.libelle)).to_be_visible()
    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            f"Souhaitez-vous tout de même procéder à la clôture de l'événement {evenement.numero} ?"
        )
    ).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.EN_COURS


def test_can_cloturer_evenement_if_on_off_contacts_structures_not_in_fin_suivi(
    live_server, page: Page, mocked_authentification_user, contact_ac: Contact
):
    """Test qu'un agent de l'AC connecté peut cloturer un événement si une structure de la liste des contacts n'est pas en fin de suivi."""
    evenement = EvenementFactory()
    mocked_authentification_user.agent.structure = contact_ac.structure
    contact2 = ContactStructureFactory()
    evenement.contacts.add(contact2)
    evenement.contacts.add(contact_ac)
    FinSuiviContact.objects.create(
        content_type=ContentType.objects.get_for_model(evenement),
        object_id=evenement.id,
        contact=contact_ac,
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()

    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            "Pour information, les structures suivantes n’ont pas signalé la fin de suivi :"
        )
    ).to_be_visible()
    expect(page.get_by_label("Clôturer l'événement").get_by_text(contact2.structure.libelle)).to_be_visible()
    expect(
        page.get_by_label("Clôturer l'événement").get_by_text(
            f"Souhaitez-vous tout de même procéder à la clôture de l'événement {evenement.numero} ?"
        )
    ).to_be_visible()
    page.get_by_role("button", name="Clôturer").click()

    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE


def test_cannot_cloturer_evenement_if_user_is_not_ac(live_server, page: Page, mocked_authentification_user):
    """Test qu'un agent connecté non membre de l'AC ne peut pas cloturer un événement même si la/les structure(s) de la liste des contacts sont en fin de suivi."""
    evenement = EvenementFactory()
    contact = ContactStructureFactory()
    evenement.contacts.add(contact)
    FinSuiviContact.objects.create(
        content_type=ContentType.objects.get_for_model(evenement), object_id=evenement.id, contact=contact
    )

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()

    expect(page.get_by_role("link", name="Clôturer l'événement")).not_to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.EN_COURS


def test_cloture_evenement_auto_fin_suivi_si_derniere_structure_ac(
    live_server, page: Page, mocked_authentification_user
):
    """Test qu'une structure de l'AC peut clôturer un événement si elle est la dernière structure de la liste des contacts à ne pas avoir signalé la fin de suivi.
    Dans ce cas, l'état 'fin de suivi' est ajouté à la structure de l'AC et un message fin de suivi est ajouté automatiquement."""
    evenement = EvenementFactory()
    contact_mus = ContactStructureFactory(
        structure__niveau1=AC_STRUCTURE, structure__niveau2=MUS_STRUCTURE, structure__libelle=MUS_STRUCTURE
    )
    contact_1 = ContactStructureFactory()
    evenement.contacts.set([contact_mus, contact_1])
    evenement_content_type = ContentType.objects.get_for_model(evenement)
    FinSuiviContact(content_type=evenement_content_type, object_id=evenement.id, contact=contact_1).save()
    mocked_authentification_user.agent.structure = contact_mus.structure
    mocked_authentification_user.agent.save()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Clôturer l'événement").click()
    expect(page.get_by_text(f"Confirmez-vous la clôture de l’événement {evenement.numero}")).to_be_visible()
    page.get_by_role("button", name="Clôturer").click()

    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
    evenement.refresh_from_db()
    assert evenement.etat == Evenement.Etat.CLOTURE
    assert FinSuiviContact.objects.filter(
        content_type=evenement_content_type, object_id=evenement.id, contact=contact_mus
    ).exists()
    assert Message.objects.filter(
        message_type=Message.FIN_SUIVI,
        sender=mocked_authentification_user.agent.contact_set.get(),
        content_type=evenement_content_type,
        object_id=evenement.id,
    ).exists()


def test_show_cloture_tag(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_text("Clôturé")).to_be_visible()


@pytest.mark.django_db
def test_cant_publish_evenement_i_cant_see(client):
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON, createur=StructureFactory())
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    response = client.post(
        reverse("publish"),
        data={
            "content_type_id": ContentType.objects.get_for_model(evenement).id,
            "content_id": evenement.id,
        },
    )

    assert response.status_code == 302
    assert evenement.etat == Evenement.Etat.BROUILLON


def test_cant_see_cloture_evenement_button_if_is_already_cloture(live_server, page: Page):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_role("button", name="Actions")).not_to_be_visible()
    expect(page.get_by_role("link", name="Clôturer l'événement")).not_to_be_visible()


def test_cant_cloture_evenement_if_already_cloture(client):
    evenement = EvenementFactory(etat=Evenement.Etat.CLOTURE)

    response = client.post(
        reverse("cloturer", kwargs={"pk": evenement.id}),
        data={"content_type_id": ContentType.objects.get_for_model(evenement).id},
    )

    evenement.refresh_from_db()
    assert response.status_code == 302
    assert evenement.is_deleted is False
