from unittest import mock
from unittest.mock import MagicMock

import pytest

from core.factories import DocumentFactory, UserFactory
from core.tasks import scan_for_viruses


@pytest.mark.django_db
def test_without_virus(settings):
    settings.ANTIVIRUS_URL = "https://test.com"
    settings.ANTIVIRUS_TOKEN = "NOT_A_REAL_TOKEN"
    user = UserFactory()
    document = DocumentFactory(content_object=user)

    mock_post = MagicMock(status_code=200)
    mock_post.json.return_value = {"is_malware": False}
    with mock.patch("core.antivirus.requests.post", mock.Mock(return_value=mock_post)):
        scan_for_viruses(document.pk)

    document.refresh_from_db()
    assert document.is_infected is False


@pytest.mark.django_db
def test_with_virus(settings):
    settings.ANTIVIRUS_URL = "https://test.com"
    settings.ANTIVIRUS_TOKEN = "NOT_A_REAL_TOKEN"
    user = UserFactory()
    document = DocumentFactory(content_object=user)

    mock_post = MagicMock(status_code=200)
    mock_post.json.return_value = {"is_malware": True}
    with mock.patch("core.antivirus.requests.post", mock.Mock(return_value=mock_post)):
        scan_for_viruses(document.pk)

    document.refresh_from_db()
    assert document.is_infected is True
