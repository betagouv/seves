from unittest import mock
from unittest.mock import MagicMock

import pytest

from core.factories import DocumentFactory, UserFactory
from core.tasks import scan_for_viruses


@pytest.mark.django_db
def test_without_virus():
    user = UserFactory()
    document = DocumentFactory(content_object=user)

    mock_run = MagicMock(returncode=0, stdout="OK", stderr="")
    with mock.patch("subprocess.run", mock.Mock(return_value=mock_run)):
        scan_for_viruses(document.pk)

    document.refresh_from_db()
    assert document.is_infected is False


@pytest.mark.django_db
def test_with_virus():
    user = UserFactory()
    document = DocumentFactory(content_object=user)

    mock_run = MagicMock(returncode=1)
    with mock.patch("subprocess.run", mock.Mock(return_value=mock_run)):
        scan_for_viruses(document.pk)

    document.refresh_from_db()
    assert document.is_infected is True
