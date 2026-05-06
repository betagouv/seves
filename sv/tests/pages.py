import typing
from urllib.parse import urlparse

from django.urls import resolve, reverse
from playwright.sync_api import Page, expect

from core.pages import WithActionsPage
from core.tests.pages import ChoiceJSPage, playwright_repeatable

if typing.TYPE_CHECKING:
    from sv.models import ElementInfeste, FicheDetection


class EvenementPage(WithActionsPage):
    def __init__(self, page: Page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, fiche: "FicheDetection| None" = None):
        path = reverse("sv:fiche-detection-creation") if fiche is None else fiche.get_absolute_url()
        return self.page.goto(f"{self.base_url}{path}")


class NewEvenementPage(EvenementPage):
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

    def navigate(self, fiche: "FicheDetection| None" = None):
        return self.page.goto(f"{self.base_url}{reverse('sv:fiche-detection-creation')}")

    def fill_required(self, fiche: "FicheDetection"):
        ChoiceJSPage(
            self.page, self.organisme_nuisible_container, fiche.evenement.organisme_nuisible.libelle_court
        ).try_select_option()
        self.statut_reglementaire.select_option(value=fiche.evenement.statut_reglementaire.libelle)

    def end_with(self, *, action: typing.Literal["save", "cancel"]):
        if action == "save":
            self.action_buttons.get_by_role("button", name="Enregistrer").click()
            self.page.wait_for_url(lambda url: resolve(urlparse(url).path).view_name == "sv:evenement-details")
        else:
            self.action_buttons.get_by_role("button", name="Annuler").click()
            self.page.wait_for_url(lambda url: resolve(urlparse(url).path).view_name == "sv:evenement-liste")


class UpdateEvenementPage(NewEvenementPage):
    def navigate(self, fiche: "FicheDetection| None" = None):
        return self.page.goto(f"{self.base_url}{reverse('sv:fiche-detection-modification', kwargs={'pk': fiche.pk})}")


class ElementsInfestesPage:
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
    def action_buttons(self):
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

    def __init__(self, page: Page):
        self.page = page

    @playwright_repeatable
    def open_new_form(self):
        if self.opened_dialog.count() == 1:
            return

        self.add_button.click()
        expect(self.opened_dialog).to_be_visible()

    def close_with(self, *, action: typing.Literal["save", "cancel"]):
        if action == "save":
            self.action_buttons.get_by_role("button", name="Enregistrer").click()
        else:
            self.action_buttons.get_by_role("button", name="Annuler").click()
        expect(self.dialogs.filter(visible=True)).to_have_count(0)

    def fill_form_and_check(self, element_infeste: "ElementInfeste", *, action: typing.Literal["save", "cancel"]):
        nb_cards_before = self.elements_cards.count()
        self.open_new_form()

        self.fieldset.get_by_label("Type").select_option(label=element_infeste.get_type_display())
        ChoiceJSPage(
            self.page, self.fieldset.get_by_test_id("espece-search"), f"{element_infeste.espece}"
        ).try_select_option()

        if element_infeste.quantite:
            self.fieldset.locator('[name$="quantite"]').fill(element_infeste.quantite)
            self.fieldset.get_by_label(element_infeste.get_quantite_unite_display(), exact=True).check(force=True)

        if element_infeste.comments:
            self.fieldset.locator('[name$="comments"]').fill(element_infeste.comments)

        self.close_with(action=action)

        expected_card_count = nb_cards_before + 1 if action == "save" else nb_cards_before
        expect(self.elements_cards).to_have_count(expected_card_count)

    def action_on_card(self, idx, *, action: typing.Literal["modify", "remove"]):
        card = self.elements_cards.nth(idx)
        if action == "remove":
            card.get_by_role("button", name="Supprimer").click()
            self.opened_deletion_confimation_dialog.get_by_role("button", name="Supprimer").click()
            expect(self.deletion_confimation_dialogs.filter(visible=True)).to_have_count(0)
        else:
            card.get_by_role("button", name="Modifier").click()
            expect(self.opened_dialog).to_be_visible()

    def action_on_last_card(self, *, action: typing.Literal["modify", "remove"]):
        self.action_on_card(self.elements_cards.count() - 1, action=action)
