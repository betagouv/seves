from django.contrib.contenttypes.models import ContentType


def content_type_str_to_obj(obj_as_str):
    content_type_id, object_id = obj_as_str.split("-")
    content_type = ContentType.objects.get(id=content_type_id)
    model_class = content_type.model_class()
    return model_class.objects.get(id=object_id)
