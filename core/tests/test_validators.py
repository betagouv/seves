from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from core.validators import MagicMimeValidator


def test_gif_header_with_php_payload_is_rejected():
    file = SimpleUploadedFile("test.php.gif", b'GIF8\n<?php echo "TEST"; ?>\n')
    with pytest.raises(ValidationError):
        MagicMimeValidator()(file)


def test_pdf_header_with_php_payload_is_rejected():
    file = SimpleUploadedFile("rapport.pdf", b'%PDF-1.4\n<?php system($_GET["cmd"]); ?>\n%%EOF')
    with pytest.raises(ValidationError):
        MagicMimeValidator()(file)
