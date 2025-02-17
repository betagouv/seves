from django.contrib.contenttypes.models import ContentType
from reversion.models import Version


def get_versions_from_ids(ids, model):
    if not ids:
        return []
    content_type = ContentType.objects.get_for_model(model)
    return Version.objects.select_related("revision__user__agent__structure").filter(
        content_type=content_type, object_id__in=list(ids)
    )
