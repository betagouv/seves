import csv
from datetime import datetime
import functools
import io
import re

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.core.exceptions import ValidationError
import requests
from requests import ReadTimeout

from core.mixins import normalize
from core.models import Departement
from sa.models import Espece, EvenementAnimal, Maladie
from sa.models.evenement import StatutAnimal, StatutEvenement, TypeLieu

IMPORTABLE_MALADIE_ACRONYMS = ("FCO", "MHE")
ID_COLUMN = "Identifiant unique"
ESPECE_COLUMN = "Espèce"
MALADIE_COLUMN = "Maladie"
DATE_COLUMN = "Date de confirmation"
INSEE_COLUMN = "Code INSEE commune"
EDE_COLUMN = "N° EDE"
MANDATORY_COLUMNS = (
    ID_COLUMN,
    ESPECE_COLUMN,
    MALADIE_COLUMN,
    DATE_COLUMN,
    INSEE_COLUMN,
    EDE_COLUMN,
)
CODE_INSEE_RE = re.compile(r"^(?:\d{5}|2A\d{3}|2B\d{3})$")
GEO_DATA_CACHE_TIMEOUT = 30 * 24 * 60 * 60


class MissingColumnsError(Exception):
    pass


class UnableToLocateException(Exception):
    pass


def _clean(value):
    return " ".join(normalize(value).split())


def _especes_by_name():
    especes = {}
    for espece in Espece.objects.all():
        especes.setdefault(_clean(espece.name.rsplit("(", 1)[0]), espece)
        especes[_clean(espece.name)] = espece
    return especes


def _maladies_by_name():
    maladies = {}
    for maladie in Maladie.objects.filter(acronym__in=IMPORTABLE_MALADIE_ACRONYMS):
        maladies[_clean(maladie.name)] = maladie
        maladies[_clean(maladie.acronym)] = maladie
    return maladies


@functools.cache
def _get_departements():
    return {str(d.numero): d.pk for d in Departement.objects.all()}


def _fetch_geo_data_from_insee_code(insee_code):
    try:
        response = requests.get(f"{settings.GEO_API_ROOT}/communes/{insee_code}?fields=centre,departement", timeout=8)
    except ReadTimeout:
        raise UnableToLocateException

    try:
        response.raise_for_status()
        response = response.json()
    except Exception:
        # Insee code is not valid, json is not valid, any other error
        raise UnableToLocateException

    departements = _get_departements()

    try:
        data = {
            "commune": response["nom"],
            "code_insee": insee_code,
            "departement_id": departements[response["departement"]["code"]],
            "coordinates": Point(response["centre"]["coordinates"][0], response["centre"]["coordinates"][1], srid=4326),
        }
    except KeyError:
        raise UnableToLocateException

    return data


def _get_geo_data_from_insee_code(insee_code):
    return cache.get_or_set(
        f"sa_import_geo_data_{insee_code}",
        lambda: _fetch_geo_data_from_insee_code(insee_code),
        GEO_DATA_CACHE_TIMEOUT,
    )


def _parse_row(row, especes, maladies, user):
    if not all(row[column] for column in MANDATORY_COLUMNS):
        return None

    code_insee = row[INSEE_COLUMN].upper()
    if not CODE_INSEE_RE.match(code_insee):
        return None

    try:
        date_confirmation = datetime.strptime(row[DATE_COLUMN], "%d/%m/%Y").date()
    except ValueError:
        return None

    espece = especes.get(_clean(row[ESPECE_COLUMN]))
    maladie = maladies.get(_clean(row[MALADIE_COLUMN]))
    if not espece or not maladie:
        return None

    try:
        geo_data = _get_geo_data_from_insee_code(code_insee)
    except UnableToLocateException:
        return None

    fields = {
        "import_id": row[ID_COLUMN],
        "espece": espece,
        "maladie": maladie,
        "statut_animal": StatutAnimal.DETENU,
        "numero_identifiant_etablissement": row[EDE_COLUMN],
        "date_statut_changed": date_confirmation,
        "statut_evenement": StatutEvenement.CONFIRME,
        "createur": user.agent.structure,
        "type_lieu": TypeLieu.FARM,
        **geo_data,
    }
    evenement = EvenementAnimal(**fields)
    try:
        evenement.full_clean(
            exclude=[f.name for f in EvenementAnimal._meta.fields if f.name not in fields],
        )
    except ValidationError:
        return None
    return evenement


def parse_csv(file, user):
    content = file.read().decode(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    if missing := [column for column in MANDATORY_COLUMNS if column not in reader.fieldnames]:
        raise MissingColumnsError(", ".join(missing))

    especes = _especes_by_name()
    maladies = _maladies_by_name()
    evenements, seen_identifiants, ignored, read = [], set(), 0, 0

    for raw_row in reader:
        read += 1
        cleaned_row = {column: raw_row[column].strip() for column in MANDATORY_COLUMNS}
        evenement = _parse_row(cleaned_row, especes, maladies, user)

        if not evenement or evenement.import_id.lower() in seen_identifiants:
            ignored += 1
            continue
        seen_identifiants.add(evenement.import_id.lower())
        evenements.append(evenement)
    return evenements, ignored, read
