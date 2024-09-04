from django.contrib.contenttypes.models import ContentType
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.models import Structure, LienLibre


@pytest.mark.django_db
def test_cant_create_freelink_on_same_object():
    structure_1 = Structure.objects.create(niveau1="Foo")
    content_type = ContentType.objects.get_for_model(structure_1)

    with pytest.raises(IntegrityError):
        LienLibre.objects.create(
            content_type_1=content_type,
            object_id_1=structure_1.id,
            content_type_2=content_type,
            object_id_2=structure_1.id,
        )


@pytest.mark.django_db
def test_cant_create_freelink_if_inverted_relation_exists():
    structure_1 = Structure.objects.create(niveau1="Foo")
    structure_2 = Structure.objects.create(niveau1="Bar")
    content_type = ContentType.objects.get_for_model(structure_1)
    LienLibre.objects.create(
        content_type_1=content_type, object_id_1=structure_1.id, content_type_2=content_type, object_id_2=structure_2.id
    )

    with pytest.raises(ValidationError):
        LienLibre.objects.create(
            content_type_1=content_type,
            object_id_1=structure_2.id,
            content_type_2=content_type,
            object_id_2=structure_1.id,
        )
