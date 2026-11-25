import contextlib
from datetime import date
from unittest import mock

from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from playwright.sync_api import Page, expect
import pytest
from requests import HTTPError, ReadTimeout
from reversion.models import Version

from core.models import Departement
from sa.import_csv import _get_departements, _get_geo_data_from_insee_code
from sa.models import EvenementAnimal, Import
from sa.models.evenement import StatutEvenement, TypeLieu
from sa.tests.factories import EspeceFactory, EvenementAnimalFactory, FCOFactory, MaladieFactory
from sa.tests.pages import ImportPage

HEADER = "Identifiant unique;Espèce;Maladie;Date de confirmation;Code INSEE commune;N° EDE"
ROW_1 = "TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00210939"
ROW_2 = "TEST-SA-2026-0002;bovin;FCO;06/04/2026;59350;00210940"

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
def mock_geo_api(timeout_for=()):
    def _get(url, *args, **kwargs):
        code_insee = url.split("/communes/")[1].split("?")[0]
        if code_insee in timeout_for:
            raise ReadTimeout
        response = mock.Mock()
        if code_insee not in COMMUNES:
            response.raise_for_status.side_effect = HTTPError("404 Client Error")
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


def _post_import(client, *lines, action="create", file_name="import.csv"):
    file = SimpleUploadedFile(file_name, ("\n".join((HEADER, *lines)) + "\n").encode())
    return client.post(reverse("sa:import"), {"file": file, "action": action}).json()


def _import_result(created=0, updated=0, unchanged=0, deleted=0, errors=0):
    return {"created": created, "updated": updated, "unchanged": unchanged, "deleted": deleted, "errors": errors}


def _analysis_result(read, to_create=0, to_update=0, unchanged=0, to_delete=0, ignored=0, skipped_deletions=0):
    return {
        "read": read,
        "to_create": to_create,
        "to_update": to_update,
        "unchanged": unchanged,
        "to_delete": to_delete,
        "ignored": ignored,
        "skipped_deletions": skipped_deletions,
    }


@pytest.fixture
def bovin_and_fco():
    return EspeceFactory(name="Bovin (Bos taurus)"), FCOFactory()


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
        expect(import_page.analysis_count("read")).to_have_text("3")
        expect(import_page.analysis_count("to_create")).to_have_text("2")
        expect(import_page.analysis_count("ignored")).to_have_text("1")
        assert not EvenementAnimal.objects.exists()
        import_page.import_button.click()
        expect(import_page.import_result).to_be_visible()
        expect(import_page.import_count("created")).to_have_text("2")
        expect(import_page.import_count("errors")).to_have_text("0")

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
    assert csv_import.nom_fichier == "import.csv"
    assert evenement.csv_import == csv_import


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
        expect(import_page.import_count("created")).to_have_text("2")

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
        expect(import_page.import_count("created")).to_have_text("1")

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
        expect(import_page.import_count("created")).to_have_text("1")

    assert list(EvenementAnimal.objects.values_list("import_id", flat=True)) == ["TEST-SA-2026-0001"]
    assert sorted({call.args[0] for call in mocked_get.call_args_list}) == [
        "https://geo.api.gouv.fr/communes/67482?fields=centre,departement",
        "https://geo.api.gouv.fr/communes/99999?fields=centre,departement",
    ]


def test_reimport_shows_synchronisation_counts_before_and_after_confirmation(live_server, page: Page, tmp_path):
    EspeceFactory(name="Bovin (Bos taurus)")
    FCOFactory()
    import_page = ImportPage(page, live_server.url)

    with mock_geo_api():
        import_page.navigate()
        import_page.analyse(_csv_file(tmp_path, ROW_1, ROW_2))
        import_page.import_button.click()
        expect(import_page.import_count("created")).to_have_text("2")

        file = _csv_file(
            tmp_path,
            "TEST-SA-2026-0001;bovin;FCO;05/04/2026;67482;00999999",
            "TEST-SA-2026-0003;bovin;FCO;07/04/2026;59350;00210941",
            "TEST-SA-2026-0004;bovin;FCO;pas une date;59350;00210942",
        )
        import_page.navigate()
        import_page.analyse(file)
        expect(import_page.analysis_count("read")).to_have_text("3")
        expect(import_page.analysis_count("to_create")).to_have_text("1")
        expect(import_page.analysis_count("to_update")).to_have_text("1")
        expect(import_page.analysis_count("unchanged")).to_have_text("0")
        expect(import_page.analysis_count("to_delete")).to_have_text("0")
        expect(import_page.analysis_count("ignored")).to_have_text("1")
        expect(import_page.skipped_deletions_warning).to_be_visible()

        import_page.import_button.click()
        expect(import_page.import_count("created")).to_have_text("1")
        expect(import_page.import_count("updated")).to_have_text("1")
        expect(import_page.import_count("deleted")).to_have_text("0")

    assert EvenementAnimal.objects.count() == 3


