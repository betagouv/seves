import contextlib
from datetime import date
from unittest import mock

from playwright.sync_api import Page, expect
import pytest
from requests import HTTPError, ReadTimeout

from core.models import Departement
from sa.import_csv import _get_departements, _get_geo_data_from_insee_code
from sa.models import EvenementAnimal, Import
from sa.models.evenement import StatutEvenement
from sa.tests.factories import EspeceFactory, FCOFactory
from sa.tests.pages import ImportPage

HEADER = "Identifiant unique;Espèce;Maladie;Date de confirmation;Code INSEE commune;N° EDE"

COMMUNES = {
    "67482": {
        "nom": "Strasbourg",
        "centre": {"type": "Point", "coordinates": [7.7521, 48.5734]},
        "departement": {"code": "67", "nom": "Bas-Rhin"},
    },
    "59350": {
        "nom": "Lille",
        "centre": {"type": "Point", "coordinates": [3.0468, 50.6311]},
        "departement": {"code": "59", "nom": "Nord"},
    },
}


@pytest.fixture(autouse=True)
def clear_geo_api_caches():
    for cached in (_get_geo_data_from_insee_code, _get_departements):
        cached.cache_clear()
    yield
    for cached in (_get_geo_data_from_insee_code, _get_departements):
        cached.cache_clear()


@pytest.fixture(autouse=True)
def departements(ensure_departements):
    return ensure_departements("Bas-Rhin", "Nord")


def _departements_by_numero():
    return {str(d.numero): d.pk for d in Departement.objects.all()}


@contextlib.contextmanager
def mock_geo_api(timeout_for=(), not_found_for=()):
    def _get(url, *args, **kwargs):
        code_insee = url.split("/communes/")[1].split("?")[0]
        if code_insee in timeout_for:
            raise ReadTimeout
        response = mock.Mock()
        if code_insee in not_found_for or code_insee not in COMMUNES:
            response.status_code = 404
            response.json.return_value = {"code": 404, "message": f"Commune {code_insee} introuvable"}
            response.raise_for_status.side_effect = HTTPError("404 Client Error", response=response)
            return response
        response.json.return_value = COMMUNES[code_insee]
        return response

    with (
        mock.patch("sa.import_csv._get_departements", _departements_by_numero),
        mock.patch("sa.import_csv.requests.get", side_effect=_get) as mocked_get,
    ):
        yield mocked_get


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

    with mock_geo_api() as mocked_get:
        import_page.analyse(file)
        assert not EvenementAnimal.objects.exists()
        import_page.import_button.click()
        expect(import_page.import_result).to_be_visible()
        expect(import_page.done_count).to_have_text("2")
        expect(import_page.error_count).to_have_text("0")

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
    assert evenement.commune == "Strasbourg"
    assert evenement.code_insee == "67482"
    assert evenement.departement.numero == "67"
    assert (round(evenement.coordinates.x, 4), round(evenement.coordinates.y, 4)) == (7.7521, 48.5734)
    assert mocked_get.call_count == 2

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

    with mock_geo_api():
        import_page.analyse(file)
        import_page.import_button.click()
        expect(import_page.import_result).to_be_visible()
        expect(import_page.done_count).to_have_text("2")

    assert EvenementAnimal.objects.filter(espece=espece, maladie=maladie).count() == 2


def test_import_analysis_alone_creates_nothing(live_server, page: Page, tmp_path):
    EspeceFactory(name="Bovin (Bos taurus)")
    FCOFactory()
    file = _csv_file(tmp_path, "TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00210939")

    import_page = ImportPage(page, live_server.url)
    import_page.navigate()

    with mock_geo_api():
        import_page.analyse(file)

    assert not EvenementAnimal.objects.exists()
    assert not Import.objects.exists()


