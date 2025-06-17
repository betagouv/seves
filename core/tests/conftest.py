import pytest

from core.constants import REGIONS, DEPARTEMENTS
from core.models import Region, Departement


@pytest.fixture(autouse=True)
def create_departement_if_needed(db):
    for nom in REGIONS:
        Region.objects.get_or_create(nom=nom)
    for numero, nom, region_nom in DEPARTEMENTS:
        region = Region.objects.get(nom=region_nom)
        Departement.objects.get_or_create(numero=numero, nom=nom, region=region)
