import csv
import datetime
from io import StringIO
from unittest import mock

import pytest

from core.models import Visibilite
from sv.export import FicheDetectionExport
from sv.factories import PrelevementFactory, FicheZoneFactory, ZoneInfesteeFactory, FicheDetectionFactory, LieuFactory
from sv.models import StructurePreleveuse


@pytest.mark.django_db
def test_export_headers_content(mocked_authentification_user):
    expected_headers = [
        "Numéro de fiche",
        "Num. événement",
        "Organisme nuisible",
        "Code OEPP",
        "Statut réglementaire",
        "Date de création",
        "Structure créatrice",
        "Numéro Europhyt",
        "Numéro RASFF",
        "Statut de l'événement",
        "Contexte",
        "Nombre ou volume de végétaux infestés",
        "Date premier signalement",
        "Commentaire",
        "Mesures conservatoires immédiates",
        "Mesures de consignation",
        "Mesures phytosanitaires",
        "Mesures de surveillance spécifique",
        # == Lieu ==
        "Nom",
        "Adresse ou lieu-dit",
        "Commune",
        "Site d'inspection",
        "Longitude WGS84",
        "Latitude WGS84",
        "Activité établissement",
        "Pays établissement",
        "Raison sociale établissement",
        "Adresse établissement",
        "SIRET établissement",
        "Code INUPP",
        # == Prelevement ==
        "Type d'analyse",
        "Prélèvement officiel",
        "Numéro du rapport d'inspection",
        "Laboratoire",
        "N° d'échantillon",
        "Structure préleveuse",
        "Date de prélèvement",
        "Nature de l'objet",
        "Espèce de l'échantillon",
        "Résultat",
        # == FicheZoneDelimitee ==
        "Commentaire zone délimitée",
        "Rayon tampon réglementaire ou arbitré",
        "Surface tampon totale",
        # == Zone infestée ==
        "Nom de la zone infestée",
        "Caractéristique principale",
        "Rayon de la zone infestée",
        "Surface infestée totale",
    ]
    stream = StringIO()
    PrelevementFactory(
        lieu__fiche_detection__zone_infestee=ZoneInfesteeFactory(),
        lieu__fiche_detection__evenement__visibilite=Visibilite.NATIONALE,
        lieu__fiche_detection__evenement__fiche_zone_delimitee=FicheZoneFactory(),
    )

    FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)
    stream.seek(0)
    headers = next(csv.reader(stream))

    assert headers == expected_headers


@pytest.mark.django_db
def test_export_data_values(mocked_authentification_user):
    stream = StringIO()
    mocked = datetime.datetime(2024, 8, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
        prelevement = PrelevementFactory(
            lieu__fiche_detection__zone_infestee=ZoneInfesteeFactory(),
            lieu__fiche_detection__evenement__visibilite=Visibilite.NATIONALE,
            lieu__fiche_detection__evenement__fiche_zone_delimitee=FicheZoneFactory(),
            lieu__wgs84_longitude=139.527867,
            lieu__wgs84_latitude=-61.396441,
        )
    lieu = prelevement.lieu
    fiche_detection = prelevement.lieu.fiche_detection
    evenement = fiche_detection.evenement

    FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)
    stream.seek(0)
    next(csv.reader(stream))  # Skip headers
    data = next(csv.reader(stream))

    expected_fields = [
        str(fiche_detection.numero),
        str(evenement.numero),
        evenement.organisme_nuisible.libelle_court,
        evenement.organisme_nuisible.code_oepp,
        evenement.statut_reglementaire.libelle,
        fiche_detection.date_creation.strftime("%Y-%m-%d %H:%M:%S+00:00"),
        str(fiche_detection.createur),
        fiche_detection.numero_europhyt,
        fiche_detection.numero_rasff,
        str(fiche_detection.statut_evenement),
        str(fiche_detection.contexte),
        fiche_detection.vegetaux_infestes,
        fiche_detection.date_premier_signalement.strftime("%Y-%m-%d"),
        fiche_detection.commentaire,
        fiche_detection.mesures_conservatoires_immediates,
        fiche_detection.mesures_consignation,
        fiche_detection.mesures_phytosanitaires,
        fiche_detection.mesures_surveillance_specifique,
        # == Lieu ==
        str(lieu),
        lieu.adresse_lieu_dit,
        lieu.commune,
        str(lieu.site_inspection),
        "139.527867",
        "-61.396441",
        lieu.activite_etablissement,
        lieu.pays_etablissement,
        lieu.raison_sociale_etablissement,
        lieu.adresse_etablissement,
        lieu.siret_etablissement,
        lieu.code_inupp_etablissement,
        # == Prelevement ==
        prelevement.type_analyse,
        str(prelevement.is_officiel),
        prelevement.numero_rapport_inspection,
        str(prelevement.laboratoire),
        prelevement.numero_echantillon,
        str(prelevement.structure_preleveuse),
        prelevement.date_prelevement.strftime("%Y-%m-%d"),
        str(prelevement.matrice_prelevee),
        str(prelevement.espece_echantillon),
        prelevement.resultat,
        # == FicheZoneDelimitee ==
        evenement.fiche_zone_delimitee.commentaire,
        str(evenement.fiche_zone_delimitee.rayon_zone_tampon),
        str(evenement.fiche_zone_delimitee.surface_tampon_totale),
        # == Zone infestée ==
        str(fiche_detection.zone_infestee.nom),
        str(fiche_detection.zone_infestee.caracteristique_principale),
        str(fiche_detection.zone_infestee.rayon),
        str(fiche_detection.zone_infestee.surface_infestee_totale),
    ]
    assert data == expected_fields


