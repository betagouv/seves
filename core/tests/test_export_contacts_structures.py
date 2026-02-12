from contextlib import redirect_stdout
from io import StringIO

from django.core.management import call_command
import pytest

from core.models import Contact, Structure


@pytest.mark.django_db
def test_export_contacts_with_data():
    structure = Structure.objects.create(niveau1="Direction", niveau2="Service A")
    Contact.objects.create(structure=structure, email="")
    Contact.objects.create(structure=structure, email="test@example.com")

    out = StringIO()
    with redirect_stdout(out):
        call_command("export_contacts_structures")

    result = out.getvalue().splitlines()
    assert len(result) == 2
    assert result[0] == "structure (niveau1),structure (niveau2),email"
    assert result[1] == "Direction,Service A,"
