from playwright.sync_api import Locator, Page, expect
from waffle.testutils import override_flag

from core.pages import TreeselectPage


def generic_test_basic_behavior(url: str, page: Page, treeselect_container: Locator):
    with override_flag("new_treeselect", active=True):
        page.goto(url)
        treeselect_page = TreeselectPage(page, treeselect_container)

        # Check component's label behavior
        expect(treeselect_page.main_button).to_have_text("Choisir dans la liste")
        treeselect_page.tick_checkbox("Allergène - composition ou étiquetage", "Allergène - Fruits à coques", "Amande")
        expect(treeselect_page.main_button).to_have_text("Amande")
        treeselect_page.tick_checkbox("Bactérie", "Brucella", "Brucella abortus")
        expect(treeselect_page.main_button).to_have_text("Amande +1 élément", use_inner_text=True)
        treeselect_page.tick_checkbox("Escherichia Coli")
        expect(treeselect_page.main_button).to_have_text("Amande +2 éléments", use_inner_text=True)

        treeselect_page.untick_checkbox("Escherichia Coli")
        expect(treeselect_page.main_button).to_have_text("Amande +1 élément", use_inner_text=True)
        treeselect_page.untick_checkbox("Bactérie", "Brucella", "Brucella abortus")
        expect(treeselect_page.main_button).to_have_text("Amande")
        treeselect_page.untick_checkbox(
            "Allergène - composition ou étiquetage", "Allergène - Fruits à coques", "Amande"
        )
        expect(treeselect_page.main_button).to_have_text("Choisir dans la liste")
