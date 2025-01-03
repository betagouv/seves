import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from playwright.sync_api import Page, expect
from core.models import Message, Contact, Agent, Structure, Visibilite
from sv.factories import EvenementFactory

User = get_user_model()


@pytest.fixture
def with_active_contact(tmp_path):
    agent = baker.make(Agent)
    agent.user.is_active = True
    agent.user.save()
    baker.make(Contact, agent=agent)
    return agent


def test_can_add_and_see_message_without_document(live_server, page: Page, with_active_contact, choice_js_fill):
    evenement = EvenementFactory()

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{evenement.add_message_url}")

    choice_js_fill(page, ".choices__input--cloned:first-of-type", with_active_contact.nom, str(with_active_contact))
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == str(with_active_contact)

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()
    message = Message.objects.get()
    page.wait_for_url(f"**{message.get_absolute_url()}")

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()


def test_can_add_and_see_message_multiple_documents(live_server, page: Page, with_active_contact, choice_js_fill):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{evenement.add_message_url}")

    choice_js_fill(page, ".choices__input--cloned:first-of-type", with_active_contact.nom, str(with_active_contact))
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")

    page.locator("#id_document_type").select_option("Autre document")
    page.locator("#id_file").set_input_files("README.md")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("README.md", exact=True)).to_be_visible()

    page.locator("#id_document_type").select_option("Cartographie")
    page.locator("#id_file").set_input_files("requirements.in")
    page.locator("#message-add-document").click()
    expect(page.get_by_text("requirements.in", exact=True)).to_be_visible()

    page.locator("#id_document_type").select_option("Autre document")
    page.locator("#id_file").set_input_files("requirements.txt")
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
    message = Message.objects.get()
    page.wait_for_url(f"**{message.get_absolute_url()}")

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()

    message = Message.objects.get()
    assert message.documents.count() == 2

    expect(page.get_by_text("README.md", exact=True)).to_be_visible()
    expect(page.get_by_text("requirements.txt", exact=True)).to_be_visible()


def test_can_add_and_see_message_with_multiple_recipients_and_copies(live_server, page: Page, choice_js_fill):
    evenement = EvenementFactory()
    agents = []
    for _ in range(4):
        agent = baker.make(Agent)
        agent.user.is_active = True
        agent.user.save()
        baker.make(Contact, agent=agent)
        agents.append(agent)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{evenement.add_message_url}")

    # Add multiple recipients
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[0].nom, str(agents[0]))
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[1].nom, str(agents[1]))

    # Add multiples recipients as copy
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[2].nom, str(agents[2]))
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[3].nom, str(agents[3]))

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    assert page.url == f"{live_server.url}{evenement.get_absolute_url()}#tabpanel-messages-panel"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    cell_content = page.text_content(cell_selector).strip()
    agent, other = cell_content.split(" et ")
    assert agent in [str(agent) for agent in agents]
    assert other == "3 autres"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()
    message = Message.objects.get()
    page.wait_for_url(f"**{message.get_absolute_url()}")

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()

    # Check that all the recipients / copies were added as contact
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("contacts").click()
    for agent in agents:
        expect(page.get_by_text(str(agent), exact=True)).to_be_visible()


def test_can_add_and_see_note_without_document(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Note").click()

    assert page.url == f"{live_server.url}{evenement.add_note_url}"

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
    message = Message.objects.get()
    page.wait_for_url(f"**{message.get_absolute_url()}")

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

    page.wait_for_url(f"**{evenement.add_compte_rendu_url}")
    page.get_by_text("MUS").click()
    page.get_by_text("BSV").click()
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == "MUS et 1 autres"

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

    page.wait_for_url(f"**{evenement.add_compte_rendu_url}")
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.add_compte_rendu_url}")
    expect(page.get_by_text("Au moins un destinataire doit être sélectionné.")).to_be_visible()


def test_cant_click_on_shortcut_when_no_structure(live_server, page: Page):
    evenement = EvenementFactory()
    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{evenement.add_message_url}")
    expect(page.get_by_role("link", name="Ajouter toutes les structures de la fiche")).not_to_be_visible()


def test_can_click_on_shortcut_when_evenement_has_structure(live_server, page: Page):
    evenement = EvenementFactory()
    structure = Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS")
    contact = Contact.objects.create(email="foo@example.com", structure=structure)
    evenement.contacts.add(contact)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")

    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{evenement.add_message_url}")
    page.locator(".destinataires-shortcut").click()

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{evenement.get_absolute_url()}#tabpanel-messages-panel")

    evenement.refresh_from_db()
    assert evenement.messages.get().recipients.get() == contact


