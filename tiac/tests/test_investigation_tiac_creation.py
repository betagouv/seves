from playwright.sync_api import Page, expect

from tiac.factories import InvestigationTiacFactory
from .pages import InvestigationTiacFormPage
from ..constants import DangersSyndromiques
from ..models import InvestigationTiac


def test_can_create_investigation_tiac_with_required_fields_only(live_server, mocked_authentification_user, page: Page):
    input_data = InvestigationTiacFactory.build()
    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.get()
    assert investigation.createur == mocked_authentification_user.agent.structure
    assert investigation.type_evenement == input_data.type_evenement
    assert investigation.contenu == input_data.contenu
    assert investigation.numero is not None
    assert investigation.is_draft is True

    expect(creation_page.page.get_by_text("L’évènement a été créé avec succès.")).to_be_visible()


def test_can_create_investigation_tiac_with_all_fields(
    live_server, mocked_authentification_user, page: Page, assert_models_are_equal
):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.date_reception.fill(input_data.date_reception.strftime("%Y-%m-%d"))
    creation_page.evenement_origin.select_option(input_data.evenement_origin)
    creation_page.set_modalites_declaration(input_data.modalites_declaration)
    creation_page.set_notify_ars(input_data.notify_ars)
    creation_page.set_will_trigger_inquiry(input_data.will_trigger_inquiry)
    creation_page.numero_sivss.fill(input_data.numero_sivss)

    creation_page.nb_sick_persons.fill(str(input_data.nb_sick_persons))
    creation_page.nb_sick_persons_to_hospital.fill(str(input_data.nb_sick_persons_to_hospital))
    creation_page.nb_dead_persons.fill(str(input_data.nb_dead_persons))
    creation_page.datetime_first_symptoms.fill(input_data.datetime_first_symptoms.strftime("%Y-%m-%dT%H:%M"))
    creation_page.datetime_last_symptoms.fill(input_data.datetime_last_symptoms.strftime("%Y-%m-%dT%H:%M"))
    creation_page.submit_as_draft()

    investigation = InvestigationTiac.objects.last()
    assert_models_are_equal(
        input_data, investigation, to_exclude=["id", "_state", "numero_annee", "numero_evenement", "date_creation"]
    )


def test_can_create_investigation_tiac_etiologie(live_server, mocked_authentification_user, page: Page):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_POISSONS.label)
    assert creation_page.nb_dangers == 1

    creation_page.precisions.fill("Mes précisions")
    creation_page.set_analyses("Oui")
    creation_page.submit_as_draft()
    investigation = InvestigationTiac.objects.last()
    assert investigation.danger_syndromiques_suspectes == ["toxine des poissons"]
    assert investigation.precisions == "Mes précisions"
    assert investigation.analyses_sur_les_malades == "oui"


def test_can_add_and_delete_danger_in_investigation_tiac_etiologie(
    live_server, mocked_authentification_user, page: Page
):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_POISSONS.label)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_COQUILLAGES.label)
    creation_page.add_danger_syndromique(DangersSyndromiques.HISTAMINE.label)
    assert creation_page.nb_dangers == 3

    creation_page.delete_danger_syndromique(1)
    assert creation_page.nb_dangers == 2
    creation_page.submit_as_draft()
    investigation = InvestigationTiac.objects.last()
    assert investigation.danger_syndromiques_suspectes == ["toxine des poissons", "histamine"]


def test_cant_add_same_danger_twice_in_investigation_tiac_etiologie(
    live_server, mocked_authentification_user, page: Page
):
    input_data: InvestigationTiac = InvestigationTiacFactory.build()

    creation_page = InvestigationTiacFormPage(page, live_server.url)
    creation_page.navigate()
    creation_page.fill_required_fields(input_data)
    creation_page.add_danger_syndromique(DangersSyndromiques.TOXINE_DES_POISSONS.label)
    creation_page.open_danger_modal()
    expect(creation_page.find_label_for_danger(DangersSyndromiques.TOXINE_DES_POISSONS.label)).to_be_disabled()
