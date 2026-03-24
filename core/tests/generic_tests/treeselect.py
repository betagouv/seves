from playwright.sync_api import Locator, Page, expect
from waffle.testutils import override_flag

from core.pages import TreeselectPage


@override_flag("new_treeselect", active=True)
def generic_test_basic_behavior(url: str, page: Page, treeselect_container: Locator):
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
    treeselect_page.untick_checkbox("Allergène - composition ou étiquetage", "Allergène - Fruits à coques", "Amande")
    expect(treeselect_page.main_button).to_have_text("Choisir dans la liste")

    # Search correctly filters values and open accordions
    treeselect_page.search("Virus de la gastroentérite aigüe (GEA)")
    expect(page.get_by_text("Allergène - composition ou étiquetage").first).not_to_be_visible()
    expect(page.get_by_text("Virus", exact=True).first).to_be_visible()
    expect(
        page.get_by_text(
            "Virus de la gastroentérite aigüe (GEA) "
            "(Calicivirus, Norovirus, Sapovirus, Rotavirus, Astrovirus, Adénovirus)"
        ).first
    ).to_be_visible()
    expect(page.get_by_text("Virus de la gastroentérite aigüe (GEA) Norovirus").first).to_be_visible()
    expect(page.get_by_text("Virus de la gastroentérite aigüe (GEA) Autres").first).to_be_visible()
    treeselect_page.tick_checkbox("Virus", "Virus de la gastroentérite aigüe (GEA) Autres")
    expect(treeselect_page.main_button).to_have_text("Virus de la gastroentérite aigüe (GEA) Autres")
