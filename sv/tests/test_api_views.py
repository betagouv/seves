import pytest
from django.urls import reverse
from sv.models import EspeceEchantillon


@pytest.mark.django_db
def test_api_view_espece_echantillon(client):
    url = reverse("sv:api-search-espece")
    EspeceEchantillon.objects.create(libelle="foo", code_oepp="A")
    EspeceEchantillon.objects.create(libelle="FOO", code_oepp="B")
    EspeceEchantillon.objects.create(libelle="FOOL", code_oepp="C")
    EspeceEchantillon.objects.create(libelle="Bar", code_oepp="D")

    response = client.get(url + "?q=FOO")

    assert response.status_code == 200
    assert response.json() == {
        "results": [{"id": 1, "name": "foo"}, {"id": 2, "name": "FOO"}, {"id": 3, "name": "FOOL"}]
    }