def test_import_ignores_row_when_geo_api_times_out(live_server, page: Page, tmp_path):
    EspeceFactory(name="Bovin (Bos taurus)")
    FCOFactory()
    file = _csv_file(
        tmp_path,
        "TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00210939",
        "TEST-SA-2026-0002;bovin;FCO;06/04/2026;59350;00210940",
    )

    import_page = ImportPage(page, live_server.url)
    import_page.navigate()

    with mock_geo_api(timeout_for=("59350",)):
        import_page.analyse(file)
        import_page.import_button.click()
        expect(import_page.import_result).to_be_visible()
        expect(import_page.done_count).to_have_text("1")

    assert list(EvenementAnimal.objects.values_list("import_id", flat=True)) == ["TEST-SA-2026-0001"]


def test_import_ignores_row_with_insee_code_unknown_to_geo_api(live_server, page: Page, tmp_path):
    EspeceFactory(name="Bovin (Bos taurus)")
    FCOFactory()
    file = _csv_file(
        tmp_path,
        "TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00210939",
        "TEST-SA-2026-0002;bovin;FCO;06/04/2026;99999;00210940",
    )

    import_page = ImportPage(page, live_server.url)
    import_page.navigate()

    with mock_geo_api() as mocked_get:
        import_page.analyse(file)
        import_page.import_button.click()
        expect(import_page.import_result).to_be_visible()
        expect(import_page.done_count).to_have_text("1")

    assert list(EvenementAnimal.objects.values_list("import_id", flat=True)) == ["TEST-SA-2026-0001"]
    assert sorted({call.args[0] for call in mocked_get.call_args_list}) == [
        "https://geo.api.gouv.fr/communes/67482?fields=centre,departement",
        "https://geo.api.gouv.fr/communes/99999?fields=centre,departement",
    ]


def test_import_errors_are_visible(live_server, page: Page, tmp_path):
    EspeceFactory(name="Bovin (Bos taurus)")
    FCOFactory()
    file = _csv_file(
        tmp_path,
        ";bovin;FCO;05/04/2026;67482;00210939",
        "TEST-SA-2026-0002;meuh-meuh;FCO;05/04/2026;67482;00210939",
        "TEST-SA-2026-0002;bovin;Tuberculose;06/04/2026;59350;00210940",
        "TEST-SA-2026-0002;bovin;FCO;06/04/226;59350;00210940",
        "TEST-SA-2026-0002;bovin;FCO;06/04/2026;595959;00210940",
        "TEST-SA-2026-0002;bovin;FCO;06/04/2026;59999;00210940",
    )

    import_page = ImportPage(page, live_server.url)
    import_page.navigate()

    expected_rows = [
        [],
        ["1", "", "Identifiant unique", "", "Ce champ est obligatoire."],
        ["2", "TEST-SA-2026-0002", "Espèce", "meuh-meuh", "Espèce non reconnue"],
        [
            "3",
            "TEST-SA-2026-0002",
            "Maladie",
            "Tuberculose",
            "Maladie non reconnue ou non compatible avec l'import CSV (Seules FCO et MHE sont acceptées)",
        ],
        ["4", "TEST-SA-2026-0002", "Date de confirmation", "06/04/226", "Le date n'est pas correctement formatée"],
        ["5", "TEST-SA-2026-0002", "Code INSEE commune", "595959", "Le code insee n'est pas correctement formaté"],
        [
            "6",
            "TEST-SA-2026-0002",
            "Code INSEE commune",
            "59999",
            "Le code insee n'est pas valable ou le service de géolocalisation n'est pas joignable",
        ],
    ]

    with mock_geo_api(not_found_for=("59999",)):
        import_page.analyse(file)
        page.wait_for_timeout(1000)
        texts = []
        for row in page.locator("table tr").all():
            texts.append([t.strip() for t in row.locator("td").all_text_contents()])
        assert not EvenementAnimal.objects.exists()
        assert len(texts) == len(expected_rows)
        for expected in expected_rows:
            assert expected in texts, f"{expected} not found in {texts}"
