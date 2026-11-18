from django.urls import reverse
from playwright.sync_api import Page, expect

from sa.models import Import
from sa.tests.factories import MALADIES, EspeceFactory, MaladieFactory, TypageFactory

CSV = """Identifiant unique;Espèce;Maladie;Date de confirmation;Code INSEE commune;N° EDE;Sérotype
TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00210939;2
"""


def test_import_saves_and_analyses_a_csv(live_server, page: Page, tmp_path, mocked_authentification_user):
    EspeceFactory(name="Bovin (Bos taurus)")
    TypageFactory(maladie=MaladieFactory(maladie_ref=MALADIES[4]), valeur_niveau_2="2")
    file = tmp_path / "import.csv"
    file.write_text(CSV, encoding="utf-8")

    page.goto(f"{live_server.url}{reverse('sa:import')}")
    page.get_by_test_id("open-import-modal").click()

    submit = page.get_by_test_id("import-submit-btn")
    expect(submit).to_be_disabled()
    page.get_by_test_id("import-filechooser").set_input_files(file)
    expect(submit).to_be_enabled()
    submit.click()

    expect(page.get_by_test_id("import-eligible-rows")).to_have_text("Lignes éligibles à l'import : 1")
    expect(page.get_by_test_id("import-ignored-rows")).to_have_text("Lignes ignorées : 0")

    csv_import = Import.objects.get()
    assert csv_import.createur == mocked_authentification_user.agent.structure
    assert csv_import.file.read().decode() == CSV
