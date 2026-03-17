import abc
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from django.conf import settings
from playwright.sync_api import Locator, Page, expect
import pytest

from core.models import Agent, Structure


class BaseDocumentPage(ABC):
    BASIC_DOCUMENT_NAME = "Mon document"

    def __init__(self, page: Page):
        self.page = page

    @property
    @abc.abstractmethod
    def add_document_button(self):
        pass

    @property
    def document_modal(self):
        return self.page.locator("#document-modal")

    @property
    def global_document_type_input(self):
        return self.page.locator("#document-upload-type-all")

    @property
    def document_type_input(self):
        return self.page.locator('[name$="document_type"]')

    @property
    def get_existing_documents_title(self):
        cards = (
            self.page.get_by_test_id("document-card").get_by_test_id("document-card-title").filter(visible=True).all()
        )

        return [c.inner_text() for c in cards]

    @property
    def modal_submit_btn(self):
        return self.page.locator("#document-modal").get_by_test_id("document-submit-btn")

    def open_document_modal(self):
        if self.document_modal.is_hidden():
            self.page.get_by_test_id("add-document-btn").click()
            expect(self.document_modal).to_be_visible()

    def validate_document_modal(self, *, expect_error=False):
        if self.document_modal.is_visible():
            self.modal_submit_btn.click()
            if expect_error:
                expect(self.document_modal).to_contain_text(
                    "Le formulaire contient des erreurs. Vous pouvez consulter ci-dessous les fichiers problématiques "
                    "(intitulé en rouge) avant de réessayer.",
                    use_inner_text=True,
                )
            else:
                expect(self.document_modal).not_to_be_visible()
        elif expect_error:
            pytest.fail("Modal is expected to generate an error but it is already closed")

    def close_document_modal_no_validate(self):
        if self.document_modal.is_visible():
            self.page.locator("#document-modal").get_by_role("button", name="Fermer").click()
            expect(self.document_modal).not_to_be_visible()

    def set_global_document_type(self, select_option: str):
        self.page.locator("#document-upload-type-all").locator("visible=true").select_option(select_option)

    def set_input_file(self, document: str | Path):
        document = Path(document).resolve()
        self.page.get_by_test_id("filechooser-link").set_input_files(document)
        # There's a bug in Chrome where the event is never dispatched again if the field is not reset
        self.page.get_by_test_id("filechooser-link").set_input_files([])

    def add_basic_document(self, suffix="", *, close=True, document: Path | str | None = None):
        self.open_document_modal()

        # Open file chooser and select file
        self.set_global_document_type("Autre document")

        document = Path(document or settings.BASE_DIR / "static/images/login.jpeg").resolve()
        document_name = document.name
        self.set_input_file(document)

        # Open modification accordion
        accordion = self.page.locator(".fr-accordion", has_text=document_name)
        expect(accordion).to_be_visible()
        accordion.get_by_test_id("open-accordion").click()

        document_name = f"{self.BASIC_DOCUMENT_NAME}{suffix}"
        accordion.locator('[name$="nom"]').fill(document_name)

        # Accordion title changed so we must reselect
        accordion = self.page.locator(".fr-accordion", has_text=document_name)
        accordion.locator('[name$="document_type"]').last.select_option("Autre document")
        accordion.locator('[name$="description"]').last.fill(f"Ma description {suffix}")
        if close:
            self.validate_document_modal()

    def remove_document_by_name_from_modal(self, document_name):
        self.open_document_modal()
        accordions = self.page.get_by_test_id("document-upload").filter(visible=True)
        count = accordions.count()
        accordions.filter(has_text=document_name).get_by_role(role="button", name="Supprimer").click()
        expect(accordions).to_have_count(count - 1)
        self.validate_document_modal()

    @contextmanager
    def modify_document_by_name(self, document_name, *, validate_modal=True) -> Generator[Locator, None, None]:
        accordion = (
            self.page.get_by_test_id("document-upload-title")
            .get_by_text(document_name, exact=True)
            .locator('xpath=./ancestor::*[@data-testid="document-upload"]')
        )
        # Setting a temporary data-testid to resist `nom` field changes
        # language=javascript
        accordion.evaluate('el => el.setAttribute("data-testid", "document-upload-tmp")')
        accordion = self.page.get_by_test_id("document-upload-tmp")
        self.open_document_modal()
        if not accordion.locator('[name$="nom"]').is_visible():
            accordion.get_by_role(role="button", name="Modifier").click()
        expect(accordion.locator('[name$="nom"]')).to_be_visible()
        yield accordion
        accordion.get_by_role(role="button", name="Modifier").click()
        expect(accordion.locator('[name$="nom"]')).not_to_be_visible()
        accordion.evaluate('el => el.setAttribute("data-testid", "document-upload")')
        if validate_modal:
            self.validate_document_modal()


