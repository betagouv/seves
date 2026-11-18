"""Lecture et validation du fichier CSV d'import d'événements de santé animale."""

import csv
from datetime import datetime
import io
import re

from core.mixins import normalize
from sa.models import Espece, Maladie, Typage

IMPORTABLE_MALADIE_ACRONYMS = ("FCO", "MHE")
EXPECTED_COLUMNS = (
    "Identifiant unique",
    "Espèce",
    "Maladie",
    "Date de confirmation",
    "Code INSEE commune",
    "N° EDE",
    "Sérotype",
)
CODE_INSEE_RE = re.compile(r"^(?:\d{5}|2[AB]\d{3})$")


class MissingColumnsError(Exception):
    """Le fichier déposé n'a pas les colonnes attendues."""


def _key(value):
    """Clé de correspondance : valeur sans accent, en minuscules, sans espace superflu."""
    return " ".join(normalize(value).split())


def _especes_by_name():
    """Les espèces du référentiel, indexées par leur nom complet et par leur seul nom français."""
    especes = {}
    for espece in Espece.objects.all():
        especes.setdefault(_key(espece.name.rsplit("(", 1)[0]), espece)
        especes[_key(espece.name)] = espece
    return especes


def _maladies_by_name():
    """Les maladies importables, indexées par leur nom et par leur acronyme."""
    maladies = {}
    for maladie in Maladie.objects.filter(acronym__in=IMPORTABLE_MALADIE_ACRONYMS):
        maladies[_key(maladie.name)] = maladie
        maladies[_key(maladie.acronym)] = maladie
    return maladies


def _serotypes_by_maladie():
    """Les sérotypes du référentiel des maladies importables, indexés par (maladie, valeur)."""
    typages = Typage.objects.filter(maladie__acronym__in=IMPORTABLE_MALADIE_ACRONYMS)
    return {(typage.maladie_id, typage.valeur_niveau_2): typage for typage in typages}


def _parse_row(row, especes, maladies, serotypes):
    """La ligne avec les valeurs du référentiel Sèves, ou None si elle doit être ignorée."""
    identifiant = row["Identifiant unique"].strip()
    numero_ede = row["N° EDE"].strip()
    code_insee = row["Code INSEE commune"].strip().upper()
    if not identifiant or not numero_ede or not CODE_INSEE_RE.match(code_insee):
        return None

    espece = especes.get(_key(row["Espèce"]))
    maladie = maladies.get(_key(row["Maladie"]))
    if not espece or not maladie:
        return None

    try:
        date_confirmation = datetime.strptime(row["Date de confirmation"].strip(), "%d/%m/%Y").date()
    except ValueError:
        return None

    serotype = None
    if valeur_serotype := row["Sérotype"].strip():
        serotype = serotypes.get((maladie.pk, valeur_serotype))
        if not serotype:
            return None

    return {
        "identifiant": identifiant,
        "espece": espece,
        "maladie": maladie,
        "date_confirmation": date_confirmation,
        "code_insee": code_insee,
        "numero_ede": numero_ede,
        "serotype": serotype,
    }


def parse_csv(file):
    """Retourne (lignes éligibles à l'import, nombre de lignes ignorées)."""
    file.seek(0)
    content = file.read().decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(content), delimiter=";", restval="")
    if missing := [column for column in EXPECTED_COLUMNS if column not in (reader.fieldnames or ())]:
        raise MissingColumnsError(", ".join(missing))

    especes, maladies, serotypes = _especes_by_name(), _maladies_by_name(), _serotypes_by_maladie()
    rows, seen_identifiants, ignored = [], set(), 0
    for raw_row in reader:
        row = _parse_row(raw_row, especes, maladies, serotypes)
        if not row or row["identifiant"] in seen_identifiants:
            ignored += 1
            continue
        seen_identifiants.add(row["identifiant"])
        rows.append(row)
    return rows, ignored
