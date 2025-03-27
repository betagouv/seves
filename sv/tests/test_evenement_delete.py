import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from core.factories import StructureFactory
from sv.factories import EvenementFactory


@pytest.mark.django_db
def test_cant_delete_evenement_i_cant_see(client):
    evenement = EvenementFactory(createur=StructureFactory())
    assert client.get(evenement.get_absolute_url()).status_code == 403

    response = client.post(
        reverse("soft-delete"),
        {"content_type_id": ContentType.objects.get_for_model(evenement).id, "content_id": evenement.pk},
    )

    assert response.status_code == 302
    evenement.refresh_from_db()
    assert evenement.is_deleted is False
