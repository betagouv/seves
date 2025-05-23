from playwright.sync_api import Page, expect


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
