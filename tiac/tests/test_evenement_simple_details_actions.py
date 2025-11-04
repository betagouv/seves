from playwright.sync_api import expect, Page

from core.factories import ContactStructureFactory, ContactAgentFactory
from core.models import Structure, Contact, LienLibre
from tiac.factories import EvenementSimpleFactory, EtablissementFactory
from tiac.models import EvenementSimple, InvestigationTiac
from .pages import EvenementSimpleDetailsPage
from core.constants import AC_STRUCTURE, MUS_STRUCTURE


def test_can_delete_evenement_simple(live_server, page):
    evenement = EvenementSimpleFactory()
    assert EvenementSimple.objects.count() == 1

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.delete()
    expect(page.get_by_text(f"L'évènement {evenement.numero} a bien été supprimé")).to_be_visible()

    assert EvenementSimple.objects.count() == 0
    assert EvenementSimple._base_manager.get().pk == evenement.pk


def test_can_cloturer_evenement_simple(live_server, page: Page, mocked_authentification_user):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    contact = Contact.objects.create(structure=ac_structure)
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    mocked_authentification_user.agent.structure = ac_structure
    evenement.contacts.add(contact)
    evenement.contacts.add(ContactStructureFactory(structure=evenement.createur))

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.cloturer()

    evenement.refresh_from_db()
    assert evenement.etat == EvenementSimple.Etat.CLOTURE
    expect(page.get_by_text("Clôturé", exact=True)).to_be_visible()
    expect(page.get_by_text(f"L'événement n°{evenement.numero} a bien été clôturé.")).to_be_visible()


def test_can_publish_evenement_produit(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementSimpleFactory()

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.publish()

    evenement.refresh_from_db()
    assert evenement.etat == EvenementSimple.Etat.EN_COURS
    expect(page.get_by_text("En cours", exact=True)).to_be_visible()
    expect(page.get_by_text("Événement simple publié avec succès")).to_be_visible()


def test_can_transfer_evenement_simple(live_server, page: Page, choice_js_fill):
    contact = ContactStructureFactory(structure__libelle="DDPP52")
    ContactAgentFactory(agent__structure=contact.structure, with_active_agent=True)
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.transfer(choice_js_fill, "DDPP52")

    evenement.refresh_from_db()
    expect(page.get_by_text("L’évènement a bien été transféré à la DDPP52")).to_be_visible()
    assert evenement.transfered_to == contact.structure
    assert contact in evenement.contacts.all()


def test_can_transform_evenement_simple_into_investigation_tiac(live_server, page: Page, choice_js_fill):
    assert InvestigationTiac.objects.count() == 0
    evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    other_evenement = EvenementSimpleFactory(etat=EvenementSimple.Etat.EN_COURS)
    LienLibre.objects.create(related_object_1=evenement, related_object_2=other_evenement)
    EtablissementFactory(evenement_simple=evenement)
    EtablissementFactory(evenement_simple=evenement)
    assert EvenementSimple.objects.count() == 2

    details_page = EvenementSimpleDetailsPage(page, live_server.url)
    details_page.navigate(evenement)
    details_page.transform()

    expect(page.get_by_text("L'événement a bien été passé en investigation de TIAC.")).to_be_visible()

    assert EvenementSimple.objects.count() == 2
    evenement.refresh_from_db()
    assert evenement.is_cloture is True

    investigation = InvestigationTiac.objects.get()
    assert investigation.is_draft is True
    fields_to_compare = [
        "date_reception",
        "evenement_origin",
        "modalites_declaration",
        "contenu",
        "notify_ars",
        "nb_sick_persons",
    ]
    for field in fields_to_compare:
        assert getattr(investigation, field) == getattr(evenement, field)
    assert investigation.etablissements.count() == 2

    linked_objects = set(
        [
            link.related_object_1 if link.related_object_1 != investigation else link.related_object_2
            for link in LienLibre.objects.for_object(investigation)
        ]
    )
    assert linked_objects == {evenement, other_evenement}
