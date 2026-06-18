from django.urls import reverse

from core.factories import ContactStructureFactory
from core.models import Structure
from tiac.factories import EvenementSimpleFactory
from tiac.models import InvestigationTiac


def test_cant_forge_evenement_simple_transfer_of_evenement_i_cant_see(client):
    evenement = EvenementSimpleFactory(createur=Structure.objects.create(libelle="A new structure"))
    assert evenement.transfered_to is None
    response = client.get(evenement.get_absolute_url())
    transfered_to = ContactStructureFactory(structure__libelle="DD_TEST", with_one_active_agent=True)
    assert response.status_code == 403

    payload = {"transfered_to": transfered_to.pk}
    response = client.post(reverse("tiac:evenement-simple-transfer", kwargs={"pk": evenement.pk}), data=payload)

    assert response.status_code == 404
    assert evenement.transfered_to is None


def test_cant_forge_evenement_simple_transform_of_evenement_i_cant_see(client):
    evenement = EvenementSimpleFactory(createur=Structure.objects.create(libelle="A new structure"))
    response = client.get(evenement.get_absolute_url())
    assert response.status_code == 403

    response = client.post(reverse("tiac:transform-investigation", kwargs={"pk": evenement.pk}))

    assert response.status_code == 404
    assert InvestigationTiac.objects.count() == 0
