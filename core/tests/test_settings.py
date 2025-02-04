import pytest


@pytest.mark.django_db
def test_default_admin_url_not_accessible(admin_client):
    """Vérifie que l'URL par défaut 'admin/' n'est pas accessible"""
    response = admin_client.get("/admin/")
    assert response.status_code == 404
