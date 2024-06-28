from django.db.models import Case, When, Value, IntegerField, Manager


class DocumentManager(Manager):
    def ordered(self):
        return self.annotate(
            custom_order=Case(
                When(is_deleted=False, then=Value(0)),
                When(is_deleted=False, then=Value(0)),
                output_field=IntegerField(),
            )
        ).order_by("custom_order", "-date_creation")
