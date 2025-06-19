from django.urls import reverse
from playwright.sync_api import Page, expect

from sv.factories import FicheDetectionFactory, LieuFactory, EvenementFactory


def test_commune_column_with_multiple_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="Marseille")

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("Paris, Lyon, Marseille", exact=True)).to_be_visible()


def test_commune_column_with_some_empty_communes(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="Paris")
    LieuFactory(fiche_detection=fiche, commune="Lyon")
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("Paris, Lyon", exact=True)).to_be_visible()


def test_commune_column_with_empty_commune(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(fiche_detection=fiche, commune="")

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("nc.", exact=True)).to_be_visible()


def test_commune_column_without_lieu(live_server, page: Page):
    FicheDetectionFactory()
    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text("nc.", exact=True)).to_be_visible()


def test_duplicate_commune_appears_only_once(live_server, page: Page):
    fiche = FicheDetectionFactory()
    LieuFactory(commune="La Rochelle", fiche_detection=fiche)
    LieuFactory(commune="La Rochelle", fiche_detection=fiche)
    LieuFactory(commune="Bordeaux", fiche_detection=fiche)

    page.goto(f"{live_server}{reverse('sv:evenement-liste')}")

    expect(page.get_by_text("La Rochelle, Bordeaux", exact=True)).to_be_visible()


def test_list_ordered_by_most_recent_date_derniere_modification(live_server, page: Page):
    fiche_detection_1, fiche_detection_2, fiche_detection_3 = FicheDetectionFactory.create_batch(3)
    fiche_detection_2.commentaire = "commentaire"
    fiche_detection_2.save()
    fiche_detection_1.evenement.numero_europhyt = 12345
    fiche_detection_1.evenement.save()
    fiche_detection_3.commentaire = "un commentaire"
    fiche_detection_3.save()

    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")

    assert (
        page.text_content(".evenements__list-row:nth-child(1) td:nth-child(2)").strip()
        == fiche_detection_3.evenement.numero
    )
    assert (
        page.text_content(".evenements__list-row:nth-child(2) td:nth-child(2)").strip()
        == fiche_detection_1.evenement.numero
    )
    assert (
        page.text_content(".evenements__list-row:nth-child(3) td:nth-child(2)").strip()
        == fiche_detection_2.evenement.numero
    )


def test_compteur_fiche(live_server, page: Page):
    nb_evenements = 101
    EvenementFactory.create_batch(nb_evenements)
    page.goto(f"{live_server.url}{reverse('sv:evenement-liste')}")
    expect(page.get_by_text(f"100 sur un total de {nb_evenements}", exact=True)).to_be_visible()
    page.get_by_role("link", name="Dernière page").click()
    expect(page.get_by_text(f"1 sur un total de {nb_evenements}", exact=True)).to_be_visible()
