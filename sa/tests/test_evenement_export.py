from playwright.sync_api import Page, expect

from core.factories import ContactAgentFactory, ContactStructureFactory
from core.models import Export
from sa.export import SaExport
from sa.tests.factories import EvenementAnimalFactory
from sa.tests.pages import EvenementListPage


def test_export_sa_performances_scales_on_number_of_evenement(live_server, page: Page, django_assert_num_queries):
    evenement = EvenementAnimalFactory()
    contact = ContactAgentFactory()
    ContactStructureFactory(structure=contact.agent.structure)
    task = Export.objects.create(user=contact.agent.user, object_ids=[evenement.id])

    with django_assert_num_queries(12):
        SaExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True

    evenement_2 = EvenementAnimalFactory()
    evenement_3 = EvenementAnimalFactory()
    task = Export.objects.create(user=contact.agent.user, object_ids=[evenement.id, evenement_2.id, evenement_3.id])

    with django_assert_num_queries(13):
        SaExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True


def test_export_sa_from_ui(live_server, page: Page, settings, mailoutbox):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    EvenementAnimalFactory(numero_annee=2025, numero_evenement=2)
    EvenementAnimalFactory(numero_annee=2025, numero_evenement=1)
    EvenementAnimalFactory(numero_annee=2024, numero_evenement=1)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    search_page.annee_field.fill("2025")
    search_page.submit_search()
    search_page.submit_export()

    expect(search_page.page.get_by_text("Votre demande d'export a bien été enregistrée")).to_be_visible()

    task = Export.objects.get()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8").split("\n")
    assert len(lines) == 4

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == "[Sèves] Votre export est prêt"


def test_export_sa_shows_modal_when_above_threshold(live_server, page: Page, settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.VOLUMINOUS_EXTRACT_THRESHOLD = 1
    nb_evenements = 2
    EvenementAnimalFactory.create_batch(nb_evenements)
    search_page = EvenementListPage(page, live_server.url)

    search_page.navigate()
    search_page.submit_export(nb_evenements=nb_evenements)
    expect(search_page.page.locator("#fr-modal-extraire-evenements")).to_be_visible()
    search_page.page.get_by_test_id("submit-extract").click()

    expect(search_page.page.get_by_text("Votre demande d'export a bien été enregistrée")).to_be_visible()
    task = Export.objects.get()
    assert task.task_done is True


def test_export_sa_number_of_lines_and_content(live_server, page: Page, django_assert_num_queries):
    evenement_1 = EvenementAnimalFactory()
    # TODO add related object here to test all fields

    evenement_2 = EvenementAnimalFactory()
    # TODO add related object here to test all fields

    evenement_3 = EvenementAnimalFactory()
    # TODO add related object here to test all fields

    evenement_4 = EvenementAnimalFactory()
    # TODO add related object here to test all fields

    contact = ContactAgentFactory()
    ContactStructureFactory(structure=contact.agent.structure)
    task = Export.objects.create(
        user=contact.agent.user, object_ids=[evenement_1.id, evenement_2.id, evenement_3.id, evenement_4.id]
    )

    SaExport().export(task.id)
    task.refresh_from_db()
    assert task.task_done is True

    content = task.file.read().decode("utf-8")
    lines = content.split("\n")
    assert len(lines) == len(
        [
            "Headers",
            "Evenement 1",
            "Evenement 2",
            "Evenement 3",
            "Evenement 4",
            "Blank line",
        ]
    )

    assert lines[5] == ""
    # TODO assert related objects values a row ?
