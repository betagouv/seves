import os
import re
import tempfile

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import Page, expect

from core.factories import ContactAgentFactory, ContactStructureFactory, StructureFactory, DocumentFactory
from core.models import Message, Contact, Structure, Visibilite, Document
from sv.factories import EvenementFactory
from sv.models import Evenement

User = get_user_model()


def test_can_add_and_see_message_without_document(live_server, page: Page, choice_js_fill):
    active_contact = ContactAgentFactory(with_active_agent=True).agent
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        active_contact.nom,
        active_contact.contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    expect(page.locator("#message-type-title")).to_have_text("message")
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == str(active_contact)

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()


def test_can_add_and_see_demande_intervention(live_server, page: Page, choice_js_fill):
    active_contact = ContactStructureFactory(with_one_active_agent=True)
    other_active_contact = ContactStructureFactory(with_one_active_agent=True)
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Demande d'intervention", exact=True).click()

    choice_js_fill(
        page,
        'label[for="id_recipients_structures_only"] ~ div.choices',
        active_contact.display_with_agent_unit,
        active_contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.keyboard.press("Escape")
    choice_js_fill(
        page,
        'label[for="id_recipients_copy_structures_only"] ~ div.choices',
        other_active_contact.display_with_agent_unit,
        other_active_contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    expect(page.locator("#message-type-title")).to_have_text("demande d'intervention")
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == str(active_contact)

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Demande d'intervention"

    page.locator(cell_selector).click()

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()

    message = Message.objects.get()
    assert list(message.recipients.all()) == [
        active_contact,
    ]
    assert list(message.recipients_copy.all()) == [
        other_active_contact,
    ]
    assert message.message_type == Message.DEMANDE_INTERVENTION


def test_can_add_and_see_message_multiple_documents(live_server, page: Page, choice_js_fill):
    active_contact = ContactAgentFactory(with_active_agent=True).agent
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        active_contact.nom,
        active_contact.contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")

    page.get_by_role("button", name="Ajouter un document").click()
    page.locator(".sidebar #id_document_type").select_option("Autre document")
    page.locator(".sidebar #id_file").set_input_files("README.md")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("README.md", exact=True)).to_be_visible()

    page.get_by_role("button", name="Ajouter un document").click()
    page.locator(".sidebar #id_document_type").select_option("Cartographie")
    page.locator(".sidebar #id_file").set_input_files("requirements.in")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("requirements.in", exact=True)).to_be_visible()

    page.get_by_role("button", name="Ajouter un document").click()
    page.locator(".sidebar #id_document_type").select_option("Autre document")
    page.locator(".sidebar #id_file").set_input_files("requirements.txt")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("requirements.txt", exact=True)).to_be_visible()

    # Test to delete the 2nd document to see if the server can handle non-consecutive IDs of inputs
    page.locator("#document_remove_1").click()
    expect(page.get_by_text("requirements.in", exact=True)).not_to_be_visible()

    page.get_by_test_id("fildesuivi-add-submit").click()
    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()

    message = Message.objects.get()
    assert message.documents.count() == 2

    expect(page.get_by_role("link", name="README.md", exact=True)).to_be_visible()
    expect(page.get_by_role("link", name="requirements.txt", exact=True)).to_be_visible()


