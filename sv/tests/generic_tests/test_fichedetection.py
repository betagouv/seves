from playwright.sync_api import expect

from sv.models import FicheDetection, Prelevement
from sv.tests.pages import EvenementCreationPage
from sv.tests.test_utils import LieuFormDomElements, PrelevementFormDomElements


def generic_test_cant_delete_lieu_with_associated_prelevement(
    prelevement: Prelevement, evenement_page: EvenementCreationPage
):
    """
    Teste qu'un lieu dont un prélèvement dépend ne peut pas être supprimé mais qu'il peut l'être une fois le
    prélèvement supprimé.
    """
    prelevement_form_elements = PrelevementFormDomElements(evenement_page.page)
    lieu_form_elements = LieuFormDomElements(evenement_page.page)

    # Try delete lieux with prelevement
    lieu_form_elements.get_element_card_remove_button(by_name=prelevement.lieu.nom).click()
    remove_impossible_modale = evenement_page.page.get_by_text("Suppression du lieu impossible")
    expect(remove_impossible_modale).to_be_visible()
    evenement_page.page.keyboard.press("Escape")
    expect(remove_impossible_modale).not_to_be_visible()

    # Remove prelevements then lieux
    while prelevement_form_elements.elements_cards.count() > 0:
        prelevement_form_elements.remove_card(0)

    while lieu_form_elements.elements_cards.count() > 0:
        lieu_form_elements.remove_card(by_idx=0)

    evenement_page.save()

    fiche_detection = FicheDetection.objects.get()
    assert fiche_detection.lieux.count() == 0
