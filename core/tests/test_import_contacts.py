import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model

from core.models import Contact, Agent, Structure


def _reset_contacts():
    # Remove objects created by fixtures
    Contact.objects.all().delete()
    Agent.objects.all().delete()
    Structure.objects.all().delete()
    User = get_user_model()
    User.objects.all().delete()


@pytest.fixture
def mock_allowed_structures_csv(tmp_path):
    """Fixture pour les données CSV de test avec un contact par structure"""
    data = """Structure;Prénom;Nom;Mail;Fonction_hiérarchique;Complément_fonction;Téléphone;Mobile
AC/DAC/DGAL/MUS;Alice;Martin;alice.martin@example.com;Manager;Chef de service;0123456789;0612345678
SD/DRAAF/DRAAF-CENTRE-VAL-DE-LOIRE/SRAL;David;Petit;david.petit@example.com;Directeur SRAL;Chef de service;0234567890;0623456789
SD/DRAAF/DRAAF-OCCITANIE/DIRECTION;François;Moreau;francois.moreau@example.com;Directeur;Direction régionale;0345678901;0634567890
SD/DAAF/DAAF976/MSI;Jacques;Thomas;jacques.thomas@example.com;Chef MSI;Responsable service;0456789012;0645678901
SD/DAAF/DAAF973/SG;Prestataire;TEMPORAIRE;inconnu;;;;"""
    p = tmp_path / "test.csv"
    p.write_text(data, encoding="utf-8")
    return str(p)


@pytest.fixture
def mock_not_allowed_structures_csv(tmp_path):
    """Fixture pour les données CSV de test avec un contact par structure"""
    data = """Structure;Prénom;Nom;Mail;Fonction_hiérarchique;Complément_fonction;Téléphone;Mobile
AUTRE_SERVICE;Sarah;Durand;sarah.durand@example.com;Manager;Non applicable;0789012345;0678901234"""
    p = tmp_path / "test.csv"
    p.write_text(data, encoding="utf-8")
    return str(p)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "contact_data",
    [
        {
            "email": "alice.martin@example.com",
            "structure_niveau2": "MUS",
            "structure_complete": "AC/DAC/DGAL/MUS",
            "prenom": "Alice",
            "nom": "Martin",
            "fonction_hierarchique": "Manager",
            "complement_fonction": "Chef de service",
            "telephone": "0123456789",
            "mobile": "0612345678",
        },
        {
            "email": "david.petit@example.com",
            "structure_niveau2": "DRAAF-CENTRE-VAL-DE-LOIRE",
            "structure_complete": "SD/DRAAF/DRAAF-CENTRE-VAL-DE-LOIRE/SRAL",
            "prenom": "David",
            "nom": "Petit",
            "fonction_hierarchique": "Directeur SRAL",
            "complement_fonction": "Chef de service",
            "telephone": "0234567890",
            "mobile": "0623456789",
        },
        {
            "email": "francois.moreau@example.com",
            "structure_niveau2": "DRAAF-OCCITANIE",
            "structure_complete": "SD/DRAAF/DRAAF-OCCITANIE/DIRECTION",
            "prenom": "François",
            "nom": "Moreau",
            "fonction_hierarchique": "Directeur",
            "complement_fonction": "Direction régionale",
            "telephone": "0345678901",
            "mobile": "0634567890",
        },
        {
            "email": "jacques.thomas@example.com",
            "structure_niveau2": "DAAF976",
            "structure_complete": "SD/DAAF/DAAF976/MSI",
            "prenom": "Jacques",
            "nom": "Thomas",
            "fonction_hierarchique": "Chef MSI",
            "complement_fonction": "Responsable service",
            "telephone": "0456789012",
            "mobile": "0645678901",
        },
    ],
)
def test_data_integrity_for_contact_agent(mock_allowed_structures_csv, contact_data):
    """Vérifie la création correcte des objets Contact, Agent et User l'intégrité des données
    pour contacts liés à des agents dont les structures sont autorisées"""
    _reset_contacts()

    call_command("import_contacts", mock_allowed_structures_csv)

    assert Contact.objects.filter(agent__isnull=False).count() == 4
    assert Agent.objects.count() == 4
    assert get_user_model().objects.count() == 4

    contact = Contact.objects.get(email=contact_data["email"])
    structure = Structure.objects.get(niveau2=contact_data["structure_niveau2"])
    assert contact.agent.structure == structure
    assert contact.agent.structure_complete == contact_data["structure_complete"]
    assert contact.agent.prenom == contact_data["prenom"]
    assert contact.agent.nom == contact_data["nom"]
    assert contact.agent.fonction_hierarchique == contact_data["fonction_hierarchique"]
    assert contact.agent.complement_fonction == contact_data["complement_fonction"]
    assert contact.agent.telephone == contact_data["telephone"]
    assert contact.agent.mobile == contact_data["mobile"]
    assert contact.agent.user.username == contact_data["email"]
    assert contact.agent.user.email == contact_data["email"]
    assert contact.agent.user.is_active is False


