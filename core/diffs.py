from django.db import models
from reversion_compare.compare import CompareObjects
from reversion_compare.mixins import CompareMethodsMixin as CompareMethodsMixin
from reversion_compare.mixins import CompareMixin as OriginalCompareMixin


class CompareMixin(CompareMethodsMixin, OriginalCompareMixin):
    def compare(self, obj, version1, version2):
        """
        Taken from OriginalCompareMixin with a small twist to get the original and new value in the diff
        """
        diff = []

        # Create a list of all normal fields and append many-to-many fields
        fields = [field for field in obj._meta.fields]
        concrete_model = obj._meta.concrete_model
        fields += concrete_model._meta.many_to_many

        # This gathers the related reverse ForeignKey fields, so we can do ManyToOne compares
        self.reverse_fields = []
        for field in obj._meta.get_fields(include_hidden=True):
            f = getattr(field, "field", None)
            if isinstance(f, models.ForeignKey) and f not in fields:
                self.reverse_fields.append(f.remote_field)

        fields += self.reverse_fields

        has_unfollowed_fields = False

        for field in fields:
            try:
                field_name = field.name
            except AttributeError:
                # is a reverse FK field
                field_name = field.field_name

            if self.compare_fields and field_name not in self.compare_fields:
                continue
            if self.compare_exclude and field_name in self.compare_exclude:
                continue

            is_reversed = field in self.reverse_fields
            obj_compare = CompareObjects(field, field_name, obj, version1, version2, is_reversed)

            is_related = obj_compare.is_related
            follow = obj_compare.follow

            if is_related and not follow:
                has_unfollowed_fields = True

            if not obj_compare.changed():
                # Skip all fields that aren't changed
                continue

            if is_reversed:
                change = obj_compare.get_m2o_change_info()
                for item in change["deleted_items"]:
                    new = f"Objet supprimé : {item._object_version.object.__class__.__name__} {item}"
                    diff.append({"field": field, "is_related": is_related, "follow": follow, "old": "", "new": new})
                for item in change["added_items"]:
                    new = f"Objet ajouté : {item._object_version.object.__class__.__name__} {item}"
                    diff.append({"field": field, "is_related": is_related, "follow": follow, "old": "", "new": new})
                for item_1, _item_2 in change["changed_items"]:
                    new = f"Objet modifié : {item_1._object_version.object.__class__.__name__} {item_1}"
                    diff.append({"field": field, "is_related": is_related, "follow": follow, "old": "", "new": new})
            elif hasattr(field, "get_internal_type") and field.get_internal_type() == "ManyToManyField":
                change = obj_compare.get_m2m_change_info()
                if change["removed_items"]:
                    new = f"Élement(s) retiré(s) {', '.join([str(item) for item in change['removed_items']])}"
                    diff.append({"field": field, "is_related": is_related, "follow": follow, "old": "", "new": new})
                if change["added_items"] or change["added_missing_objects"]:
                    items = change["added_items"] + change["added_missing_objects"]
                    new = f"Élement(s) ajouté(s) {', '.join([str(item) for item in items])}"
                    diff.append({"field": field, "is_related": is_related, "follow": follow, "old": "", "new": new})
            else:
                old = obj_compare.compare_obj1.to_string()
                new = obj_compare.compare_obj2.to_string()
                diff.append({"field": field, "is_related": is_related, "follow": follow, "old": old, "new": new})

        if comment := version1.revision.get_comment():
            diff.append({"field": "", "is_related": None, "follow": None, "old": "", "new": comment})

        return diff, has_unfollowed_fields
