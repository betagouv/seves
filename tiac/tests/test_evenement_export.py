from playwright.sync_api import Page, expect

from core.factories import UserFactory
from core.models import Export
from tiac.export import TiacExport
from tiac.factories import (
    EvenementSimpleFactory,
    InvestigationTiacFactory,
    RepasSuspectFactory,
    AlimentSuspectFactory,
    AnalyseAlimentaireFactory,
    EtablissementFactory,
)
from tiac.tests.pages import EvenementListPage


def test_export_tiac_performances_scales_on_number_of_evenement_simple(
    live_server, mocked_authentification_user, page: Page, django_assert_num_queries
):
    evenement = EvenementSimpleFactory()
    data = [{"model": "tiac.evenementsimple", "ids": [evenement.id]}]
    task = Export.objects.create(user=UserFactory(), queryset_sequence=data)

    with django_assert_num_queries(11):
        TiacExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True

    evenement_2 = EvenementSimpleFactory()
    evenement_3 = EvenementSimpleFactory()
    data = [{"model": "tiac.evenementsimple", "ids": [evenement.id, evenement_2.id, evenement_3.id]}]
    task = Export.objects.create(user=UserFactory(), queryset_sequence=data)

    with django_assert_num_queries(11):
        TiacExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True


def test_export_tiac_performances_scales_on_number_of_related_objects(
    live_server, mocked_authentification_user, page: Page, django_assert_num_queries
):
    evenement = InvestigationTiacFactory()
    data = [{"model": "tiac.investigationtiac", "ids": [evenement.id]}]
    task = Export.objects.create(user=UserFactory(), queryset_sequence=data)

    with django_assert_num_queries(14):
        TiacExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True

    RepasSuspectFactory(investigation=evenement)
    AlimentSuspectFactory(investigation=evenement, cuisine=True)
    AnalyseAlimentaireFactory(investigation=evenement)
    EtablissementFactory(investigation=evenement)
    task = Export.objects.create(user=UserFactory(), queryset_sequence=data)

    with django_assert_num_queries(16):
        TiacExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True


def test_export_tiac_from_ui(live_server, mocked_authentification_user, page: Page, settings, mailoutbox):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=2)
    InvestigationTiacFactory(numero_annee=2025, numero_evenement=1)
    InvestigationTiacFactory(numero_annee=2024, numero_evenement=1)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_field.fill("2025")
    search_page.submit_search()
    search_page.submit_export()

    expect(search_page.page.get_by_text("Votre demande d'export a bien été enregistrée")).to_be_visible()

    task = Export.objects.get()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8").split("\n")
    assert lines[1].startswith('"T-2025.2",')
    assert lines[2].startswith('"T-2025.1",')
    assert len(lines) == 4

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == "Sèves - Votre export est prêt"