def test_reimport_updates_changed_evenement_and_leaves_identical_one_untouched(client, bovin_and_fco):
    ovin = EspeceFactory(name="Ovin (Ovis aries)")
    changed_row = "TEST-SA-2026-0001;ovin;FCO;08/04/2026;67482;00999999"
    with mock_geo_api():
        _post_import(client, ROW_1, ROW_2)
        first, second = EvenementAnimal.objects.order_by("import_id")

        assert _post_import(client, changed_row, ROW_2, action="test") == _analysis_result(2, to_update=1, unchanged=1)
        assert _post_import(client, changed_row, ROW_2) == _import_result(updated=1, unchanged=1)

    assert EvenementAnimal.objects.count() == 2
    updated = EvenementAnimal.objects.get(pk=first.pk)
    assert updated.numero == first.numero
    assert updated.espece == ovin
    assert updated.date_statut_changed == date(2026, 4, 8)
    assert updated.numero_identifiant_etablissement == "00999999"
    assert Version.objects.get_for_object(updated).count() == 2
    assert Version.objects.get_for_object(second).count() == 1


def test_reimport_overwrites_manual_changes_on_imported_fields_only(client, bovin_and_fco):
    with mock_geo_api() as mocked_get:
        _post_import(client, ROW_1)
        evenement = EvenementAnimal.objects.get()
        evenement.numero_identifiant_etablissement = "MODIFIE"
        evenement.commentaire = "Commentaire saisi dans Sèves"
        evenement.coordinates = Point(7.7, 48.5, srid=4326)
        evenement.save()
        _get_geo_data_from_insee_code.cache_clear()
        mocked_get.reset_mock()

        assert _post_import(client, ROW_1) == _import_result(updated=1)

    evenement.refresh_from_db()
    assert evenement.numero_identifiant_etablissement == "00210939"
    assert evenement.commentaire == "Commentaire saisi dans Sèves"
    assert (evenement.coordinates.x, evenement.coordinates.y) == (7.7, 48.5)
    mocked_get.assert_not_called()


def test_reimport_with_new_insee_code_recomputes_location(client, bovin_and_fco):
    with mock_geo_api():
        _post_import(client, ROW_1)
        evenement = EvenementAnimal.objects.get()
        assert _post_import(client, "TEST-SA-2026-0001;bovin;FCO;05/04/2026;59350;00210939") == _import_result(
            updated=1
        )

    evenement.refresh_from_db()
    assert evenement.code_insee == "59350"
    assert evenement.commune == "Lille"
    assert evenement.departement.numero == "59"
    assert (round(evenement.coordinates.x, 4), round(evenement.coordinates.y, 4)) == (3.0468, 50.6311)
    assert evenement.type_lieu == TypeLieu.FARM


def test_reimport_soft_deletes_absent_evenement_and_creates_a_new_one_if_it_reappears(client, bovin_and_fco):
    with mock_geo_api():
        _post_import(client, ROW_1, ROW_2)
        absent = EvenementAnimal.objects.get(import_id="TEST-SA-2026-0002")
        assert _post_import(client, ROW_1) == _import_result(unchanged=1, deleted=1)

        deleted = EvenementAnimal._base_manager.get(pk=absent.pk)
        assert deleted.is_deleted
        assert deleted.numero == absent.numero
        assert client.get(absent.get_absolute_url()).status_code == 404

        assert _post_import(client, ROW_1, ROW_2) == _import_result(created=1, unchanged=1)

    recreated = EvenementAnimal.objects.get(import_id="TEST-SA-2026-0002")
    assert recreated.numero != absent.numero
    assert EvenementAnimal._base_manager.get(pk=absent.pk).is_deleted


def test_reimport_rejects_maladie_change_on_existing_evenement(client, bovin_and_fco):
    MaladieFactory(name="Maladie hémorragique épizootique", acronym="MHE")
    with mock_geo_api():
        _post_import(client, ROW_1, ROW_2)
        summary = _post_import(client, "TEST-SA-2026-0001;bovin;MHE;05/04/2026;67482;00210939", ROW_2, action="test")

    assert summary == _analysis_result(2, unchanged=1, ignored=1, skipped_deletions=1)


def test_reimport_leaves_evenements_from_other_files_and_manual_ones_untouched(
    client, bovin_and_fco, mocked_authentification_user
):
    with mock_geo_api():
        _post_import(client, ROW_1, file_name="suivi.csv")
        manual = EvenementAnimalFactory(
            createur=mocked_authentification_user.agent.structure, import_id="TEST-SA-2026-0002"
        )

        assert _post_import(client, ROW_1, ROW_2, file_name="suivi-v2.csv") == _import_result(created=2)

    assert EvenementAnimal.objects.count() == 4
    assert (
        EvenementAnimal.objects.get(pk=manual.pk).numero_identifiant_etablissement
        == manual.numero_identifiant_etablissement
    )


def test_file_without_rows_is_rejected(client):
    file = SimpleUploadedFile("import.csv", f"{HEADER}\n".encode())
    response = client.post(reverse("sa:import"), {"file": file, "action": "create"})

    assert response.status_code == 400
    assert response.json() == {"error": "Le fichier ne contient aucune ligne à importer."}
    assert not Import.objects.exists()
