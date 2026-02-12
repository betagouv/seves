from unittest.mock import patch

from django.urls import reverse


@patch("ssa.views.api.requests.get")
@patch("ssa.views.api.csv.reader")
def test_api_view_siret_found(mock_csv_reader, mock_requests_get, client):
    mock_requests_get.return_value.text = "mocked content"
    mock_csv_reader.return_value = iter(
        [
            ["Numero de département", "Numéro agrément/Approval number", "SIRET", "Other columns"],
            ["1", "03.223.432", "12345", "Other data"],
        ]
    )

    response = client.get(reverse("ssa:find-numero-agrement") + "?siret=12345")

    assert response.status_code == 200
    assert response.json() == {"numero_agrement": "03.223.432"}
    assert mock_requests_get.call_count == 1


@patch("ssa.views.api.requests.get")
@patch("ssa.views.api.csv.reader")
def test_api_view_siret_not_found(mock_csv_reader, mock_requests_get, client):
    mock_requests_get.return_value.text = "mocked content"
    mock_csv_reader.return_value = iter(
        [
            ["Numero de département", "Numéro agrément/Approval number", "SIRET", "Other columns"],
            ["1", "03.223.432", "12345", "Other data"],
        ]
    )

    response = client.get(reverse("ssa:find-numero-agrement") + "?siret=5555555")

    assert response.status_code == 404
    assert response.json() == {"error": "SIRET non trouvé"}
    assert mock_requests_get.call_count == 18
