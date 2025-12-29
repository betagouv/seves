from playwright.sync_api import expect

from core.factories import ContactStructureFactory, ContactAgentFactory
from core.pages import WithContactsPage
from seves.settings import SSA_GROUP, SV_GROUP


def generic_test_add_contact_agent_to_an_evenement(live_server, page, choice_js_fill, object, mailoutbox):
    contact_structure = ContactStructureFactory()
    contact = ContactAgentFactory(
        with_active_agent__with_groups=(SSA_GROUP, SV_GROUP), agent__structure=contact_structure.structure
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.add_agent(choice_js_fill, contact)

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("L'agent a été ajouté avec succès.")).to_be_visible()
    expect(page.get_by_test_id("contacts-agents")).to_be_visible()
    assert page.get_by_test_id("contacts-agents").count() == 1
    assert object.__class__.objects.filter(pk=object.pk, contacts=contact).exists()

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "Ajout aux contacts" in mail.subject
    assert "Vous avez été ajouté au suivi de l’évènement" in mail.body


def generic_test_add_contact_structure_to_an_evenement(live_server, page, choice_js_fill, object, mailoutbox):
    contact_structure = ContactStructureFactory(with_one_active_agent__with_groups=(SSA_GROUP, SV_GROUP))

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.add_structure(choice_js_fill, contact_structure)

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("La structure a été ajoutée avec succès.")).to_be_visible()
    expect(page.get_by_test_id("contacts-structures")).to_be_visible()
    assert page.get_by_test_id("contacts-structures").count() == 1
    assert object.__class__.objects.filter(pk=object.pk, contacts=contact_structure).exists()

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "Ajout aux contacts" in mail.subject
    assert "Vous avez été ajouté au suivi de l’évènement" in mail.body


def generic_test_add_contact_structure_to_an_evenement_with_dedicated_email(
    live_server, page, choice_js_fill, object, mailoutbox, domain
):
    contact_structure = ContactStructureFactory(with_one_active_agent__with_groups=(SSA_GROUP, SV_GROUP))
    setattr(contact_structure, f"{domain}_email", "testemail@test.com")
    contact_structure.save()

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.add_structure(choice_js_fill, contact_structure)

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("La structure a été ajoutée avec succès.")).to_be_visible()
    expect(page.get_by_test_id("contacts-structures")).to_be_visible()
    assert page.get_by_test_id("contacts-structures").count() == 1
    expect(page.get_by_text("testemail@test.com", exact=True)).to_be_visible()
    assert object.__class__.objects.filter(pk=object.pk, contacts=contact_structure).exists()

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "Ajout aux contacts" in mail.subject
    assert "Vous avez été ajouté au suivi de l’évènement" in mail.body
    assert mail.to == ["testemail@test.com"], f"Got {mail.to}"


def generic_test_remove_contact_agent_from_an_evenement(live_server, page, object, mailoutbox):
    contact = ContactAgentFactory()
    object.contacts.set([contact])

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.remove_contact(contact)

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("Le contact a bien été supprimé de la fiche.")).to_be_visible()
    assert object.contacts.count() == 0

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "Retrait des contacts" in mail.subject
    assert "Vous avez été retiré du suivi de l’évènement" in mail.body


def generic_test_remove_contact_structure_from_an_evenement(live_server, page, object, mailoutbox):
    contact = ContactStructureFactory()
    object.contacts.set([contact])

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.remove_contact(contact)

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("Le contact a bien été supprimé de la fiche.")).to_be_visible()
    assert object.contacts.count() == 0

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert "Retrait des contacts" in mail.subject
    assert "Vous avez été retiré du suivi de l’évènement" in mail.body


def generic_test_add_multiple_contacts_agents_to_an_evenement(live_server, page, object, choice_js_fill, mailoutbox):
    contact_structure = ContactStructureFactory()
    contact_agent_1, contact_agent_2 = ContactAgentFactory.create_batch(
        2, with_active_agent__with_groups=(SSA_GROUP, SV_GROUP), agent__structure=contact_structure.structure
    )

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    contact_page.add_agents(choice_js_fill, [contact_agent_1, contact_agent_2])

    contact_page.go_to_contact_tab()
    expect(page.get_by_text("Les 2 agents ont été ajoutés avec succès.")).to_be_visible()
    assert page.get_by_test_id("contacts-agents").count() == 2
    expect(
        page.get_by_test_id("contacts-agents").get_by_text(
            f"{contact_agent_1.agent.nom} {contact_agent_1.agent.prenom}", exact=True
        )
    ).to_be_visible()
    expect(
        page.get_by_test_id("contacts-agents").get_by_text(
            f"{contact_agent_2.agent.nom} {contact_agent_2.agent.prenom}", exact=True
        )
    ).to_be_visible()

    assert len(mailoutbox) == 2
    assert "Ajout aux contacts" in mailoutbox[0].subject
    assert "Ajout aux contacts" in mailoutbox[1].subject


def generic_test_cant_add_contact_agent_if_he_cant_access_domain(live_server, page, choice_js_cant_pick, object):
    contact_structure = ContactStructureFactory()
    contact = ContactAgentFactory(with_active_agent=True, agent__structure=contact_structure.structure)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    choice_js_cant_pick(
        contact_page.page, "#add-contact-agent-form .choices", contact.agent.nom, contact.display_with_agent_unit
    )


def generic_test_cant_add_contact_structure_if_any_agent_cant_access_domain(
    live_server, page, choice_js_cant_pick, object
):
    contact = ContactAgentFactory(with_active_agent=True)

    page.goto(f"{live_server.url}{object.get_absolute_url()}")
    contact_page = WithContactsPage(page)
    choice_js_cant_pick(
        contact_page.page, "#add-contact-structure-form .choices", contact.agent.nom, contact.display_with_agent_unit
    )
