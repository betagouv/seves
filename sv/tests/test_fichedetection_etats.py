import pytest
from model_bakery import baker
from sv.models import Etat, FicheDetection, Contact
from django.utils.timezone import now, timedelta
from django.core.management import call_command
from playwright.sync_api import Page, expect


@pytest.fixture
def etat_nouveau(db):
    return Etat.objects.get_or_create(libelle="nouveau")[0]


@pytest.fixture
def create_fiche(db):
    return baker.make(FicheDetection, date_creation=now() - timedelta(days=15))


def _add_contacts_to_fiche(fiche_detection, mocked_authentification_user):
    user_contact_agent = Contact.objects.get(agent=mocked_authentification_user.agent)
    user_contact_structure = Contact.objects.get(structure=mocked_authentification_user.agent.structure)
    fiche_detection.contacts.add(user_contact_agent)
    fiche_detection.contacts.add(user_contact_structure)


def test_etat_initial(etat_nouveau):
    """Test que l'état initial d'une fiche est bien 'nouveau' lors de sa création."""
    fiche = baker.make(FicheDetection)
    assert fiche.etat == etat_nouveau


def test_command_updates_fiche_status(create_fiche):
    """Test que la commande update_fichedetection_etat met à jour l'état des fiches à 'en cours'
    si elles ont été créées il y a plus de 15 jours."""
    call_command("update_fichedetection_etat")
    fiche = FicheDetection.objects.first()
    assert fiche.etat.libelle == "en cours"


def test_element_suivi_fin_suivi_creates_etat_fin_suivi(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user
):
    """Test que l'ajout d'un élément de suivi de type 'fin de suivi' ajoute l'état 'fin de suivi'
    à la structure de l'agent connecté sur la fiche concernée."""
    _add_contacts_to_fiche(fiche_detection, mocked_authentification_user)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Fil de suivi").click()
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Signaler la fin de suivi").click()
    page.get_by_label("Message :").fill("test")
    page.get_by_test_id("fildesuivi-add-submit").click()
    page.get_by_test_id("contacts").click()
    expect(page.locator("p").filter(has_text="Fin de suivi")).to_be_visible()


def test_element_suivi_fin_suivi_already_exists(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user
):
    """Test l'impossibilité de créer un élément de suivi de type 'fin de suivi' s'il en existe déjà un pour la structure de l'agent connecté."""
    _add_contacts_to_fiche(fiche_detection, mocked_authentification_user)
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    for _ in range(2):
        page.get_by_role("tab", name="Fil de suivi").click()
        page.get_by_test_id("element-actions").click()
        page.get_by_role("link", name="Signaler la fin de suivi").click()
        page.get_by_label("Message :").fill("test")
        page.get_by_test_id("fildesuivi-add-submit").click()

    expect(page.locator("body")).to_contain_text(
        "Un objet Fin suivi contact avec ces champs Content type, Object id et Contact existe déjà."
    )
    rows = page.locator("table.fil-de-suivi tbody tr")
    expect(rows).to_have_count(1)


def test_cannot_create_fin_suivi_if_structure_not_in_contacts(
    live_server, page: Page, fiche_detection: FicheDetection, mocked_authentification_user
):
    """Test l'impossibilité de créer un élément de suivi de type 'fin de suivi' si la structure de l'agent connecté n'est pas dans les contacts de la fiche."""
    page.goto(f"{live_server.url}{fiche_detection.get_absolute_url()}")
    page.get_by_role("tab", name="Fil de suivi").click()
    page.get_by_test_id("element-actions").click()
    page.get_by_role("link", name="Signaler la fin de suivi").click()
    page.get_by_label("Message :").fill("test")
    page.get_by_test_id("fildesuivi-add-submit").click()
    expect(page.locator("body")).to_contain_text(
        "Vous ne pouvez pas signaler la fin de suivi pour cette fiche car votre structure n'est pas dans la liste des contacts."
    )
    rows = page.locator("table.fil-de-suivi tbody tr")
    expect(rows).to_have_count(0)
