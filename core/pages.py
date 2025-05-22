from playwright.sync_api import Page, expect


class WithMessagePage:
    def __init__(self, page: Page):
        self.page = page

    def new_message(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Message").click()

    def pick_recipient(self, contact, choice_js_fill):
        choice_js_fill(
            self.page,
            'label[for="id_recipients"] ~ div.choices',
            contact.nom,
            contact.contact_set.get().display_with_agent_unit,
            use_locator_as_parent_element=True,
        )

    @property
    def message_form_title(self):
        return self.page.locator("#message-type-title")

    @property
    def message_title(self):
        return self.page.locator("#id_title")

    @property
    def message_content(self):
        return self.page.locator("#id_content")

    def submit_message(self):
        self.page.get_by_test_id("fildesuivi-add-submit").click()

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
