from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import ContactStructureFactory
from core.models import Structure, Contact
from ssa.factories import EvenementProduitFactory
from ssa.models import EvenementProduit
from ssa.tests.pages import EvenementProduitDetailsPage


def test_can_delete_evenement_produit(live_server, page):
    evenement = EvenementProduitFactory()
    assert EvenementProduit.objects.count() == 1

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'évènement {evenement.numero} a bien été supprimé")).to_be_visible()

    assert EvenementProduit.objects.count() == 0
    assert EvenementProduit._base_manager.get().pk == evenement.pk


def test_can_cloturer_evenement_produit(live_server, page: Page, mocked_authentification_user):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    contact = Contact.objects.create(structure=ac_structure)
    evenement = EvenementProduitFactory(etat=EvenementProduit.Etat.EN_COURS)
    mocked_authentification_user.agent.structure = ac_structure
    evenement.contacts.add(contact)
    evenement.contacts.add(ContactStructureFactory(structure=evenement.createur))

    details_page = EvenementProduitDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer()

    evenement.refresh_from_db()
    assert evenement.etat == EvenementProduit.Etat.CLOTURE
    expect(page.get_by_text("Clôturé", exact=True)).to_be_visible()
    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()