@pytest.mark.django_db
def test_invalid_structure_contact_exclusion(mock_not_allowed_structures_csv):
    """Vérifie que les contacts liés à des structures non autorisées ne sont pas sauvegardés en base"""
    _reset_contacts()
    call_command("import_contacts", mock_not_allowed_structures_csv)
    assert Contact.objects.count() == 0


@pytest.mark.django_db
def test_ignore_unknown_email(tmp_path):
    """Test qu'un contact lié à un agent avec un email 'inconnu' n'est pas sauvegardé en base"""
    _reset_contacts()
    csv_data = """Structure;Prénom;Nom;Mail;Fonction_hiérarchique;Complément_fonction;Téléphone;Mobile
    SD/DAAF/DAAF973/SG;Prestataire;TEMPORAIRE;inconnu;;;;"""
    p = tmp_path / "test.csv"
    p.write_text(csv_data, encoding="utf-8")
    call_command("import_contacts", str(p))
    assert Contact.objects.count() == 0


@pytest.mark.django_db
def test_import_contacts_twice_with_user_activation(mock_allowed_structures_csv):
    """Test pour s'assurer que deux importations des contacts fonctionnent en ayant activé un user entre les deux"""
    _reset_contacts()
    call_command("import_contacts", mock_allowed_structures_csv)
    User = get_user_model()
    user = User.objects.get(username="alice.martin@example.com")
    user.is_active = True
    user.save()
    call_command("import_contacts", mock_allowed_structures_csv)


@pytest.mark.django_db
def test_allowed_structure_creation(mock_allowed_structures_csv):
    """Vérifie la création correcte des objets Structure et Contact si les structures sont autorisées"""
    _reset_contacts()
    call_command("import_contacts", mock_allowed_structures_csv)
    expected_structures = [
        {"niveau1": "AC/DAC/DGAL", "niveau2": "MUS", "libelle": "MUS"},
        {"niveau1": "SD/DRAAF", "niveau2": "DRAAF-CENTRE-VAL-DE-LOIRE", "libelle": "DRAAF-CENTRE-VAL-DE-LOIRE"},
        {"niveau1": "SD/DRAAF", "niveau2": "DRAAF-OCCITANIE", "libelle": "DRAAF-OCCITANIE"},
        {"niveau1": "SD/DAAF", "niveau2": "DAAF976", "libelle": "DAAF976"},
    ]
    assert Structure.objects.count() == len(expected_structures)
    assert Contact.objects.filter(structure__isnull=False).count() == len(expected_structures)
    for expected_structure in expected_structures:
        assert Contact.objects.filter(
            structure__niveau1=expected_structure["niveau1"],
            structure__niveau2=expected_structure["niveau2"],
            structure__libelle=expected_structure["libelle"],
        ).exists()


@pytest.mark.django_db
def test_invalid_structure_exclusion(mock_not_allowed_structures_csv):
    """Vérifie que les structures non autorisées ne sont pas créées"""
    _reset_contacts()
    call_command("import_contacts", mock_not_allowed_structures_csv)
    assert Structure.objects.count() == 0
