from datetime import date

from playwright.sync_api import Page

from sa.models import EvenementAnimal, Import
from sa.models.evenement import StatutEvenement
from sa.tests.factories import EspeceFactory, FCOFactory
from sa.tests.pages import ImportPage

HEADER = "Identifiant unique;Espèce;Maladie;Date de confirmation;Code INSEE commune;N° EDE"


def _csv_file(tmp_path, *lines):
    file = tmp_path / "import.csv"
    file.write_text("\n".join((HEADER, *lines)) + "\n", encoding="utf-8")
    return file


def test_import_analyses_then_creates_evenements_with_one_row_in_error(
    live_server, page: Page, tmp_path, mocked_authentification_user
):
    espece = EspeceFactory(name="Bovin (Bos taurus)")
    maladie = FCOFactory()
    file = _csv_file(
        tmp_path,
        "TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00210939",
        "TEST-SA-2026-0002;bovin;FCO;06/04/2026;59350;00210940",
        f"TEST-SA-2026-0003;bovin;FCO;07/04/2026;59350;{'9' * 300}",
    )

    import_page = ImportPage(page, live_server.url)
    import_page.navigate()
    import_page.analyse(file)

    assert not EvenementAnimal.objects.exists()

    import_page.import_button.click()
    page.wait_for_timeout(500)

    assert sorted(EvenementAnimal.objects.values_list("import_id", flat=True)) == [
        "TEST-SA-2026-0001",
        "TEST-SA-2026-0002",
    ]
    evenement = EvenementAnimal.objects.get(import_id="TEST-SA-2026-0001")
    assert evenement.espece == espece
    assert evenement.maladie == maladie
    assert evenement.numero_identifiant_etablissement == "00210939"
    assert evenement.date_statut_changed == date(2026, 4, 5)
    assert evenement.statut_evenement == StatutEvenement.CONFIRME
    assert evenement.createur == mocked_authentification_user.agent.structure

    csv_import = Import.objects.get()
    assert csv_import.createur == mocked_authentification_user.agent.structure


def test_import_matches_espece_and_maladie_by_full_name(live_server, page: Page, tmp_path):
    espece = EspeceFactory(name="Bovin (Bos taurus)")
    maladie = FCOFactory()
    file = _csv_file(
        tmp_path,
        "TEST-SA-2026-0001;Bovin (Bos taurus);Fièvre catarrhale ovine;05/04/2026;67482;00210939",
        "TEST-SA-2026-0002;BOVIN;fco;06/04/2026;59350;00210940",
    )

    import_page = ImportPage(page, live_server.url)
    import_page.navigate()
    import_page.analyse(file)
    import_page.import_button.click()
    page.wait_for_timeout(500)
    assert EvenementAnimal.objects.filter(espece=espece, maladie=maladie).count() == 2


def test_import_analysis_alone_creates_nothing(live_server, page: Page, tmp_path):
    EspeceFactory(name="Bovin (Bos taurus)")
    FCOFactory()
    file = _csv_file(tmp_path, "TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00210939")

    import_page = ImportPage(page, live_server.url)
    import_page.navigate()
    import_page.analyse(file)

    assert not EvenementAnimal.objects.exists()
    assert not Import.objects.exists()
