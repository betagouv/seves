from contextlib import redirect_stdout
from io import StringIO

from django.core.management import call_command
import pytest

from core.models import Contact, Structure


@pytest.fixture
def mock_csv_data(tmp_path):
    data = (
        "structure (niveau1),structure (niveau2),email\n"
        "Direction,Service A,new@example.com\n"
        "Direction,Service B,another@example.com\n"
        "Direction,Service C,"
    )
    p = tmp_path / "test.csv"
    p.write_text(data, encoding="utf-8")
    return str(p)


@pytest.mark.django_db
def test_update_contacts_emails(mock_csv_data):
    structure_a = Structure.objects.create(niveau1="Direction", niveau2="Service A")
    structure_b = Structure.objects.create(niveau1="Direction", niveau2="Service B")
    structure_c = Structure.objects.create(niveau1="Direction", niveau2="Service C")

    contact_a = Contact.objects.create(structure=structure_a, email="")
    contact_b = Contact.objects.create(structure=structure_b, email="")
    contact_c = Contact.objects.create(structure=structure_c, email="")

    out = StringIO()
    with redirect_stdout(out):
        call_command("update_contacts_structures_email", mock_csv_data)

    assert "Mise à jour effectuée : 2 contacts modifiés" in out.getvalue()

    contact_a.refresh_from_db()
    contact_b.refresh_from_db()
    contact_c.refresh_from_db()
    assert contact_a.email == "new@example.com"
    assert contact_b.email == "another@example.com"
    assert contact_c.email == ""
