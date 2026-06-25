from django.urls import reverse

from core.models import Structure
from tiac.factories import InvestigationTiacFactory


def test_cant_forge_investigation_tiac_update_i_cant_see(client):
    evenement = InvestigationTiacFactory(createur=Structure.objects.create(libelle="A new structure"))
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    response = client.post(reverse("tiac:investigation-tiac-edition", kwargs={"pk": evenement.pk}), data={})

    assert response.status_code == 403
