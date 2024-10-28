from io import StringIO
import pytest
from model_bakery import baker
from unittest import mock

from core.models import Visibilite
from sv.export import FicheDetectionExport
from sv.models import Etat, FicheDetection, NumeroFiche, Lieu, Prelevement, StructurePreleveur
import datetime


def _create_fiche_with_lieu_and_prelevement(numero=123, fill_optional=False):
    etat = Etat.objects.get(id=Etat.get_etat_initial())
    numero = NumeroFiche.objects.create(annee=2024, numero=numero)
    mocked = datetime.datetime(2024, 8, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
        fiche = baker.make(
            FicheDetection,
            etat=etat,
            numero=numero,
            numero_europhyt="EUROPHYT",
            numero_rasff="RASFF",
            date_premier_signalement="2024-01-01",
            commentaire="Mon commentaire",
            mesures_conservatoires_immediates="MCI",
            mesures_consignation="MC",
            mesures_phytosanitaires="MP",
            mesures_surveillance_specifique="MSP",
            visibilite=Visibilite.NATIONAL,
            hors_zone_infestee=None,
            zone_infestee=None,
            _fill_optional=fill_optional,
        )
    lieu = baker.make(
        Lieu,
        fiche_detection=fiche,
        nom="Mon lieu",
        wgs84_longitude=10,
        wgs84_latitude=20,
        lambert93_latitude=30,
        lambert93_longitude=40,
        adresse_lieu_dit="L'angle",
        commune="Saint-Pierre",
        code_insee="12345",
        _fill_optional=fill_optional,
    )
    structure = StructurePreleveur.objects.create(nom="My structure")
    baker.make(
        Prelevement,
        lieu=lieu,
        numero_echantillon="Echantillon 3",
        date_prelevement="2023-12-12",
        is_officiel=True,
        numero_phytopass="Phyto123",
        resultat="detecte",
        structure_preleveur=structure,
        _fill_optional=fill_optional,
    )


@pytest.mark.django_db
def test_export_fiche_detection_content(mocked_authentification_user):
    stream = StringIO()
    _create_fiche_with_lieu_and_prelevement()
    FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    stream.seek(0)
    lines = stream.readlines()
    assert len(lines) == 2

    headers = [
        "Numero",
        "Numero Europhyt",
        "Numero Rasff",
        "Statut Evenement",
        "Organisme Nuisible",
        "Statut Reglementaire",
        "Date Premier Signalement",
        "Commentaire",
        "Mesures Conservatoires Immediates",
        "Mesures Consignation",
        "Mesures Phytosanitaires",
        "Mesures Surveillance Specifique",
        "Etat",
        "Date Creation",
        "Nom",
        "Wgs84 Longitude",
        "Wgs84 Latitude",
        "Lambert93 Latitude",
        "Lambert93 Longitude",
        "Adresse Lieu Dit",
        "Commune",
        "Code Insee",
        "Departement",
        "Numero Echantillon",
        "Date Prelevement",
        "Is Officiel",
        "Numero Phytopass",
        "Resultat",
        "Structure Preleveur",
        "Site Inspection",
        "Matrice Prelevee",
        "Espece Echantillon",
        "Laboratoire Agree",
        "Laboratoire Confirmation Officielle",
    ]
    assert lines[0] == ",".join(headers) + "\r\n"
    assert (
        lines[1]
        == "2024.123,EUROPHYT,RASFF,,,,2024-01-01,Mon commentaire,MCI,MC,MP,MSP,nouveau,2024-08-01 00:00:00+00:00,Mon lieu,10.0,20.0,30.0,40.0,L'angle,Saint-Pierre,12345,,Echantillon 3,2023-12-12,True,Phyto123,detecte,My structure,,,,,\r\n"
    )


@pytest.mark.django_db
def test_export_fiche_detection_performance(django_assert_num_queries, mocked_authentification_user):
    stream = StringIO()
    _create_fiche_with_lieu_and_prelevement(fill_optional=True)

    with django_assert_num_queries(10):
        FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    stream.seek(0)
    lines = stream.readlines()
    assert len(lines) == 2

    stream = StringIO()
    _create_fiche_with_lieu_and_prelevement(numero=4, fill_optional=True)
    _create_fiche_with_lieu_and_prelevement(numero=5, fill_optional=True)
    _create_fiche_with_lieu_and_prelevement(numero=6, fill_optional=True)
    with django_assert_num_queries(10):
        FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    stream.seek(0)
    lines = stream.readlines()
    assert len(lines) == 5


@pytest.mark.django_db
def test_export_fiche_detection_numbers_of_lines(django_assert_num_queries, mocked_authentification_user):
    stream = StringIO()
    etat = Etat.objects.get(id=Etat.get_etat_initial())
    numero = NumeroFiche.objects.create(annee=2024, numero=123)
    mocked = datetime.datetime(2024, 8, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    with mock.patch("django.utils.timezone.now", mock.Mock(return_value=mocked)):
        fiche = baker.make(FicheDetection, etat=etat, numero=numero, visibilite=Visibilite.NATIONAL)
    _lieu_without_prelevement = baker.make(Lieu, fiche_detection=fiche)
    _lieu_without_prelevement_2 = baker.make(Lieu, fiche_detection=fiche)
    lieu = baker.make(
        Lieu,
        fiche_detection=fiche,
        nom="Mon lieu",
        wgs84_longitude=10,
        wgs84_latitude=20,
        lambert93_latitude=30,
        lambert93_longitude=40,
        adresse_lieu_dit="L'angle",
        commune="Saint-Pierre",
        code_insee="12345",
    )
    baker.make(Prelevement, lieu=lieu)
    baker.make(Prelevement, lieu=lieu)

    FicheDetectionExport().export(stream=stream, user=mocked_authentification_user)

    stream.seek(0)
    lines = stream.readlines()
    assert len(lines) == 5
