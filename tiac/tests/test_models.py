import pytest

from tiac.factories import EvenementSimpleFactory, EtablissementFactory


@pytest.mark.django_db
def test_evenement_simple_latest_revision():
    evenement = EvenementSimpleFactory()
    assert evenement.latest_version is not None
    latest_version = evenement.latest_version

    evenement.commentaire = "Lorem"
    evenement.save()
    del evenement.latest_version
    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created

    latest_version = evenement.latest_version

    etablissement = EtablissementFactory(evenement_simple=evenement, raison_sociale="Mon entreprise")
    del evenement.latest_version
    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created
    assert evenement.latest_version.revision.comment == "L'établissement 'Mon entreprise' a été ajouté à la fiche"

    latest_version = evenement.latest_version

    etablissement.raison_sociale = "Test"
    etablissement.save()
    del evenement.latest_version
    assert latest_version.pk != evenement.latest_version.pk
    assert latest_version.revision.date_created < evenement.latest_version.revision.date_created
