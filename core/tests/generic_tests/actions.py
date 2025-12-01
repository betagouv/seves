from playwright.sync_api import expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import ContactStructureFactory
from core.mixins import WithEtatMixin
from core.models import Structure


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
