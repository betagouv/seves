from functools import cached_property
import typing

from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest

from core.pages import WithActionsPage
from core.tests.pages import ChoiceJSPage, playwright_repeatable
from core.tests.utils import to_match_viewname

if typing.TYPE_CHECKING:
    from sv.models import ElementInfeste, FicheDetection


FormCloseAction = typing.Literal["save", "cancel"]


class WithElementsInfestesFormset:
    @property
    def block(self):
        return self.page.get_by_test_id("elements-infestes")

    @property
    def add_button(self):
        return self.block.get_by_test_id("add-element-infeste")

    @property
    def dialogs(self):
        return self.block.get_by_test_id("form-dialog")

    @property
    def opened_dialog(self):
        return self.block.get_by_test_id("form-dialog").filter(visible=True)

    @property
    def fieldset(self):
        return self.opened_dialog.get_by_test_id("fieldset")

    @property
    def dialog_action_buttons(self):
        return self.opened_dialog.get_by_test_id("action-btns")

    @property
    def empty_message(self):
        return self.block.get_by_text("Pas d'élément infesté")

    @property
    def elements_cards(self):
        return self.block.get_by_test_id("element-card").filter(visible=True)

    @property
    def deletion_confimation_dialogs(self):
        return self.block.get_by_test_id("deletion-confirmation")

    @property
    def opened_deletion_confimation_dialog(self):
        return self.deletion_confimation_dialogs.filter(visible=True)

    @playwright_repeatable
    def open_new_form(self):
        if self.opened_dialog.count() == 1:
            return

        self.add_button.click()
        expect(self.opened_dialog).to_be_visible()

    def close_with(self, *, action: FormCloseAction):
        if action == "save":
            self.dialog_action_buttons.get_by_role("button", name="Enregistrer").click()
        else:
            self.dialog_action_buttons.get_by_role("button", name="Annuler").click()
        expect(self.dialogs.filter(visible=True)).to_have_count(0)

    def fill_new_form_and_check(self, element_infeste: "ElementInfeste", *, action: FormCloseAction):
        nb_cards_before = self.elements_cards.count()
        self.open_new_form()
        self.fill_form_and_check(element_infeste, action=action)
        expected_card_count = nb_cards_before + 1 if action == "save" else nb_cards_before
        expect(self.elements_cards).to_have_count(expected_card_count)

    def fill_form_and_check(self, element_infeste: "ElementInfeste", *, action: FormCloseAction):
        self.fieldset.get_by_label("Type").select_option(label=element_infeste.get_type_display())

        if element_infeste.espece:
            ChoiceJSPage(
                self.page, self.fieldset.get_by_test_id("espece-search").filter(visible=True)
            ).try_select_option(f"{element_infeste.espece}")

        if element_infeste.quantite:
            self.fieldset.locator('[name$="quantite"]').fill(f"{element_infeste.quantite}")
            self.fieldset.get_by_label(element_infeste.get_quantite_unite_display(), exact=True).check(force=True)

        if element_infeste.comments:
            self.fieldset.locator('[name$="comments"]').fill(element_infeste.comments)

        self.close_with(action=action)

    def remove_card(self, idx):
        self.elements_cards.nth(idx).get_by_role("button", name="Supprimer").click()
        self.opened_deletion_confimation_dialog.get_by_role("button", name="Supprimer").click()
        expect(self.deletion_confimation_dialogs.filter(visible=True)).to_have_count(0)

    def remove_last_card(self):
        self.remove_card(self.elements_cards.count() - 1)

    def edit_card(self, idx, new_data: "ElementInfeste", close_with_action: FormCloseAction = "save"):
        if self.opened_dialog.count() > 0:
            pytest.fail(f"Can't edit element {idx} because a dialog is already opened")

        self.elements_cards.nth(idx).get_by_role("button", name="Modifier").click()
        expect(self.opened_dialog).to_be_visible()
        self.fill_form_and_check(new_data, action=close_with_action)


class EvenementPage(WithActionsPage):
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, object):
        return self.page.goto(f"{self.base_url}{object.get_absolute_url()}")


class EvenementCreationPage(WithElementsInfestesFormset):
    @property
    def action_buttons(self):
        return self.page.get_by_test_id("fiche-action-btns")

    @property
    def fiche_fieldset(self):
        return self.page.get_by_test_id("fiche-detection")

    @property
    def organisme_nuisible_container(self):
        return self.page.locator("#organisme-nuisible")

    @property
    def statut_reglementaire(self):
        return self.fiche_fieldset.get_by_label("Statut réglementaire")

    @cached_property
    def choice_js_page(self):
        return ChoiceJSPage(self.page, self.organisme_nuisible_container)

    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self):
        return self.page.goto(f"{self.base_url}{reverse('sv:fiche-detection-creation')}")

    def fill_required(self, fiche: "FicheDetection"):
        self.choice_js_page.try_select_option(fiche.evenement.organisme_nuisible.libelle_court)
        self.statut_reglementaire.select_option(value=fiche.evenement.statut_reglementaire.libelle)

    def save(self):
        self.action_buttons.get_by_role("button", name="Enregistrer").click()
        self.page.wait_for_url(to_match_viewname("sv:evenement-details"))


class EvenementUpdatePage(EvenementCreationPage):
    def navigate(self, fiche: "FicheDetection"):
        return self.page.goto(f"{self.base_url}{reverse('sv:fiche-detection-modification', kwargs={'pk': fiche.pk})}")
