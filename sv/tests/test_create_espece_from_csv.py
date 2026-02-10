from django.core.management import call_command
import pytest

from sv.models import EspeceEchantillon


@pytest.mark.django_db
def test_create_espece_from_csv(tmp_path):
    assert EspeceEchantillon.objects.count() == 0

    temp_csv = tmp_path / "test.csv"
    with open(temp_csv, mode="w") as file:
        file.write("vegetalCodeOeppLb;vegetalCourtLb\nABEEN;Abelia engleriana\nABEGR;Abelia graebneriana")

    call_command("create_espece_from_csv", file=str(temp_csv))

    assert EspeceEchantillon.objects.count() == 2
