from abc import ABC, abstractmethod
from contextlib import contextmanager

from django.conf import settings
from playwright.sync_api import Page, expect

from core.models import Document, Agent, Structure


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

    @property
    def recipients_locator(self):
        return f'{self.container_id} label[for="id_recipients"] ~ div.choices'

    @property
    def document_modal(self):
        return self.page.locator("#document-modal")

    def new_message(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Message").click()
        self.page.wait_for_url("**/core/message-add/**")

    def delete_message(self):
        self.page.locator("table .fr-icon-delete-bin-line").click()
        self.page.locator(".fr-modal__body").locator("visible=true").get_by_role("button", name="Supprimer").click()

    def new_note(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Note").click()
        self.page.wait_for_timeout(600)

    def new_point_de_situation(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Point de situation").click()
        self.page.wait_for_timeout(600)

    def new_compte_rendu(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Compte rendu sur demande d'intervention").click()
        self.page.wait_for_timeout(600)

    def new_demande_intervention(self):
        self.page.get_by_test_id("element-actions").click()
        self.page.get_by_role("link", name="Demande d'intervention", exact=True).click()
        self.page.wait_for_timeout(600)

    def pick_recipient(self, contact, choice_js_fill):
        if isinstance(contact, Agent):
            choice_js_fill(
                self.page,
                self.recipients_locator,
                contact.nom,
                contact.contact_set.get().display_with_agent_unit,
                use_locator_as_parent_element=True,
            )
        elif isinstance(contact, Structure):
            choice_js_fill(
                self.page,
                self.recipients_locator,
                contact.libelle,
                contact.libelle,
                use_locator_as_parent_element=True,
            )
        else:
            raise NotImplementedError

    def pick_recipient_copy(self, contact, choice_js_fill):
        if isinstance(contact, Agent):
            choice_js_fill(
                self.page,
                f'{self.container_id} label[for="id_recipients_copy"] ~ div.choices',
                contact.nom,
                contact.contact_set.get().display_with_agent_unit,
                use_locator_as_parent_element=True,
            )
        elif isinstance(contact, Structure):
            choice_js_fill(
                self.page,
                f'{self.container_id} label[for="id_recipients_copy"] ~ div.choices',
                contact.libelle,
                contact.libelle,
                use_locator_as_parent_element=True,
            )
        else:
            raise NotImplementedError

    @property
    def message_form_title(self):
        return self.page.locator("h1")

    @property
    def message_title(self):
        return self.page.locator(f"{self.container_id}").locator(f"{self.TITLE_ID}")

    @property
    def message_content(self):
        return self.page.locator(f"{self.CONTENT_ID}")

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

    def open_message(self, index=1) -> Page:
        """Returns the new message page if page was opened in a new tab"""
        link = self.page.locator(f"#table-sm-row-key-{index} td:nth-child(6) a")
        if link.get_attribute("target") == "_blank":
            with self.page.context.expect_page() as new_page_info:
                link.click()
            return new_page_info.value
        else:
            link.click()
            self.page.wait_for_url("**/core/message/**/")
            return self.page

    def open_document_modal(self):
        if self.document_modal.is_hidden():
            self.page.get_by_test_id("add-document-btn").click()
            expect(self.document_modal).to_be_visible()

    def validate_document_modal(self):
        if self.document_modal.is_visible():
            self.page.locator("#document-modal").get_by_test_id("document-submit-btn").click()
            expect(self.document_modal).not_to_be_visible()

    def close_document_modal_no_validate(self):
        if self.document_modal.is_visible():
            self.page.locator("#document-modal").get_by_role("button", name="Fermer").click()
            expect(self.document_modal).not_to_be_visible()

    def delete_document(self, nth):
        document_count = self.page.get_by_test_id("document-card").count()
        self.page.get_by_test_id("document-delete-btn").nth(nth).click()
        # Check that deleting removes file bloc in both message aside and modal
        expect(self.page.get_by_test_id("document-card")).to_have_count(document_count - 1)

    def add_basic_message(self, contact, choice_js_fill):
        self.pick_recipient(contact, choice_js_fill)
        expect((self.page.get_by_text("Nouveau message"))).to_be_visible()

        self.message_title.fill("Title of the message")
        self.message_content.fill("My content \n with a line return")

    def add_basic_document(self, suffix="", close=True):
        self.open_document_modal()

        # Open file chooser and select file
        self.page.locator("#document-upload-type-all").locator("visible=true").select_option("Autre document")

        document_name = "login.jpeg"
        self.page.get_by_test_id("filechooser-link").set_input_files(
            settings.BASE_DIR / "static/images" / document_name
        )
        # There's a bug in Chrome where the event is never dispatched again if the field is not reset
        self.page.get_by_test_id("filechooser-link").set_input_files([])

        # Open modification accordion
        accordion = self.page.locator(f'.fr-accordion:has-text("{document_name}")')
        expect(accordion).to_be_visible()
        accordion.get_by_test_id("open-accordion").click()

        document_name = f"Mon document{suffix}"
        accordion.locator('[name$="nom"]').fill(document_name)

        # Accordion title changed so we must reselect
        accordion = self.page.locator(f'.fr-accordion:has-text("{document_name}")')

        accordion.locator('[name$="document_type"]').last.select_option("Autre document")
        accordion.locator('[name$="description"]').last.fill(f"Ma description {suffix}")
        if close:
            self.validate_document_modal()

    def remove_document_by_name_from_aside(self, document_name):
        aside_card_list = self.page.get_by_test_id("document-card")
        count = aside_card_list.count()
        aside_card_list.filter(has_text=document_name).get_by_role(role="button", name="Supprimer").click()
        expect(aside_card_list).to_have_count(count - 1)

    def remove_document_by_name_from_modal(self, document_name):
        self.open_document_modal()
        accordions = self.page.get_by_test_id("document-upload").filter(visible=True)
        count = accordions.count()
        accordions.filter(has_text=document_name).get_by_role(role="button", name="Supprimer").click()
        expect(accordions).to_have_count(count - 1)
        self.validate_document_modal()

    @contextmanager
    def modify_document_by_name(self, document_name):
        accordion = self.page.get_by_test_id("document-upload").filter(has_text=document_name)
        self.open_document_modal()
        accordion.get_by_role(role="button", name="Modifier").click()
        expect(accordion.locator('[name$="nom"]')).to_be_visible()
        yield accordion
        accordion.get_by_role(role="button", name="Modifier").click()
        expect(accordion.locator('[name$="nom"]')).not_to_be_visible()
        self.validate_document_modal()

    @property
    def add_document_button(self):
        return self.page.get_by_role("button", name="Ajouter un document")

    @property
    def global_document_type_input(self):
        return self.page.locator("#document-upload-type-all")

    @property
    def document_type_input(self):
        return self.page.locator('[name$="document_type"]')

    @property
    def get_existing_documents_title(self):
        cards = (
            self.page.locator(self.container_id).get_by_test_id("document-card").get_by_test_id("document-card-title")
        )
        texts = [cards.nth(i).inner_text() for i in range(cards.count())]
        return [t for t in texts if t]

    @property
    def recipents_dropdown_items(self):
        return self.page.locator(f"{self.recipients_locator} .choices__item")

    def search_in_message_list(self, query):
        self.page.locator("#id_full_text_search").fill(query)
        self.page.locator(".fr-icon-search-line").click()
        self.page.wait_for_load_state("load")


class CreateMessagePage(BaseMessagePage):
    def __init__(self, page: Page, container_id="#message-form"):
        super().__init__(page)
        self._container_id = container_id

    @property
    def container_id(self):
        return self._container_id


class UpdateMessagePage(BaseMessagePage):
    def __init__(self, page: Page, container_id="#message-form"):
        super().__init__(page)
        self._container_id = container_id

    @property
    def container_id(self) -> str:
        return self._container_id


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
        self.page.locator(f'.fr-btns-group button[aria-controls="fr-modal-edit-{id}"]').click()
        expect(self.page.locator(f"#fr-modal-edit-{id}")).to_be_visible()

    @property
    def document_add_title(self):
        return self.page.locator("#fr-modal-add-doc #id_nom")

    @property
    def document_add_type(self):
        return self.page.locator("#fr-modal-add-doc #id_document_type")

    @property
    def document_add_description(self):
        return self.page.locator("#fr-modal-add-doc #id_description")

    @property
    def document_add_file(self):
        return self.page.locator("#fr-modal-add-doc #id_file")

    def add_document(self):
        self.open_document_tab()
        self.open_add_document()
        self.document_add_title.fill("Name of the document")
        self.document_add_type.select_option(Document.TypeDocument.AUTRE)
        self.document_add_description.fill("Description")
        self.document_add_file.set_input_files(settings.BASE_DIR / "static/images/marianne.png")
        self.page.get_by_test_id("documents-send").click()

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

    def add_agents(self, choice_js_fill, contacts):
        for contact in contacts:
            choice_js_fill(
                self.page, "#add-contact-agent-form .choices", contact.agent.nom, contact.display_with_agent_unit
            )
            self.page.keyboard.press("Escape")
        self.page.locator("#add-contact-agent-form").get_by_role("button", name="Ajouter").click()

    def add_structure(self, choice_js_fill, contact):
        choice_js_fill(self.page, "#add-contact-structure-form .choices", str(contact), str(contact))
        self.page.locator("#add-contact-structure-form").get_by_role("button", name="Ajouter").click()

    def remove_contact(self, contact):
        self.page.locator(f'a[aria-controls="fr-modal-contact-{contact.id}"]').click()
        expect(
            self.page.locator(".fr-modal__body")
            .locator("visible=true")
            .get_by_text(str(contact.agent or contact.structure))
        ).to_be_visible()
        expect(self.page.locator(f"#fr-modal-contact-{contact.id}")).to_be_visible()
        self.page.get_by_test_id(f"contact-delete-{contact.id}").click()
