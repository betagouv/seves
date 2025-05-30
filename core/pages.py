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
    def form_selector(self):
        return ""

    def new_message(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Message").click()

    def pick_recipient(self, contact, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.form_selector} label[for="id_recipients"] ~ div.choices',
            contact.nom,
            contact.contact_set.get().display_with_agent_unit,
            use_locator_as_parent_element=True,
        )

    def pick_recipient_structure_only(self, structure, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.form_selector} label[for="id_recipients_structures_only"] ~ div.choices',
            structure.libelle,
            structure.libelle,
            use_locator_as_parent_element=True,
        )

    def pick_recipient_copy(self, contact, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.form_selector} label[for="id_recipients_copy"] ~ div.choices',
            contact.nom,
            contact.contact_set.get().display_with_agent_unit,
            use_locator_as_parent_element=True,
        )

    def pick_recipient_copy_structure_only(self, structure, choice_js_fill):
        choice_js_fill(
            self.page,
            f'{self.form_selector} label[for="id_recipients_copy_structures_only"] ~ div.choices',
            structure.libelle,
            structure.libelle,
            use_locator_as_parent_element=True,
        )

    @property
    def message_form_title(self):
        return self.page.locator("#message-type-title")

    @property
    @abstractmethod
    def message_title(self):
        pass

    @property
    @abstractmethod
    def message_content(self):
        pass

    @property
    @abstractmethod
    def submit_button(self):
        pass

    @property
    @abstractmethod
    def save_as_draft_button(self):
        pass

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


class CreateMessagePage(BaseMessagePage):
    @property
    def message_title(self):
        return self.page.locator(self.TITLE_ID)

    @property
    def message_content(self):
        return self.page.locator(self.CONTENT_ID)

    @property
    def submit_button(self):
        return self.page.get_by_test_id(self.SUBMIT_BTN_TEST_ID)

    @property
    def save_as_draft_button(self):
        return self.page.locator("#message-add-form").get_by_test_id(self.DRAFT_BTN_TEST_ID)


class UpdateMessagePage(BaseMessagePage):
    def __init__(self, page: Page, message_id: int):
        super().__init__(page)
        self.message_id = message_id

    @property
    def form_selector(self) -> str:
        return f"#sidebar-message-update-form-{self.message_id}"

    @property
    def message_title(self):
        return self.page.locator(f"{self.form_selector}").locator(f"{self.TITLE_ID}")

    @property
    def message_content(self):
        return self.page.locator(f"{self.form_selector} {self.CONTENT_ID}")

    @property
    def submit_button(self):
        return self.page.locator(self.form_selector).get_by_test_id(self.SUBMIT_BTN_TEST_ID)

    @property
    def save_as_draft_button(self):
        return self.page.locator(self.form_selector).get_by_test_id(self.DRAFT_BTN_TEST_ID)


class WithDocumentsPage:
    def __init__(self, page: Page):
        self.page = page

    def open_document_tab(self):
        self.page.get_by_test_id("documents").click()

    def document_title(self, id):
        return self.page.get_by_test_id(f"document-title-{id}")

    def open_edit_document(self, id):
        self.page.locator(f'a[aria-controls="fr-modal-edit-{id}"]').click()
        expect(self.page.locator(f"#fr-modal-edit-{id}")).to_be_visible()

    def document_edit_title(self, id):
        return self.page.locator(f"#fr-modal-edit-{id} #id_nom")

    def document_edit_description(self, id):
        return self.page.locator(f"#fr-modal-edit-{id} #id_description")

    def document_edit_save(self, id):
        self.page.get_by_test_id(f"documents-edit-{id}").click()
