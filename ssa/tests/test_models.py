import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.factories import DocumentFactory
from core.models import Document
from ssa.factories import EvenementProduitFactory, EtablissementFactory
from ssa.constants import CategorieDanger, PretAManger


@pytest.mark.django_db
def test_numero_rappel_conso():
    evenement = EvenementProduitFactory(numeros_rappel_conso=["1999-01-0123"])
    evenement.full_clean()

    evenement = EvenementProduitFactory(numeros_rappel_conso=["1999-01-3"])
    with pytest.raises(ValidationError):
        evenement.full_clean()

    evenement = EvenementProduitFactory(numeros_rappel_conso=["1999-1-3333"])
    with pytest.raises(ValidationError):
        evenement.full_clean()


@pytest.mark.django_db
def test_numero_rasff_aac():
    evenement = EvenementProduitFactory(numero_rasff="2024.1234")
    evenement.full_clean()
    evenement = EvenementProduitFactory(numero_rasff="AA24.5864")
    evenement.full_clean()
    evenement = EvenementProduitFactory(numero_rasff="987654")
    evenement.full_clean()

    evenement = EvenementProduitFactory(numero_rasff="989")
    with pytest.raises(ValidationError):
        evenement.full_clean()


@pytest.mark.django_db
def test_evenement_produit_latest_revision():
    evenement = EvenementProduitFactory()
    assert evenement.latest_version is not None
    latest_version = evenement.latest_version

    evenement.description = "Lorem"
    evenement.save()
    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created
    latest_version = evenement.latest_version

    etablissement = EtablissementFactory(evenement_produit=evenement)
    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created

    etablissement.raison_sociale = "Foo"
    etablissement.save()
    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created


@pytest.mark.django_db
def test_pam_requires_danger_bacterien_constraint():
    EvenementProduitFactory(produit_pret_a_manger="", categorie_danger=CategorieDanger.OGM)

    with pytest.raises(IntegrityError):
        EvenementProduitFactory(produit_pret_a_manger=PretAManger.OUI, categorie_danger=CategorieDanger.OGM)
    with pytest.raises(IntegrityError):
        EvenementProduitFactory(produit_pret_a_manger=PretAManger.NON, categorie_danger=CategorieDanger.OGM)
    with pytest.raises(IntegrityError):
        EvenementProduitFactory(produit_pret_a_manger=PretAManger.SANS_OBJET, categorie_danger=CategorieDanger.OGM)

    EvenementProduitFactory(produit_pret_a_manger=PretAManger.OUI, categorie_danger=CategorieDanger.SALMONELLA)
    EvenementProduitFactory(produit_pret_a_manger=PretAManger.NON, categorie_danger=CategorieDanger.STAPHYLOCOCCUS)
    EvenementProduitFactory(
        produit_pret_a_manger=PretAManger.SANS_OBJET, categorie_danger=CategorieDanger.VIBRIO_VULNIFICUS
    )


@pytest.mark.django_db
def test_cant_create_document_with_invalid_document_type():
    DocumentFactory(
        content_object=EvenementProduitFactory(), document_type=Document.TypeDocument.CERTIFICAT_PHYTOSANITAIRE
    )
