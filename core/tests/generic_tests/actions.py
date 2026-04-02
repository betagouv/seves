import re

from playwright.sync_api import expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import ContactStructureFactory
from core.mixins import WithEtatMixin
from core.models import LienLibre, Structure


def generic_test_can_cloturer_evenement(
    live_server, page, object, mocked_authentification_user, mailoutbox, nav_name=None
):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    contact_ac = ContactStructureFactory(structure=ac_structure)

    mocked_authentification_user.agent.structure = ac_structure
    object.contacts.add(contact_ac)
    other_contact = ContactStructureFactory(structure=object.createur)
    object.contacts.add(other_contact)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    nav_name = nav_name or "Clôturer l'événement"
    page.get_by_role("link", name=nav_name).click()
    page.get_by_role("button", name="Clôturer").click()

    object.refresh_from_db()
    assert object.etat == WithEtatMixin.Etat.CLOTURE
    expect(page.get_by_text("Clôturé", exact=True)).to_be_visible()
    expect(page.get_by_text(f"L'événement n°{object.numero} a bien été clôturé.")).to_be_visible()

    assert len(mailoutbox) == 1, f"Found {len(mailoutbox)}"
    mail = mailoutbox[0]
    assert set(mail.to) == {other_contact.email}
    assert "Clôture de l’évènement" in mail.subject


def generic_test_ac_can_update_fiche_even_when_state_is_cloture(
    live_server, page, object, mocked_authentification_user, field_to_edit
):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    ContactStructureFactory(structure=ac_structure)
    object.etat = WithEtatMixin.Etat.CLOTURE
    object.save()

    mocked_authentification_user.agent.structure = ac_structure
    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Modifier l'événement").click()
    expect(page.get_by_text("Modification d'une fiche clôturée", exact=True)).to_be_visible()
    page.get_by_role("link", name="Poursuivre la modification").click()
    page.wait_for_url(re.compile(r".*(modification|edition).*"))

    page.locator(field_to_edit).fill("Test")
    page.get_by_role("button", name="Enregistrer").first.click()
    expect(page.get_by_text(f"Événement {object.numero}", exact=True)).to_be_visible()

    object.refresh_from_db()
    assert object.etat == WithEtatMixin.Etat.CLOTURE


def generic_test_can_update_fiche_even_when_free_links_exists_to_a_deleted_object(
    live_server, page, object, field_name, other_object
):
    LienLibre.objects.create(related_object_1=object, related_object_2=other_object)
    other_object.is_deleted = True
    other_object.save()

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Modifier l'événement").click()
    page.wait_for_url(re.compile(r".*(modification|edition).*"))

    page.locator(f"#id_{field_name}").fill("Test")
    page.get_by_role("button", name="Enregistrer").first.click()
    expect(page.get_by_text(f"Événement {object.numero}", exact=True)).to_be_visible()

    object.refresh_from_db()
    assert getattr(object, field_name) == "Test"


def generic_test_soft_delete_object_also_removes_existing_lien_libre(live_server, page, object, other_object):
    LienLibre.objects.create(related_object_1=object, related_object_2=other_object)
    assert LienLibre.objects.count() == 1

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    expect(page.get_by_text(other_object.numero, exact=True)).to_be_visible()

    page.get_by_role("button", name="Actions").click()
    page.get_by_role("link", name="Supprimer l'événement").click()
    page.get_by_test_id("submit-delete-modal").click()

    page.goto(f"{live_server.url}{other_object.get_absolute_url()}")
    expect(page.get_by_text(f"Événement {other_object.numero}", exact=True)).to_be_visible()
    expect(page.get_by_text(object.numero, exact=True)).not_to_be_visible()

    object.refresh_from_db()
    assert object.is_deleted is True
    assert LienLibre.objects.count() == 0