def test_can_add_and_see_message_with_multiple_recipients_and_copies(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    contacts = ContactAgentFactory.create_batch(4, with_active_agent=True)
    agents = [contact.agent for contact in contacts]

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    # Add multiple recipients
    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        agents[0].nom,
        agents[0].contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        agents[1].nom,
        agents[1].contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )

    page.locator("#message-type-title").click()
    page.wait_for_timeout(500)
    # Add multiples recipients as copy
    choice_js_fill(
        page,
        'label[for="id_recipients_copy"] ~ div.choices',
        agents[2].nom,
        agents[2].contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    choice_js_fill(
        page,
        'label[for="id_recipients_copy"] ~ div.choices',
        agents[3].nom,
        agents[3].contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    assert page.url == f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-messages-panel"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"
    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    cell_content = page.text_content(cell_selector).strip()
    clean_content = " ".join(cell_content.split())
    agent, other = re.split(r" et ", clean_content)
    assert agent.strip() in [str(agent) for agent in agents]
    assert "1 autre" in other

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()

    # Check that all the recipients / copies were added as contact
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("contacts").click()
    for agent in agents:
        expect(page.get_by_label("Contacts").locator("p").filter(has_text=str(agent))).to_be_visible()


def test_can_add_and_see_note_without_document(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Note").click()

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    assert page.url == f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-messages-panel"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == ""

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Note"

    page.locator(cell_selector).click()

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()


def test_can_add_and_see_compte_rendu(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    structure = Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS")
    Contact.objects.create(structure=structure, email="bar@example.com")
    structure = Structure.objects.create(niveau1="SAS/SDSPV/BSV", niveau2="SAS/SDSPV/BSV", libelle="BSV")
    Contact.objects.create(structure=structure, email="foo@example.com")
    page.get_by_test_id("element-actions").click()
    page.get_by_test_id("fildesuivi-actions-compte-rendu").click()

    expect(page.locator("#message-type-title")).to_have_text("compte rendu sur demande d'intervention")
    page.get_by_text("MUS", exact=True).click()
    page.get_by_text("BSV", exact=True).click()
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert " ".join(page.text_content(cell_selector).strip().split()) == "MUS et 1 autre"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Compte rendu sur demande d'intervention"


def test_cant_add_compte_rendu_without_recipient(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    Contact.objects.create(structure=Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS"))
    structure = Structure.objects.create(niveau1="SAS/SDSPV/BSV", niveau2="SAS/SDSPV/BSV", libelle="BSV")
    Contact.objects.create(structure=structure)
    page.get_by_test_id("element-actions").click()
    page.get_by_test_id("fildesuivi-actions-compte-rendu").click()

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    expect(page.get_by_text("Au moins un destinataire doit être sélectionné.")).to_be_visible()


def test_cant_click_on_shortcut_when_no_structure(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    expect(page.get_by_role("link", name="Ajouter toutes les structures de la fiche")).not_to_be_visible()


def test_cant_click_on_shortcut_when_only_our_structure(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementFactory()
    evenement.contacts.add(mocked_authentification_user.agent.structure.contact_set.get())
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    expect(page.get_by_role("link", name="Ajouter toutes les structures de la fiche")).not_to_be_visible()


def test_can_click_on_shortcut_when_evenement_has_structure(live_server, page: Page, mocked_authentification_user):
    evenement = EvenementFactory()
    structure = Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS")
    contact = Contact.objects.create(email="foo@example.com", structure=structure)
    evenement.contacts.add(contact)
    # Test our own structure is never added when using the shortcut
    evenement.contacts.add(mocked_authentification_user.agent.structure.contact_set.get())

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    page.locator(".destinataires-shortcut").locator("visible=true").click()

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    evenement.refresh_from_db()
    assert evenement.messages.get().recipients.get() == contact


def test_formatting_contacts_messages_details_page(live_server, page: Page):
    evenement = EvenementFactory()
    structure = Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS")

    sender = ContactAgentFactory(agent__nom="Reinhardt", agent__prenom="Django", agent__structure=structure)
    evenement.contacts.add(sender)
    contact = ContactAgentFactory(agent__nom="Reinhardt", agent__prenom="Jean", agent__structure=structure)
    evenement.contacts.add(contact)
    message = Message.objects.create(content_object=evenement, sender=sender, title="Minor", content="Swing")
    message.recipients.set([contact])

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_role("cell", name=str(message.title)).click()
    expect(page.locator(".sidebar").get_by_text("De : Reinhardt Django (MUS)")).to_be_visible()
    expect(page.locator(".sidebar").get_by_text("A : Reinhardt Jean (MUS)")).to_be_visible()


def test_cant_pick_inactive_user_in_message(live_server, page: Page, choice_js_cant_pick):
    evenement = EvenementFactory()
    agent = ContactAgentFactory(agent__user__is_active=False).agent

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    choice_js_cant_pick(page, 'label[for="id_recipients"] ~ div.choices', agent.nom, str(agent))


def test_cant_only_pick_structure_with_email(live_server, page: Page, choice_js_fill, choice_js_cant_pick):
    evenement = EvenementFactory()
    ContactStructureFactory(structure__niveau1="FOO", structure__niveau2="FOO", structure__libelle="FOO")
    ContactStructureFactory(structure__niveau1="BAR", structure__niveau2="BAR", structure__libelle="BAR", email="")

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    choice_js_fill(page, 'label[for="id_recipients"] ~ div.choices', "FOO", "FOO", use_locator_as_parent_element=True)
    choice_js_cant_pick(page, 'label[for="id_recipients"] ~ div.choices', "BAR", "BAR")


@pytest.mark.parametrize("message_type, message_label", Message.MESSAGE_TYPE_CHOICES)
def test_cant_add_message_if_evenement_brouillon(client, mocked_authentification_user, message_type, message_label):
    active_contact = ContactAgentFactory(with_active_agent=True).agent
    evenement = EvenementFactory(etat=Evenement.Etat.BROUILLON)

    response = client.post(
        evenement.add_message_url,
        data={
            "sender": Contact.objects.get(agent=mocked_authentification_user.agent).pk,
            "recipients": [active_contact.pk],
            "message_type": message_type,
            "content": "My content \n with a line return",
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_can_see_more_than_4_search_result_in_recipients_and_recipients_copy_field(live_server, page: Page):
    evenement = EvenementFactory()
    nb_structure = 20
    for i in range(nb_structure):
        structure = Structure.objects.create(niveau1=f"Structure {i + 1}", libelle=f"Structure {i + 1}")
        Contact.objects.create(structure=structure, email=f"structure{i}@test.fr")

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    # Test le champ Destinataires
    page.locator('label[for="id_recipients"] ~ div.choices').click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill("Structure")
    for i in range(nb_structure):
        expect(
            page.locator('label[for="id_recipients"] ~ div.choices')
            .locator(".choices__list")
            .get_by_role("option", name=f"Structure {i + 1}", exact=True)
        ).to_be_visible()

    page.locator(".fr-select").first.press("Escape")

    # Test le champ Copie
    page.locator('label[for="id_recipients_copy"] ~ div.choices').click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill("Structure")
    for i in range(nb_structure):
        expect(
            page.locator('label[for="id_recipients_copy"] ~ div.choices')
            .locator(".choices__list")
            .get_by_role("option", name=f"Structure {i + 1}", exact=True)
        ).to_be_visible()


def test_create_message_adds_agent_and_structure_contacts(
    live_server, page: Page, mocked_authentification_user: User, choice_js_fill
):
    """Test que l'ajout d'un message ajoute l'agent à l'origine du message et sa structure comme contacts ainsi que
    l'agent et la structure du destinataire et des copies"""
    evenement = EvenementFactory()

    # Création du contact destinataire
    contact = ContactAgentFactory()
    contact.agent.user.is_active = True
    contact.agent.user.save()
    ContactStructureFactory(structure=contact.agent.structure)

    # Création du contact de copie
    contact_copy = ContactAgentFactory()
    contact_copy.agent.user.is_active = True
    contact_copy.agent.user.save()
    ContactStructureFactory(structure=contact_copy.agent.structure)

    # Ajout d'un message
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    # Ajout du destinataire
    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        contact.agent.nom,
        contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.keyboard.press("Escape")
    # Ajout de la copie
    choice_js_fill(
        page,
        'label[for="id_recipients_copy"] ~ div.choices',
        contact_copy.agent.nom,
        contact_copy.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.keyboard.press("Escape")
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("Message de test")
    page.get_by_test_id("fildesuivi-add-submit").click()

    # Vérification que le message a été créé
    assert evenement.messages.count() == 1
    message = evenement.messages.get()
    assert message.content == "Message de test"
    assert message.message_type == Message.MESSAGE

    # Vérification des contacts dans l'interface
    page.get_by_test_id("contacts").click()

    agents_section = page.locator("[data-testid='contacts-agents']")
    expect(agents_section.get_by_text(str(mocked_authentification_user.agent), exact=True)).to_be_visible()
    expect(agents_section.get_by_text(str(contact.agent), exact=True)).to_be_visible()

    structures_section = page.locator("[data-testid='contacts-structures']")
    sender_structure = str(mocked_authentification_user.agent.structure)
    recipient_structure = str(contact.agent.structure)

    for structure in (sender_structure, recipient_structure):
        expect(structures_section.get_by_text(structure, exact=True)).to_be_visible()

    # Vérification en base de données
    assert evenement.contacts.count() == 6
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).exists()
    assert evenement.contacts.filter(agent=contact.agent).exists()
    assert evenement.contacts.filter(agent=contact_copy.agent).exists()
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).exists()
    assert evenement.contacts.filter(structure=contact.agent.structure).exists()
    assert evenement.contacts.filter(structure=contact_copy.agent.structure).exists()


def test_create_multiple_messages_adds_contacts_once(
    live_server, page: Page, mocked_authentification_user: User, choice_js_fill
):
    """Test que l'ajout de plusieurs messages n'ajoute qu'une fois les contacts"""
    evenement = EvenementFactory()

    # Création du contact destinataire
    contact = ContactAgentFactory()
    contact.agent.user.is_active = True
    contact.agent.user.save()

    # Ajout du premier message
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        contact.agent.nom,
        contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Message 1")
    page.locator("#id_content").fill("Message de test 1")
    page.get_by_test_id("fildesuivi-add-submit").click()

    # Ajout du second message
    page.get_by_test_id("element-actions").click()
    page.locator(".message-actions").get_by_role("link", name="Message", exact=True).click()

    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        contact.agent.nom,
        contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Message 2")
    page.locator("#id_content").fill("Message de test 2")
    page.get_by_test_id("fildesuivi-add-submit").click()

    # Vérification que les deux messages ont été créés
    assert evenement.messages.count() == 2
    for message in evenement.messages.all():
        assert message.message_type == Message.MESSAGE

    # Vérification des contacts dans l'interface
    page.get_by_test_id("contacts").click()

    agents_section = page.locator("[data-testid='contacts-agents']")
    expect(agents_section.get_by_text(str(mocked_authentification_user.agent), exact=True)).to_be_visible()
    expect(agents_section.get_by_text(str(contact.agent), exact=True)).to_be_visible()

    structures_section = page.locator("[data-testid='contacts-structures']")
    expect(
        structures_section.get_by_text(str(mocked_authentification_user.agent.structure), exact=True)
    ).to_be_visible()

    # Vérification en base de données
    assert evenement.contacts.filter(agent=mocked_authentification_user.agent).count() == 1
    assert evenement.contacts.filter(structure=mocked_authentification_user.agent.structure).count() == 1


def test_create_message_from_locale_changes_to_limitee_and_add_structures_in_allowed_structures(
    live_server, page: Page, mocked_authentification_user: User, choice_js_fill
):
    evenement = EvenementFactory(visibilite=Visibilite.LOCALE)

    # Création du contact destinataire
    contact = ContactAgentFactory()
    contact.agent.user.is_active = True
    contact.agent.user.save()
    ContactStructureFactory(structure=contact.agent.structure)

    # Ajout d'un message
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    # Envoi du message
    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        contact.agent.nom,
        contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("Message de test")
    page.get_by_test_id("fildesuivi-add-submit").click()

    evenement.refresh_from_db()
    assert evenement.is_visibilite_limitee is True
    assert len(evenement.allowed_structures.all()) == 2
    assert contact.agent.structure in evenement.allowed_structures.all()
    assert mocked_authentification_user.agent.structure in evenement.allowed_structures.all()


def test_create_message_from_locale_from_same_structure_does_not_changes_visibilite_to_limitee(
    live_server, page: Page, mocked_authentification_user: User, choice_js_fill
):
    evenement = EvenementFactory(visibilite=Visibilite.LOCALE)

    # Création du contact destinataire
    contact = ContactAgentFactory(agent__structure=mocked_authentification_user.agent.structure, with_active_agent=True)

    # Ajout d'un message
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    # Envoi du message
    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        contact.agent.nom,
        contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("Message de test")
    page.get_by_test_id("fildesuivi-add-submit").click()

    evenement.refresh_from_db()
    assert evenement.is_visibilite_locale is True


def test_create_message_from_visibilite_limitee_add_structures_in_allowed_structures(
    live_server, page: Page, mocked_authentification_user: User, choice_js_fill
):
    structure = StructureFactory()
    evenement = EvenementFactory()
    evenement.allowed_structures.set([structure])
    evenement.visibilite = Visibilite.LIMITEE
    evenement.save()

    # Création du contact destinataire
    contact = ContactAgentFactory()
    contact.agent.user.is_active = True
    contact.agent.user.save()
    ContactStructureFactory(structure=contact.agent.structure)

    # Ajout d'un message
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    # Envoi du message
    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        contact.agent.nom,
        contact.display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("Message de test")
    page.get_by_test_id("fildesuivi-add-submit").click()

    # Vérification que le message a été créé
    evenement.refresh_from_db()
    assert evenement.is_visibilite_limitee is True
    assert len(evenement.allowed_structures.all()) == 2
    assert contact.agent.structure in evenement.allowed_structures.all()
    assert mocked_authentification_user.agent.structure in evenement.allowed_structures.all()


@pytest.mark.django_db
def test_cant_forge_post_of_message_in_evenement_we_cant_see(client, mocked_authentification_user):
    evenement = EvenementFactory(createur=Structure.objects.create(libelle="A new structure"))
    response = client.get(evenement.get_absolute_url())
    contact = ContactAgentFactory()
    contact.agent.user.is_active = True
    contact.agent.user.save()

    assert response.status_code == 403
    content_type = ContentType.objects.get_for_model(evenement).id

    payload = {
        "content_type": content_type,
        "object_id": evenement.pk,
        "recipients": contact.pk,
        "title": "Test",
        "content": "Test",
        "message_type": "message",
        "next": "/",
    }
    response = client.post(
        reverse("message-add", kwargs={"obj_type_pk": content_type, "obj_pk": evenement.pk}), data=payload
    )

    assert response.status_code == 403
    evenement.refresh_from_db()
    assert evenement.messages.count() == 0


def test_can_delete_document_attached_to_message(live_server, page: Page, mocked_authentification_user: User):
    evenement = EvenementFactory()
    structure, _ = Structure.objects.get_or_create(niveau1="MUS", niveau2="MUS", libelle="MUS")
    sender = ContactAgentFactory()
    evenement.contacts.add(sender)
    contact = ContactAgentFactory()
    evenement.contacts.add(contact)
    message = Message.objects.create(content_object=evenement, sender=sender, title="Minor", content="Swing")
    message.recipients.set([contact])
    document = DocumentFactory(nom="Test document", description="", content_object=message)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("documents").click()
    expect(page.get_by_role("link", name="Test document")).to_be_visible()

    page.locator(f'a[aria-controls="fr-modal-{document.id}"]').click()
    expect(page.locator(f"#fr-modal-{document.id}")).to_be_visible()
    page.get_by_test_id(f"documents-delete-{document.id}").click()

    page.wait_for_timeout(600)
    document = Document.objects.get()
    assert document.is_deleted is True
    assert document.deleted_by == mocked_authentification_user.agent


def test_message_with_document_exceeding_max_size_shows_validation_error(live_server, page: Page, choice_js_fill):
    active_contact = ContactAgentFactory(with_active_agent=True).agent
    # Créer un fichier temporaire CSV de 16Mo
    file_size = 16 * 1024 * 1024
    fd, temp_path = tempfile.mkstemp(suffix=".csv")
    os.truncate(fd, file_size)
    os.close(fd)

    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()
    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        active_contact.nom,
        active_contact.contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Message avec fichier trop volumineux")
    page.locator("#id_content").fill("Test de validation de taille de fichier")
    page.get_by_role("button", name="Ajouter un document").click()

    file_input = page.locator(".sidebar #id_file")
    max_size_attr = file_input.get_attribute("data-max-size")
    assert int(max_size_attr) == 15 * 1024 * 1024

    page.locator(".sidebar #id_document_type").select_option("Autre document")
    page.locator(".sidebar #id_file").set_input_files(temp_path)

    validation_message = file_input.evaluate("el => el.validationMessage")
    assert "Le fichier est trop volumineux (maximum 15 Mo autorisés)" in validation_message

    page.get_by_test_id("fildesuivi-add-submit").click()

    evenement.refresh_from_db()
    assert evenement.documents.count() == 0
    assert evenement.messages.count() == 0

    os.unlink(temp_path)


def test_can_add_message_with_document_confirmation_modal_reject(live_server, page: Page, choice_js_fill):
    active_contact = ContactAgentFactory(with_active_agent=True).agent
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        active_contact.nom,
        active_contact.contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")

    page.get_by_role("button", name="Ajouter un document").click()
    page.locator(".sidebar #id_document_type").select_option("Autre document")
    page.locator(".sidebar #id_file").set_input_files("README.md")

    page.get_by_test_id("fildesuivi-add-submit").click()
    expect(page.locator("#fr-modal-document-confirmation")).to_be_visible()
    page.locator("#send-without-adding-document").click()
    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")
    message = Message.objects.get()
    assert message.documents.count() == 0


def test_can_add_message_with_document_confirmation_modal_confirm(live_server, page: Page, choice_js_fill):
    active_contact = ContactAgentFactory(with_active_agent=True).agent
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Message").click()

    choice_js_fill(
        page,
        'label[for="id_recipients"] ~ div.choices',
        active_contact.nom,
        active_contact.contact_set.get().display_with_agent_unit,
        use_locator_as_parent_element=True,
    )
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")

    page.get_by_role("button", name="Ajouter un document").click()
    page.locator(".sidebar #id_document_type").select_option("Autre document")
    page.locator(".sidebar #id_file").set_input_files("README.md")

    page.get_by_test_id("fildesuivi-add-submit").click()
    expect(page.locator("#fr-modal-document-confirmation")).to_be_visible()
    page.locator("#send-with-adding-document").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")
    message = Message.objects.get()
    assert message.documents.count() == 1
    expect(page.get_by_role("link", name="README.md", exact=True)).to_be_visible()


def test_can_add_and_see_point_de_situation(live_server, page: Page):
    active_contact = ContactAgentFactory(with_active_agent=True)
    evenement = EvenementFactory()
    evenement.contacts.add(active_contact)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Point de situation").click()

    expect(page.locator("#message-type-title")).to_have_text("point de situation")
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == str(active_contact)

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Point de situation"
