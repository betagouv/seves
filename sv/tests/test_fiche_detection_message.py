from model_bakery import baker
from playwright.sync_api import Page, expect
from core.models import Message, Contact, Agent, Structure
from ..models import FicheDetection


def test_can_add_and_see_message_without_document(
    live_server, page: Page, fiche_detection: FicheDetection, choice_js_fill
):
    agent = baker.make(Agent)
    baker.make(Contact, agent=agent)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{fiche_detection.add_message_url}")

    choice_js_fill(page, ".choices__input--cloned:first-of-type", agent.nom, str(agent))
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == str(agent)

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Message"

    page.locator(cell_selector).click()
    message = Message.objects.get()
    page.wait_for_url(f"**{message.get_absolute_url()}")

    expect(page.get_by_role("heading", name="Title of the message")).to_be_visible()
    assert "My content <br> with a line return" in page.get_by_test_id("message-content").inner_html()


def test_can_add_and_see_message_multiple_documents(
    live_server, page: Page, fiche_detection: FicheDetection, choice_js_fill
):
    agent = baker.make(Agent)
    baker.make(Contact, agent=agent)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{fiche_detection.add_message_url}")

    choice_js_fill(page, ".choices__input--cloned:first-of-type", agent.nom, str(agent))
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
    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}#tabpanel-messages-panel")

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


def test_can_add_and_see_message_with_multiple_recipients_and_copies(
    live_server, page: Page, fiche_detection: FicheDetection, choice_js_fill
):
    agents = []
    for _ in range(4):
        agent = baker.make(Agent)
        baker.make(Contact, agent=agent)
        agents.append(agent)

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{fiche_detection.add_message_url}")

    # Add multiple recipients
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[0].nom, str(agents[0]))
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[1].nom, str(agents[1]))

    # Add multiples recipients as copy
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[2].nom, str(agents[2]))
    choice_js_fill(page, ".choices__input--cloned:first-of-type", agents[3].nom, str(agents[3]))

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    assert page.url == f"{live_server.url}{fiche_detection.get_absolute_url()}#tabpanel-messages-panel"

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

    # Check that all the recipients / copies were added as contact of the fiche
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("contacts").click()
    for agent in agents:
        expect(page.get_by_text(str(agent), exact=True)).to_be_visible()


def test_can_add_and_see_note_without_document(live_server, page: Page, fiche_detection: FicheDetection):
    agent = baker.make(Agent)
    baker.make(Contact, agent=agent)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Note").click()

    assert page.url == f"{live_server.url}{fiche_detection.add_note_url}"

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    assert page.url == f"{live_server.url}{fiche_detection.get_absolute_url()}#tabpanel-messages-panel"

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


def test_can_add_and_see_compte_rendu(live_server, page: Page, fiche_detection: FicheDetection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    structure = Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS")
    Contact.objects.create(structure=structure, email="bar@example.com")
    structure = Structure.objects.create(niveau1="SAS/SDSPV/BSV", niveau2="SAS/SDSPV/BSV", libelle="BSV")
    Contact.objects.create(structure=structure, email="foo@example.com")
    page.get_by_test_id("element-actions").click()
    page.get_by_test_id("fildesuivi-actions-compte-rendu").click()

    page.wait_for_url(f"**{fiche_detection.add_compte_rendu_url}")
    page.get_by_text("MUS").click()
    page.get_by_text("BSV").click()
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}#tabpanel-messages-panel")

    cell_selector = f"#table-sm-row-key-1 td:nth-child({2}) a"
    assert page.text_content(cell_selector) == "Structure Test"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({3}) a"
    assert page.text_content(cell_selector).strip() == "MUS et 1 autres"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({4}) a"
    assert page.text_content(cell_selector) == "Title of the message"

    cell_selector = f"#table-sm-row-key-1 td:nth-child({6}) a"
    assert page.text_content(cell_selector) == "Compte rendu sur demande d'intervention"


def test_cant_add_compte_rendu_without_recipient(live_server, page: Page, fiche_detection: FicheDetection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    Contact.objects.create(structure=Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS"))
    structure = Structure.objects.create(niveau1="SAS/SDSPV/BSV", niveau2="SAS/SDSPV/BSV", libelle="BSV")
    Contact.objects.create(structure=structure)
    page.get_by_test_id("element-actions").click()
    page.get_by_test_id("fildesuivi-actions-compte-rendu").click()

    page.wait_for_url(f"**{fiche_detection.add_compte_rendu_url}")
    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{fiche_detection.add_compte_rendu_url}")
    expect(page.get_by_text("Au moins un destinataire doit être sélectionné.")).to_be_visible()


def test_cant_click_on_shortcut_when_no_structure(live_server, page: Page, fiche_detection: FicheDetection):
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{fiche_detection.add_message_url}")
    expect(page.get_by_role("link", name="Ajouter toutes les structures de la fiche")).not_to_be_visible()


def test_can_click_on_shortcut_when_fiche_has_structure(live_server, page: Page, fiche_detection: FicheDetection):
    structure = Structure.objects.create(niveau1="MUS", niveau2="MUS", libelle="MUS")
    contact = Contact.objects.create(email="foo@example.com", structure=structure)
    fiche_detection.contacts.add(contact)

    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")

    expect(page.get_by_test_id("fildesuivi-add")).to_be_visible()
    page.get_by_test_id("fildesuivi-add").click()

    page.wait_for_url(f"**{fiche_detection.add_message_url}")
    page.locator(".destinataires-shortcut").click()

    page.locator("#id_title").fill("Title of the message")
    page.locator("#id_content").fill("My content \n with a line return")
    page.get_by_test_id("fildesuivi-add-submit").click()

    page.wait_for_url(f"**{fiche_detection.get_absolute_url()}#tabpanel-messages-panel")

    fiche_detection.refresh_from_db()
    assert fiche_detection.messages.get().recipients.get() == contact
