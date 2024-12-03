import pytest
from django.core.management import call_command


@pytest.fixture
def mock_csv_data(tmp_path):
    """Fixture pour les données CSV de test"""
    data = """Structure;Autre Colonne
    AC/DAC/DGAL/MUS;;;;;;;;
    AC/DAC/DGAL/MUS;;;;;;;;
    AC/DAC/DGAL/MUS;;;;;;;;
    SD/DRAAF/DRAAF-CENTRE-VAL-DE-LOIRE/SRAL;;;;;;;;
    SD/DRAAF/DRAAF-CENTRE-VAL-DE-LOIRE/SRAL;;;;;;;;
    SD/DRAAF/DRAAF-OCCITANIE/DIRECTION;;;;;;;;
    SD/DRAAF/DRAAF-OCCITANIE/DIRECTION;;;;;;;;
    SD/DRAAF/DRAAF-OCCITANIE/DIRECTION;;;;;;;;
    SD/DRAAF/DRAAF-OCCITANIE/DIRECTION;;;;;;;;
    SD/DAAF/DAAF976/MSI;;;;;;;;
    SD/DAAF/DAAF976/MSI;;;;;;;;
    DDI/DDPP/DDPP17/SSA;;;;;;;;
    DDI/DDPP/DDPP17/SSA;;;;;;;;
    DDI/DDPP/DDPP17/SSA;;;;;;;;
    DDI/DDPP/DDPP17/SSA;;;;;;;;
    DDETSPP;;;;;;;;
    DDETSPP;;;;;;;;
    DDETSPP;;;;;;;;
    AUTRE/SERVICE;;;;;;;;
    AUTRE/SERVICE;;;;;;;;"""
    p = tmp_path / "test.csv"
    p.write_text(data, encoding="utf-8")
    return str(p)


@pytest.mark.parametrize(
    "expected_structures",
    [
        "AC/DAC/DGAL/MUS",
        "SD/DRAAF/DRAAF-CENTRE-VAL-DE-LOIRE/SRAL",
        "SD/DRAAF/DRAAF-OCCITANIE/DIRECTION",
        "SD/DAAF/DAAF976/MSI",
        "DDI/DDPP/DDPP17/SSA",
        "DDETSPP",
    ],
)
def test_extract_allowed_structures_command(mock_csv_data, tmp_path, expected_structures):
    output_path = tmp_path / "allowed_structures.py"
    call_command("get_structures_from_csv_agricoll_export", mock_csv_data, str(output_path))
    with open(output_path, "r") as f:
        content = f.read()
        assert expected_structures in content
        assert content.count(expected_structures) == 1


def test_not_allowed_structures_exclusion(mock_csv_data, tmp_path):
    output_path = tmp_path / "allowed_structures.py"
    call_command("get_structures_from_csv_agricoll_export", mock_csv_data, str(output_path))
    with open(output_path, "r") as f:
        content = f.read()
        assert "AUTRE/SERVICE" not in content
