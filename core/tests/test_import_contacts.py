import pytest
from io import StringIO
from django.core.management import call_command
from django.core.exceptions import ObjectDoesNotExist

from core.models import Contact, Agent, Structure


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
    assert Agent.objects.count() == 2
    assert Structure.objects.count() == 2
    assert Contact.objects.count() == 4


@pytest.mark.django_db
def test_data_integrity(mock_csv_data):
    """Test pour vérifier l'intégrité des données après l'importation"""
    call_command("import_contacts", mock_csv_data)

    # vérification de l'enregistrement des structures
    structure_ddpp17 = Structure.objects.get(niveau2="DDPP17")
    assert structure_ddpp17.niveau1 == "DDI/DDPP"
    assert structure_ddpp17.niveau2 == "DDPP17"
    assert structure_ddpp17.libelle == "DDPP17"

    structure_mus = Structure.objects.get(niveau2="MUS")
    assert structure_mus.niveau1 == "AC/DAC/DGAL"
    assert structure_mus.niveau2 == "MUS"
    assert structure_mus.libelle == "MUS"

    # vérification de l'enregistrement des contacts de type Structure (FK structure non null)
    assert Contact.objects.get(structure=structure_ddpp17) is not None
    assert Contact.objects.get(structure=structure_mus) is not None

    # vérification de l'enregistrement des contacts de type Agent (FK agent non null)
    contact = Contact.objects.get(email="test@example.com")
    assert contact.agent.structure == structure_ddpp17
    assert contact.agent.structure_complete == "DDI/DDPP/DDPP17/SSA"
    assert contact.agent.prenom == "John"
    assert contact.agent.nom == "Doe"
    assert contact.agent.fonction_hierarchique == "Manager"
    assert contact.agent.complement_fonction == ""
    assert contact.agent.telephone == "+33 5 46 00 00 00"
    assert contact.agent.mobile == "+33 6 00 00 00 00"

    contact2 = Contact.objects.get(email="test2@example2.com")
    assert contact2.agent.structure == structure_mus
    assert contact2.agent.structure_complete == "AC/DAC/DGAL/MUS"
    assert contact2.agent.prenom == "John2"
    assert contact2.agent.nom == "Doe2"
    assert contact2.agent.fonction_hierarchique == "Super Manager"
    assert contact2.agent.complement_fonction == ""
    assert contact2.agent.telephone == "+33 5 46 01 00 00"


@pytest.mark.django_db
def test_ignore_unknown_email(mock_csv_data):
    """Test pour s'assurer que les lignes avec un email 'inconnu' sont ignorées"""
    call_command("import_contacts", mock_csv_data)
    assert Contact.objects.filter(agent__isnull=False).count() == 2
    with pytest.raises(ObjectDoesNotExist):
        Contact.objects.get(email="inconnu")
