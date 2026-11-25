import csv
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache, partial
import io
import logging
import re

from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import transaction
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
UPDATABLE_FIELDS = ("espece_id", "numero_identifiant_etablissement", "date_statut_changed")
LOCATION_FIELDS = ("commune", "code_insee", "departement_id", "coordinates")

logger = logging.getLogger(__name__)


class MissingColumnsError(Exception):
    pass


class EmptyFileError(Exception):
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


@cache
def _get_departements():
    return {str(d.numero): d.pk for d in Departement.objects.all()}


@cache
def _get_geo_data_from_insee_code(insee_code):
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


def _parse_row(row, especes, maladies, user, previous):
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

    # As the event number depends on the maladie, it cannot change once the event exists
    if previous and previous.maladie_id != maladie.pk:
        return None

    if previous and previous.code_insee == code_insee:
        geo_data = {"code_insee": code_insee}
    else:
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


def _apply_changes(evenement, parsed):
    fields = UPDATABLE_FIELDS
    if parsed.code_insee != evenement.code_insee:
        fields = (*UPDATABLE_FIELDS, *LOCATION_FIELDS)
    changed_fields = [f for f in fields if getattr(evenement, f) != getattr(parsed, f)]
    for f in changed_fields:
        setattr(evenement, f, getattr(parsed, f))
    return changed_fields


def _run(operation, evenement):
    try:
        with transaction.atomic():
            operation()
    except Exception as e:
        logger.warning(f"Could not import row {evenement.import_id}: {e}")
        return False
    return True


@dataclass
class ImportPlan:
    read: int = 0
    invalid: int = 0
    duplicates: int = 0
    unchanged: int = 0
    skipped_deletions: int = 0
    to_create: list = field(default_factory=list)
    to_update: list = field(default_factory=list)
    to_delete: list = field(default_factory=list)

    def summary(self):
        return {
            "read": self.read,
            "to_create": len(self.to_create),
            "to_update": len(self.to_update),
            "unchanged": self.unchanged,
            "to_delete": len(self.to_delete),
            "ignored": self.invalid + self.duplicates,
            "skipped_deletions": self.skipped_deletions,
        }

    def apply(self, csv_import, user):
        result = {"created": 0, "updated": 0, "unchanged": self.unchanged, "deleted": 0, "errors": 0}
        for evenement in self.to_create:
            evenement.csv_import = csv_import
            result["created" if _run(evenement.save, evenement) else "errors"] += 1
        for evenement, changed_fields in self.to_update:
            done = _run(partial(evenement.save, update_fields=changed_fields), evenement)
            result["updated" if done else "errors"] += 1
        for evenement in self.to_delete:
            result["deleted" if _run(partial(evenement.soft_delete, user), evenement) else "errors"] += 1
        return result


def _get_previously_imported_evenements(structure, file_name):
    evenements = EvenementAnimal.objects.filter(csv_import__createur=structure, csv_import__nom_fichier=file_name)
    return {evenement.import_id.lower(): evenement for evenement in evenements}


def parse_csv(file, user):
    content = file.read().decode(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    if not reader.fieldnames:
        raise EmptyFileError
    if missing := [column for column in MANDATORY_COLUMNS if column not in reader.fieldnames]:
        raise MissingColumnsError(", ".join(missing))

    previously_imported = _get_previously_imported_evenements(user.agent.structure, file.name)
    especes = _especes_by_name()
    maladies = _maladies_by_name()
    plan, seen_identifiants = ImportPlan(), set()

    for raw_row in reader:
        plan.read += 1
        cleaned_row = {column: raw_row[column].strip() for column in MANDATORY_COLUMNS}
        identifiant = cleaned_row[ID_COLUMN].lower()
        if identifiant in seen_identifiants:
            plan.duplicates += 1
            continue

        previous = previously_imported.get(identifiant)
        evenement = _parse_row(cleaned_row, especes, maladies, user, previous)
        if not evenement:
            plan.invalid += 1
            continue
        seen_identifiants.add(identifiant)

        if not previous:
            plan.to_create.append(evenement)
        elif changed_fields := _apply_changes(previous, evenement):
            plan.to_update.append((previous, changed_fields))
        else:
            plan.unchanged += 1

    if not plan.read:
        raise EmptyFileError

    absent = [
        evenement for identifiant, evenement in previously_imported.items() if identifiant not in seen_identifiants
    ]
    # An invalid row may belong to an evenement that is still followed, so nothing is deleted in that case
    if plan.invalid:
        plan.skipped_deletions = len(absent)
    else:
        plan.to_delete = absent
    return plan