class BaseMessagePage(BaseDocumentPage, ABC):
    TITLE_ID = "#id_title"
    CONTENT_ID = "#id_content"
    DRAFT_BTN_TEST_ID = "draft-fildesuivi-add-submit"
    SUBMIT_BTN_TEST_ID = "fildesuivi-add-submit"

    @property
    @abstractmethod
    def container_id(self):
        return ""

    @property
    def recipients_locator(self):
        return f'{self.container_id} label[for="id_recipients"] ~ div.choices'

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

    def add_basic_message_content(self):
        self.message_title.fill("Title of the message")
        self.message_content.fill("My content \n with a line return")

    def add_basic_message(self, contact, choice_js_fill):
        self.pick_recipient(contact, choice_js_fill)
        expect((self.page.get_by_text("Nouveau message"))).to_be_visible()

        self.add_basic_message_content()

    def remove_document_by_name_from_aside(self, document_name):
        aside_card_list = self.page.get_by_test_id("document-card")
        count = aside_card_list.count()
        aside_card_list.filter(has_text=document_name).get_by_role(role="button", name="Supprimer").click()
        expect(aside_card_list).to_have_count(count - 1)

    @property
    def add_document_button(self):
        return self.page.get_by_role("button", name="Ajouter un document")

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


class WithDocumentsPage(BaseDocumentPage):
    @property
    def container_id(self):
        return "#tabpanel-documents-panel"

    @property
    def add_document_button(self):
        return self.page.get_by_role("button", name="Ajouter des documents")

    def open_document_tab(self):
        if not self.page.locator(self.container_id).is_visible():
            self.page.get_by_test_id("documents").click()
            expect(self.page.locator(self.container_id)).to_be_visible()

    def open_contact_tab(self):
        self.page.get_by_test_id("contacts").click()
        expect(self.page.locator("#tabpanel-contacts-panel")).to_be_visible()

    def open_document_modal(self):
        self.open_document_tab()
        super().open_document_modal()

    def open_edit_document(self, doc_id):
        self.page.locator(f'.fr-btns-group button[aria-controls="fr-modal-edit-{doc_id}"]').click()
        expect(self.page.locator(f"#fr-modal-edit-{doc_id}")).to_be_visible()

    def document_title(self, doc_id):
        return self.page.get_by_test_id(f"document-title-{doc_id}")

    def document_edit_title(self, doc_id):
        return self.page.locator(f"#fr-modal-edit-{doc_id} #id_nom")

    def document_edit_type(self, doc_id):
        return self.page.locator(f"#fr-modal-edit-{doc_id} #id_document_type")

    def document_edit_description(self, doc_id):
        return self.page.locator(f"#fr-modal-edit-{doc_id} #id_description")

    def document_edit_save(self, doc_id):
        self.page.get_by_test_id(f"documents-edit-{doc_id}").click()


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


class TreeselectPage:
    @property
    def treeselect(self):
        return self.container.locator(
            "xpath=descendant-or-self::*[contains(concat(' ',normalize-space(@class),' '),' fr-treeselect ')]"
        ).first

    @property
    def main_button(self):
        return self.treeselect.locator(".fr-treeselect__button").first

    @property
    def main_dropdown(self):
        return self.treeselect.locator(".fr-treeselect__collapse").first

    @property
    def options_container(self):
        return self.treeselect.locator(".fr-treeselect__body").first

    @property
    def search_bar(self):
        return self.treeselect.locator(".fr-treeselect__head .fr-search-bar input").first

    def __init__(self, page: Page, container: Locator):
        self.page = page
        self.container = container

    def open_treeselect(self):
        if self.options_container.is_visible():
            return
        self.main_button.click()
        expect(self.options_container).to_be_visible()

    def close_treeselect(self):
        if not self.options_container.is_visible():
            return
        self.main_button.click()
        expect(self.options_container).not_to_be_visible()

    def _locate_group(self, name: str, container: Locator | None = None):
        container = container or self.container
        group_header = container.locator(".fr-treeselect__group .fr-treeselect__group-header").filter(has_text=name)
        group = group_header.locator("..")
        collapse = group.locator("> .fr-collapse")
        button = group_header.locator(".fr-treeselect__group-button")
        return group, button, collapse

    def open_group(self, name: str, container: Locator | None = None):
        self.open_treeselect()

        group, button, collapse = self._locate_group(name, container)
        if not collapse.is_visible():
            button.click()
            expect(collapse).to_be_visible()

        return group

    def open_groups(self, *names: str) -> Locator:
        group = None
        for name in names:
            group = self.open_group(name, group)
        # If `names` is an empty liste because check box is top-level, just return the main dropdown
        return group or self.main_dropdown

    def close_group(self, name: str, container: Locator | None = None):
        self.open_treeselect()

        group, button, collapse = self._locate_group(name, container)
        if collapse.is_visible():
            button.click()
            expect(collapse).not_to_be_visible()
        return group or self.container

    def tick_checkbox(self, *names: str):
        *groups, checkbox_label = names
        group = self.open_groups(*groups)
        group.get_by_label(checkbox_label, exact=True).set_checked(True, force=True)

    def untick_checkbox(self, *names: str):
        *groups, checkbox_label = names
        group = self.open_groups(*groups)
        group.get_by_label(checkbox_label, exact=True).set_checked(False, force=True)

    def search(self, term):
        self.search_bar.fill(term)
