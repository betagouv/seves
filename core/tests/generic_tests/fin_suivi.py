from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import Page, expect

from core.constants import AC_STRUCTURE, MUS_STRUCTURE
from core.factories import ContactAgentFactory
from core.mixins import WithEtatMixin
from core.models import FinSuiviContact, Structure


def generic_test_can_add_fin_de_suivi(live_server, page: Page, object, mailoutbox, mocked_authentification_user):
    ac_structure = Structure.objects.create(niveau1=AC_STRUCTURE, niveau2=MUS_STRUCTURE, libelle=MUS_STRUCTURE)
    active_contact = ContactAgentFactory(
        agent__structure=ac_structure, with_active_agent__with_groups=(settings.SSA_GROUP, settings.SV_GROUP)
    )
    object.contacts.add(active_contact)
    users_contact = mocked_authentification_user.agent.structure.contact_set.get()
    object.contacts.add(users_contact)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Signaler la fin de suivi").click()

    expect(page.get_by_text("Fin de suivi ajouté avec succès.")).to_be_visible()

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [active_contact.email]
    assert "Fin de suivi" in mail.subject
    assert "La fin de suivi a été déclarée pour" in mail.body

    fin_de_suivi = FinSuiviContact.objects.get()
    assert fin_de_suivi.content_object == object
    assert fin_de_suivi.contact == users_contact

    assert page.get_by_text("Fin de suivi").count() == 3
    page.get_by_role("button", name="Actions").click()
    page.get_by_role("button", name="Reprendre le suivi").click()

    expect(page.get_by_text("La reprise de suivi a été prise en compte.")).to_be_visible()
    assert len(mailoutbox) == 1
    assert FinSuiviContact.objects.count() == 0


def generic_test_can_filter_by_fin_de_suivi(live_server, page: Page, factory, url, mocked_authentification_user):
    obj_1 = factory(etat=WithEtatMixin.Etat.BROUILLON)
    obj_2 = factory(etat=WithEtatMixin.Etat.EN_COURS)
    obj_3 = factory(etat=WithEtatMixin.Etat.CLOTURE)
    obj_4 = factory(etat=WithEtatMixin.Etat.BROUILLON)
    obj_5 = factory(etat=WithEtatMixin.Etat.EN_COURS)
    obj_6 = factory(etat=WithEtatMixin.Etat.CLOTURE)

    for obj in (obj_4, obj_5, obj_6):
        FinSuiviContact.objects.create(
            contact=mocked_authentification_user.agent.structure.contact_set.get(),
            object_id=obj.id,
            content_type=ContentType.objects.get_for_model(obj),
        )

    page.goto(f"{live_server.url}{url}")
    page.locator("#id_etat").select_option("Fin de suivi", force=True)
    page.get_by_text("Rechercher", exact=True).click(force=True)

    expect(page.get_by_role("cell", name=str(obj_1.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(obj_2.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(obj_3.numero))).not_to_be_visible()
    expect(page.get_by_role("cell", name=str(obj_4.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(obj_5.numero))).to_be_visible()
    expect(page.get_by_role("cell", name=str(obj_6.numero))).to_be_visible()
