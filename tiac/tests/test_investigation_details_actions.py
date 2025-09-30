from playwright.sync_api import expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import ContactStructureFactory
from core.models import Structure, Contact
from tiac.factories import InvestigationTiacFactory
from tiac.models import InvestigationTiac
from .pages import InvestigationTiacDetailsPage


def test_can_delete_investigation_tiac(live_server, page):
    evenement = InvestigationTiacFactory()
    assert InvestigationTiac.objects.count() == 1

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'investigation TIAC {evenement.numero} a bien été supprimée")).to_be_visible()

    assert InvestigationTiac.objects.count() == 0
    assert InvestigationTiac._base_manager.get().pk == evenement.pk


def test_can_cloturer_investigation(live_server, page, mocked_authentification_user):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    contact = Contact.objects.create(structure=ac_structure)
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS)
    mocked_authentification_user.agent.structure = ac_structure
    evenement.contacts.add(contact)
    evenement.contacts.add(ContactStructureFactory(structure=evenement.createur))

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer()

    evenement.refresh_from_db()
    assert evenement.etat == InvestigationTiac.Etat.CLOTURE
    expect(page.get_by_text("Clôturé", exact=True)).to_be_visible()
    expect(page.get_by_text(f"L'investigation n°{evenement.numero} a bien été clôturée.")).to_be_visible()


def test_can_cloturer_investigation_if_last_remaining_structure(live_server, page, mocked_authentification_user):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    contact = Contact.objects.create(structure=ac_structure)
    evenement = InvestigationTiacFactory(etat=InvestigationTiac.Etat.EN_COURS, createur=ac_structure)
    mocked_authentification_user.agent.structure = ac_structure
    evenement.contacts.add(contact)

    details_page = InvestigationTiacDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer()

    evenement.refresh_from_db()
    assert evenement.etat == InvestigationTiac.Etat.CLOTURE
    expect(page.get_by_text("Clôturé", exact=True)).to_be_visible()
    expect(page.get_by_text(f"L'investigation n°{evenement.numero} a bien été clôturée.")).to_be_visible()
