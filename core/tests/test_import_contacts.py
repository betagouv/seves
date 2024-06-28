import pytest
from io import StringIO
from django.core.management import call_command
from django.core.exceptions import ObjectDoesNotExist

from core.models import Contact


@pytest.fixture
def mock_csv_data(tmp_path):
    """Fixture pour les données CSV de test"""
    data = """Structure;Prénom;Nom;Mail;Fonction_hiérarchique;Complément_fonction;Téléphone;Mobile
DDI/DDPP/DDPP17/SSA;John;Doe;test@example.com;Manager;;+33 5 46 00 00 00;+33 6 00 00 00 00
AC/DAC/DGAL/MUS;John2;Doe2;test2@example2.com;Super Manager;;+33 5 46 01 00 00;;
SD/DAAF/DAAF973/SG;Prestataire;TEMPORAIRE;inconnu;;;;"""
    p = tmp_path / "test.csv"
    p.write_text(data, encoding="utf-8")
    return str(p)


@pytest.mark.django_db
def test_import_contacts(mock_csv_data):
    """Test du processus complet d'importation des contacts"""
    out = StringIO()
    call_command("import_contacts", mock_csv_data, stdout=out)
    output = out.getvalue()
    assert "Importation terminée" in output
    assert Contact.objects.count() == 2


@pytest.mark.django_db
def test_data_integrity(mock_csv_data):
    """Test pour vérifier l'intégrité des données après l'importation"""
    call_command("import_contacts", mock_csv_data)
    contact = Contact.objects.get(email="test@example.com")
    assert contact.structure == "DDI/DDPP/DDPP17/SSA"
    assert contact.prenom == "John"
    assert contact.nom == "Doe"
    assert contact.fonction_hierarchique == "Manager"
    assert contact.complement_fonction == ""
    assert contact.telephone == "+33 5 46 00 00 00"
    assert contact.mobile == "+33 6 00 00 00 00"
    contact2 = Contact.objects.get(email="test2@example2.com")
    assert contact2.structure == "AC/DAC/DGAL/MUS"
    assert contact2.prenom == "John2"
    assert contact2.nom == "Doe2"
    assert contact2.fonction_hierarchique == "Super Manager"
    assert contact2.complement_fonction == ""
    assert contact2.telephone == "+33 5 46 01 00 00"


@pytest.mark.django_db
def test_ignore_unknown_email(mock_csv_data):
    """Test pour s'assurer que les lignes avec un email 'inconnu' sont ignorées"""
    call_command("import_contacts", mock_csv_data)
    assert Contact.objects.count() == 2
    with pytest.raises(ObjectDoesNotExist):
        Contact.objects.get(email="inconnu")
