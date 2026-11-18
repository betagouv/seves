"""Lecture et validation du fichier CSV d'import d'événements de santé animale."""

import csv
from datetime import datetime
import io
import re

from core.mixins import normalize
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
EXPECTED_COLUMNS = (*MANDATORY_COLUMNS, "Sérotype")
CODE_INSEE_RE = re.compile(r"^(?:\d{5}|2A\d{3}|2B\d{3})$")


class MissingColumnsError(Exception):
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


def _parse_row(row, especes, maladies):
    if not all(row[column] for column in MANDATORY_COLUMNS):
        return None

    code_insee = row[INSEE_COLUMN].upper()
    if not CODE_INSEE_RE.match(code_insee):
        return None

    try:
        date_confirmation = datetime.strptime(row[DATE_COLUMN].strip(), "%d/%m/%Y").date()
    except ValueError:
        return None

    espece = especes.get(_clean(row[ESPECE_COLUMN]))
    maladie = maladies.get(_clean(row[MALADIE_COLUMN]))

    return {
        "identifiant": row[ID_COLUMN],
        "espece": espece,
        "maladie": maladie,
        "date_confirmation": date_confirmation,
        "code_insee": code_insee,
        "numero_ede": row[EDE_COLUMN],
    }


def parse_csv(file):
    content = file.read().decode()
    reader = csv.DictReader(io.StringIO(content), delimiter=";")
    if missing := [column for column in EXPECTED_COLUMNS if column not in (reader.fieldnames or ())]:
        raise MissingColumnsError(", ".join(missing))

    especes = _especes_by_name()
    maladies = _maladies_by_name()
    rows, seen_identifiants, ignored = [], set(), 0

    for raw_row in reader:
        cleaned_row = {column: raw_row[column].strip() for column in EXPECTED_COLUMNS}
        row = _parse_row(cleaned_row, especes, maladies)

        if not row or row["identifiant"] in seen_identifiants:
            ignored += 1
            continue
        seen_identifiants.add(row["identifiant"])
        rows.append(row)
    return rows, ignored


def create_from_row(row, user):
    EvenementAnimal.objects.create(
        import_id=row["identifiant"],
        espece=row["espece"],
        maladie=row["maladie"],
        statut_animal=StatutAnimal.DETENU,
        numero_identifiant_etablissement=row["numero_ede"],
        date_statut_changed=row["date_confirmation"],
        statut_evenement=StatutEvenement.CONFIRME,
        createur=user.agent.structure,
        type_lieu=TypeLieu.FARM,
    )
