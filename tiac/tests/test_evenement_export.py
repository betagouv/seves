from playwright.sync_api import Page, expect

from core.factories import ContactAgentFactory, ContactStructureFactory
from core.models import Export, FinSuiviContact
from tiac.constants import SuspicionConclusion
from tiac.export import TiacExport
from tiac.factories import (
    AlimentSuspectFactory,
    AnalyseAlimentaireFactory,
    EtablissementFactory,
    EvenementSimpleFactory,
    InvestigationTiacFactory,
    RepasSuspectFactory,
)
from tiac.tests.pages import EvenementListPage


def test_export_tiac_performances_scales_on_number_of_evenement_simple(
    live_server, mocked_authentification_user, page: Page, django_assert_num_queries
):
    evenement = EvenementSimpleFactory()
    data = [{"model": "tiac.evenementsimple", "ids": [evenement.id]}]
    contact = ContactAgentFactory()
    ContactStructureFactory(structure=contact.agent.structure)
    task = Export.objects.create(user=contact.agent.user, queryset_sequence=data)

    with django_assert_num_queries(14):
        TiacExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True

    evenement_2 = EvenementSimpleFactory()
    evenement_3 = EvenementSimpleFactory()
    data = [{"model": "tiac.evenementsimple", "ids": [evenement.id, evenement_2.id, evenement_3.id]}]
    task = Export.objects.create(user=contact.agent.user, queryset_sequence=data)

    with django_assert_num_queries(14):
        TiacExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True


def test_export_tiac_performances_scales_on_number_of_related_objects(
    live_server, mocked_authentification_user, page: Page, django_assert_num_queries
):
    evenement = InvestigationTiacFactory()
    data = [{"model": "tiac.investigationtiac", "ids": [evenement.id]}]
    contact = ContactAgentFactory()
    ContactStructureFactory(structure=contact.agent.structure)
    task = Export.objects.create(user=contact.agent.user, queryset_sequence=data)

    with django_assert_num_queries(20):
        TiacExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True

    RepasSuspectFactory(investigation=evenement)
    AlimentSuspectFactory(investigation=evenement, cuisine=True)
    AnalyseAlimentaireFactory(investigation=evenement)
    EtablissementFactory(investigation=evenement)
    task = Export.objects.create(user=contact.agent.user, queryset_sequence=data)

    with django_assert_num_queries(24):
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

    search_page.annee_field.fill("2025")
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
    assert mail.subject == "[Sèves] Votre export est prêt"


def test_export_tiac_from_ui_with_only_one_type_of_object_in_filter(
    live_server, mocked_authentification_user, page: Page, settings, mailoutbox
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    EvenementSimpleFactory(numero_annee=2025, numero_evenement=2)
    InvestigationTiacFactory(numero_annee=2025, numero_evenement=1, suspicion_conclusion=SuspicionConclusion.CONFIRMED)
    InvestigationTiacFactory(numero_annee=2024, numero_evenement=1, suspicion_conclusion=SuspicionConclusion.CONFIRMED)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()

    search_page.annee_field.fill("2025")
    search_page.conclusion_field.select_option("TIAC à agent confirmé")
    search_page.submit_search()
    search_page.submit_export()

    expect(search_page.page.get_by_text("Votre demande d'export a bien été enregistrée")).to_be_visible()

    task = Export.objects.get()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8").split("\n")
    assert len(lines) == 3

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == "[Sèves] Votre export est prêt"


def test_export_tiac_from_ui_with_only_investigation_tiac(
    live_server, mocked_authentification_user, page: Page, settings, mailoutbox
):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    InvestigationTiacFactory(numero_annee=2025, numero_evenement=1)
    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.submit_export()

    expect(search_page.page.get_by_text("Votre demande d'export a bien été enregistrée")).to_be_visible()

    task = Export.objects.get()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8").split("\n")
    assert lines[1].startswith('"T-2025.1",')
    assert len(lines) == 3

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == "[Sèves] Votre export est prêt"


def test_export_etat_value_in_fin_de_suivi(live_server, mocked_authentification_user, page: Page, settings, mailoutbox):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    evenement_1 = EvenementSimpleFactory()
    evenement_2 = InvestigationTiacFactory()
    contact = mocked_authentification_user.agent.structure.contact_set.get()
    for evenement in (evenement_1, evenement_2):
        evenement.contacts.add(contact)
        FinSuiviContact.objects.create(
            content_object=evenement,
            contact=contact,
        )

    search_page = EvenementListPage(page, live_server.url)
    search_page.navigate()
    search_page.submit_export()

    expect(search_page.page.get_by_text("Votre demande d'export a bien été enregistrée")).to_be_visible()
    task = Export.objects.get()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8")
    assert lines.count("Fin de suivi pour ma structure") == 2


def test_export_tiac_number_of_lines_and_content(
    live_server, mocked_authentification_user, page: Page, django_assert_num_queries
):
    evenement_1 = InvestigationTiacFactory()
    EtablissementFactory(investigation=evenement_1, raison_sociale="Etablissement 1")
    RepasSuspectFactory(investigation=evenement_1, denomination="Repas 1")
    RepasSuspectFactory(investigation=evenement_1, denomination="Repas 2")

    evenement_2 = InvestigationTiacFactory()
    EtablissementFactory(investigation=evenement_2, raison_sociale="Etablissement 2")
    EtablissementFactory(investigation=evenement_2, raison_sociale="Etablissement 3")

    evenement_3 = EvenementSimpleFactory()
    EtablissementFactory(evenement_simple=evenement_3, raison_sociale="Etablissement 4")

    evenement_4 = EvenementSimpleFactory()

    data = [
        {"model": "tiac.investigationtiac", "ids": [evenement_1.id, evenement_2.id]},
        {"model": "tiac.evenementsimple", "ids": [evenement_3.id, evenement_4.id]},
    ]
    contact = ContactAgentFactory()
    ContactStructureFactory(structure=contact.agent.structure)
    task = Export.objects.create(user=contact.agent.user, queryset_sequence=data)

    TiacExport().export(task.id)
    task.refresh_from_db()
    assert task.task_done is True

    content = task.file.read().decode("utf-8")
    lines = content.split("\n")
    assert len(lines) == len(
        [
            "Headers",
            "Evenement 1 + Etablissement 1 + Repas 1",
            "Evenement 1 + Repas 2",
            "Evenement 2 + Etablissement 2",
            "Evenement 2 + Etablissement 3",
            "Evenement 3 + Etablissement 4",
            "Evenement 4",
            "Blank line",
        ]
    )

    assert lines[7] == ""
    expected_values = ["Etablissement 1", "Etablissement 2", "Etablissement 3", "Etablissement 4", "Repas 1", "Repas 2"]
    for value in expected_values:
        assert value in content