@pytest.mark.django_db
def test_export_fiche_detection_performance(django_assert_num_queries, mocked_authentification_user):
    structure, _ = StructurePreleveuse.objects.get_or_create(nom="My structure")

    PrelevementFactory(
        structure_preleveuse=structure,
        lieu__fiche_detection__evenement__visibilite=Visibilite.NATIONALE,
    )
    stream = StringIO()
    with django_assert_num_queries(9):
        FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    PrelevementFactory.create_batch(
        3,
        structure_preleveuse=structure,
        lieu__fiche_detection__evenement__visibilite=Visibilite.NATIONALE,
    )
    stream = StringIO()
    with django_assert_num_queries(9):
        FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory,expected_data_lines",
    [
        (FicheDetectionFactory, 1),
        (lambda: FicheDetectionFactory.create_batch(2), 2),
    ],
)
def test_numbers_of_line_when_export_fiche_detection(mocked_authentification_user, factory, expected_data_lines):
    factory()

    stream = StringIO()
    FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    stream.seek(0)
    reader = csv.reader(stream)
    next(reader)  # Skip headers
    data_lines = list(reader)
    assert len(data_lines) == expected_data_lines


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory,expected_data_lines",
    [
        (LieuFactory, 1),
        (lambda: LieuFactory.create_batch(2), 2),
    ],
)
def test_numbers_of_line_when_export_fiche_detection_with_lieu(
    mocked_authentification_user, factory, expected_data_lines
):
    factory()

    stream = StringIO()
    FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    stream.seek(0)
    reader = csv.reader(stream)
    next(reader)  # Skip headers
    data_lines = list(reader)
    assert len(data_lines) == expected_data_lines


@pytest.mark.django_db
@pytest.mark.parametrize(
    "nb_lieu,nb_prelevement,expected_data_lines",
    [
        (1, 2, 2),  # 1 lieu avec 2 prélèvements = 2 lignes
        (2, 3, 6),  # 2 lieux avec 3 prélèvements chacun = 6 lignes
    ],
)
def test_numbers_of_line_when_export_fiche_detection_with_prelevements(
    mocked_authentification_user, nb_lieu, nb_prelevement, expected_data_lines
):
    fiche = FicheDetectionFactory()
    for _ in range(nb_lieu):
        lieu = LieuFactory(fiche_detection=fiche)
        PrelevementFactory.create_batch(nb_prelevement, lieu=lieu)

    stream = StringIO()
    FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    stream.seek(0)
    reader = csv.reader(stream)
    next(reader)  # Skip headers
    data_lines = list(reader)
    assert len(data_lines) == expected_data_lines