def test_formatting_contacts_messages_details_page(live_server, page: Page):
    evenement = EvenementFactory()
    structure = Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS")
    sender = Contact.objects.create(agent=baker.make(Agent, nom="Reinhardt", prenom="Django", structure=structure))
    evenement.contacts.add(sender)
    contact = Contact.objects.create(agent=baker.make(Agent, nom="Reinhardt", prenom="Jean", structure=structure))
    evenement.contacts.add(contact)
    message = Message.objects.create(content_object=evenement, sender=sender, title="Minor", content="Swing")
    message.recipients.set([contact])

    page.goto(f"{live_server.url}{message.get_absolute_url()}")
    expect(page.get_by_text("De : Reinhardt Django (MUS)", exact=True)).to_be_visible()
    expect(page.get_by_text("A : Reinhardt Jean (MUS)", exact=True)).to_be_visible()


def test_cant_pick_inactive_user_in_message(live_server, page: Page, choice_js_cant_pick):
    evenement = EvenementFactory()
    user = baker.make(User, is_active=False)
    agent = baker.make(Agent, user=user)
    baker.make(Contact, agent=agent, structure=None)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{evenement.add_message_url}")

    choice_js_cant_pick(page, ".choices__input--cloned:first-of-type", agent.nom, str(agent))


def test_cant_only_pick_structure_with_email(live_server, page: Page, choice_js_fill, choice_js_cant_pick):
    evenement = EvenementFactory()
    structure_with_email = baker.make(Structure, niveau1="FOO", niveau2="FOO", libelle="FOO")
    baker.make(Contact, agent=None, structure=structure_with_email)

    structure_without_email = baker.make(Structure, niveau1="BAR", niveau2="BAR", libelle="BAR")
    baker.make(Contact, agent=None, email="", structure=structure_without_email)

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{evenement.add_message_url}")

    choice_js_fill(page, ".choices__input--cloned:first-of-type", "FOO", "FOO")
    choice_js_cant_pick(page, ".choices__input--cloned:first-of-type", "BAR", "BAR")


@pytest.mark.parametrize("message_type, message_label", Message.MESSAGE_TYPE_CHOICES)
def test_cant_access_add_message_form_if_evenement_brouillon(client, message_type, message_label):
    evenement = EvenementFactory(visibilite=Visibilite.BROUILLON)

    response = client.get(evenement.get_add_message_url(message_type), follow=True)

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


@pytest.mark.parametrize("message_type, message_label", Message.MESSAGE_TYPE_CHOICES)
def test_cant_add_message_if_evenement_brouillon(
    client, mocked_authentification_user, with_active_contact, message_type, message_label
):
    evenement = EvenementFactory(visibilite=Visibilite.BROUILLON)

    response = client.post(
        evenement.get_add_message_url(message_type),
        data={
            "sender": Contact.objects.get(agent=mocked_authentification_user.agent).pk,
            "recipients": [with_active_contact.pk],
            "message_type": message_type,
            "content": "My content \n with a line return",
        },
        follow=True,
    )

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


@pytest.mark.parametrize("message_type, message_label", Message.MESSAGE_TYPE_CHOICES)
def test_cant_access_message_details_if_evenement_brouillon(
    client, mocked_authentification_user, with_active_contact, message_type, message_label
):
    evenement = EvenementFactory(visibilite=Visibilite.BROUILLON)
    message = Message.objects.create(
        message_type=message_type,
        title="un titre",
        content="un contenu",
        sender=Contact.objects.get(agent=mocked_authentification_user.agent),
        content_object=evenement,
    )
    recipient_contact = Contact.objects.get(agent=with_active_contact)
    message.recipients.set([recipient_contact])

    response = client.get(message.get_absolute_url(), follow=True)

    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert messages[0].level_tag == "error"
    assert str(messages[0]) == "Action impossible car la fiche est en brouillon"


def test_can_see_more_than_4_search_result_in_recipients_and_recipients_copy_field(live_server, page: Page):
    evenement = EvenementFactory()
    nb_structure = 20
    for i in range(nb_structure):
        structure = Structure.objects.create(niveau1=f"Structure {i+1}", libelle=f"Structure {i+1}")
        Contact.objects.create(structure=structure, email=f"structure{i}@test.fr")

    page.goto(f"{live_server.url}{evenement.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()
    page.wait_for_url(f"**{evenement.add_message_url}")

    # Test le champ Destinataires
    page.locator(".choices__input--cloned:first-of-type").nth(0).click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill("Structure")
    for i in range(nb_structure):
        expect(page.get_by_role("option", name=f"Structure {i + 1}", exact=True)).to_be_visible()

    page.locator(".fr-select").first.press("Escape")

    # Test le champ Copie
    page.locator(".choices__input--cloned:first-of-type").nth(1).click()
    page.wait_for_selector("input:focus", state="visible", timeout=2_000)
    page.locator("*:focus").fill("Structure")
    for i in range(nb_structure):
        expect(page.get_by_role("option", name=f"Structure {i + 1}", exact=True)).to_be_visible()
