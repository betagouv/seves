from abc import ABC, abstractmethod

from playwright.sync_api import Page, expect


class BaseMessagePage(ABC):
    TITLE_ID = "#id_title"
    CONTENT_ID = "#id_content"
    DRAFT_BTN_TEST_ID = "draft-fildesuivi-add-submit"
    SUBMIT_BTN_TEST_ID = "fildesuivi-add-submit"

    def __init__(self, page: Page):
        self.page = page

    @property
    @abstractmethod
    def container_id(self):
        return ""

    def new_message(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Message").click()

    def pick_recipient(self, contact, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.container_id} label[for="id_recipients"] ~ div.choices',
            contact.nom,
            contact.contact_set.get().display_with_agent_unit,
            use_locator_as_parent_element=True,
        )

    def pick_recipient_structure_only(self, structure, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.container_id} label[for="id_recipients_structures_only"] ~ div.choices',
            structure.libelle,
            structure.libelle,
            use_locator_as_parent_element=True,
        )

    def pick_recipient_copy(self, contact, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.container_id} label[for="id_recipients_copy"] ~ div.choices',
            contact.nom,
            contact.contact_set.get().display_with_agent_unit,
            use_locator_as_parent_element=True,
        )

    def pick_recipient_copy_structure_only(self, structure, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.container_id} label[for="id_recipients_copy_structures_only"] ~ div.choices',
            structure.libelle,
            structure.libelle,
            use_locator_as_parent_element=True,
        )

    @property
    def message_form_title(self):
        return self.page.locator("#message-type-title")

    @property
    def message_title(self):
        return self.page.locator(f"{self.container_id}").locator(f"{self.TITLE_ID}")

    @property
    def message_content(self):
        return self.page.locator(f"{self.container_id} {self.CONTENT_ID}")

    @property
    def submit_button(self):
        return self.page.locator(self.container_id).get_by_test_id(self.SUBMIT_BTN_TEST_ID)

    @property
    def save_as_draft_button(self):
        return self.page.locator(self.container_id).get_by_test_id(self.DRAFT_BTN_TEST_ID)

    def submit_message(self):
        self.submit_button.click()

    def save_as_draft_message(self):
        self.save_as_draft_button.click()

    def message_sender_in_table(self, index=1):
        return self.page.text_content(f"#table-sm-row-key-{index} td:nth-child(2) a")

    def message_recipient_in_table(self, index=1):
        return self.page.text_content(f"#table-sm-row-key-{index} td:nth-child(3) a")

    def message_title_in_table(self, index=1):
        return self.page.text_content(f"#table-sm-row-key-{index} td:nth-child(4) a")

    def message_type_in_table(self, index=1):
        return self.page.text_content(f"#table-sm-row-key-{index} td:nth-child(6) a")

    def open_message(self, index=1):
        self.page.locator(f"#table-sm-row-key-{index} td:nth-child(6) a").click()

    @property
    def message_title_in_sidebar(self):
        return self.page.locator(".sidebar.open h5")

    @property
    def message_content_in_sidebar(self):
        return self.page.locator(".sidebar.open").get_by_test_id("message-content")

    @property
    def add_document_button(self):
        return self.page.get_by_role("button", name="Ajouter un document")

    @property
    def document_type_input(self):
        return self.page.locator(".sidebar #id_document_type")


class CreateMessagePage(BaseMessagePage):
    container_id = "#sidebar"


class UpdateMessagePage(BaseMessagePage):
    def __init__(self, page: Page, message_id: int):
        super().__init__(page)
        self.message_id = message_id

    @property
    def container_id(self) -> str:
        return f"#sidebar-message-{self.message_id}"


class WithDocumentsPage:
    def __init__(self, page: Page):
        self.page = page

    def open_document_tab(self):
        self.page.get_by_test_id("documents").click()

    def document_title(self, id):
        return self.page.get_by_test_id(f"document-title-{id}")

    def open_add_document(self):
        self.page.get_by_test_id("documents-add").click()
        expect(self.page.locator("#fr-modal-add-doc")).to_be_visible()

    @property
    def add_document_types(self):
        return self.page.locator(".fr-modal__body").locator("visible=true").locator("#id_document_type")

    def open_edit_document(self, id):
        self.page.locator(f'a[aria-controls="fr-modal-edit-{id}"]').click()
        expect(self.page.locator(f"#fr-modal-edit-{id}")).to_be_visible()

    def document_edit_title(self, id):
        return self.page.locator(f"#fr-modal-edit-{id} #id_nom")

    def document_edit_description(self, id):
        return self.page.locator(f"#fr-modal-edit-{id} #id_description")

    def document_edit_save(self, id):
        self.page.get_by_test_id(f"documents-edit-{id}").click()


class WithContactsPage:
    def __init__(self, page: Page):
        self.page = page
        self.go_to_contact_tab()

    def go_to_contact_tab(self):
        self.page.get_by_role("tab", name="Contacts").click()
        self.page.get_by_role("tab", name="Contacts").evaluate("el => el.scrollIntoView()")

    def add_agent(self, choice_js_fill, contact):
        choice_js_fill(
            self.page, "#add-contact-agent-form .choices", contact.agent.nom, contact.display_with_agent_unit
        )
        self.page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    def add_structure(self, choice_js_fill, contact):
        choice_js_fill(self.page, "#add-contact-structure-form .choices", str(contact), str(contact))
        self.page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()
