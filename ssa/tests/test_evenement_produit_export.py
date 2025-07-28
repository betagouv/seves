import csv
from io import StringIO

import pytest
from playwright.sync_api import Page, expect

from core.factories import UserFactory
from core.models import Export, LienLibre
from ssa.export import EvenementProduitExport
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.tests.pages import EvenementProduitListPage

NB_QUERIES = 11


@pytest.mark.django_db
def test_export_evenement_produit_simple_case(mailoutbox):
    evenement = EvenementProduitFactory()
    other_evenement = EvenementProduitFactory(numero_annee=2024, numero_evenement=22)
    LienLibre.objects.create(related_object_1=other_evenement, related_object_2=evenement)
    user = UserFactory()
    task = Export.objects.create(user=user, object_ids=[evenement.pk])

    EvenementProduitExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8").split("\n")
    assert (
        lines[0]
        == '"Numéro de fiche","État","Structure créatrice","Date de création","Numéro RASFF","Type d\'événement","Source","Description","Catégorie de produit","Dénomination","Marque","Lots, DLC/DDM","Description complémentaire","Température de conservation","Catégorie de danger","Quantification","Unité de quantification","Évaluation","Produit prêt a manger","Référence souches","Référence clusters","Actions engagées","Numéro de rappels conso","Numéros des objets liés","Numéro SIRET","Raison sociale","Adresse ou lieu-dit","Commune","Département","Pays établissement","Type d\'exploitant","Position dans le dossier"\r'
    )

    expected_fields = [
        str(evenement.numero),
        "Brouillon",
        str(evenement.createur),
        evenement.date_creation.strftime("%d/%m/%Y %Hh%M"),
        evenement.numero_rasff,
        evenement.get_type_evenement_display(),
        evenement.get_source_display(),
        evenement.description,
        evenement.get_categorie_produit_display(),
        evenement.denomination,
        evenement.marque,
        evenement.lots,
        evenement.description_complementaire,
        evenement.get_temperature_conservation_display(),
        evenement.get_categorie_danger_display(),
        str(evenement.quantification),
        evenement.get_quantification_unite_display(),
        evenement.evaluation,
        evenement.get_produit_pret_a_manger_display(),
        evenement.reference_souches,
        evenement.reference_clusters,
        evenement.get_actions_engagees_display(),
        ",".join(evenement.numeros_rappel_conso),
        "2024.22",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ]
    assert expected_fields == next(csv.reader(StringIO(lines[1])))
    assert lines[2] == ""
    assert len(lines) == 3

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == [
        user.email,
    ]
    assert mail.subject == "Sèves - Votre export est prêt"
    assert "_export_evenement_produit.csv" in mail.body


@pytest.mark.django_db
def test_export_evenement_produit_performances_scales_on_number_of_objects(django_assert_num_queries):
    evenement = EvenementProduitFactory()
    task = Export.objects.create(user=UserFactory(), object_ids=[evenement.pk])

    with django_assert_num_queries(NB_QUERIES):
        EvenementProduitExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True

    evenement_1, evenement_2, evenement_3 = EvenementProduitFactory.create_batch(3)
    task = Export.objects.create(user=UserFactory(), object_ids=[evenement_1.pk, evenement_2.pk, evenement_3.pk])

    with django_assert_num_queries(NB_QUERIES + 2):
        EvenementProduitExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True


@pytest.mark.django_db
def test_export_evenement_produit_performances_scales_on_number_of_etablissements(django_assert_num_queries):
    evenement = EtablissementFactory().evenement_produit
    task = Export.objects.create(user=UserFactory(), object_ids=[evenement.pk])

    with django_assert_num_queries(NB_QUERIES + 2):
        EvenementProduitExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True

    evenement = EtablissementFactory().evenement_produit
    EtablissementFactory(evenement_produit=evenement)
    EtablissementFactory(evenement_produit=evenement)
    task = Export.objects.create(user=UserFactory(), object_ids=[evenement.pk])

    with django_assert_num_queries(NB_QUERIES + 4):
        EvenementProduitExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True


@pytest.mark.django_db
def test_export_evenement_produit_content_etablissement(mailoutbox):
    etablissement_1 = EtablissementFactory()
    etablissement_2 = EtablissementFactory(evenement_produit=etablissement_1.evenement_produit)
    task = Export.objects.create(user=UserFactory(), object_ids=[etablissement_1.evenement_produit.pk])
    EvenementProduitExport().export(task.id)

    task.refresh_from_db()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8").split("\n")

    expected_fields = [
        etablissement_1.siret,
        etablissement_1.raison_sociale,
        etablissement_1.adresse_lieu_dit,
        etablissement_1.commune,
        str(etablissement_1.departement),
        str(etablissement_1.pays.name),
        etablissement_1.get_type_exploitant_display(),
        etablissement_1.get_position_dossier_display(),
    ]
    assert expected_fields == next(csv.reader(StringIO(lines[1])))[24:32]

    expected_fields = [
        etablissement_2.siret,
        etablissement_2.raison_sociale,
        etablissement_2.adresse_lieu_dit,
        etablissement_2.commune,
        str(etablissement_2.departement),
        str(etablissement_2.pays.name),
        etablissement_2.get_type_exploitant_display(),
        etablissement_2.get_position_dossier_display(),
    ]
    assert expected_fields == next(csv.reader(StringIO(lines[2])))[24:32]
    assert lines[3] == ""
    assert len(lines) == 4


def test_export_evenement_produit_from_ui(live_server, mocked_authentification_user, page: Page, settings, mailoutbox):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    EvenementProduitFactory(numero_annee=2025, numero_evenement=2)
    EvenementProduitFactory(numero_annee=2025, numero_evenement=1)
    EvenementProduitFactory(numero_annee=2025, numero_evenement=21)
    EvenementProduitFactory(numero_annee=2024, numero_evenement=22)
    search_page = EvenementProduitListPage(page, live_server.url)
    search_page.navigate()

    search_page.numero_field.fill("2025")
    search_page.submit_search()
    search_page.submit_export()

    expect(search_page.page.get_by_text("Votre demande d'export a bien été enregistrée")).to_be_visible()

    task = Export.objects.get()
    assert task.task_done is True
    lines = task.file.read().decode("utf-8").split("\n")
    assert lines[1].startswith('"2025.21",')
    assert lines[2].startswith('"2025.2",')
    assert lines[3].startswith('"2025.1",')
    assert len(lines) == 5

    assert len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.subject == "Sèves - Votre export est prêt"
