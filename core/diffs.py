from dataclasses import dataclass
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import ManyToOneRel
from django.utils import timezone
from reversion.models import Revision, Version
from reversion.revisions import _get_options
from reversion_compare.compare import CompareObjects
from reversion_compare.mixins import CompareMethodsMixin as CompareMethodsMixin, CompareMixin as OriginalCompareMixin

from core.models import Agent, Structure


@dataclass
class Diff:
    field: str
    old: str
    new: str
    comment: str
    agent: Agent
    structure: Structure
    date_created: datetime

    def _normalize_value(self, value):
        if value == "None":
            value = "Vide"
        if value == "True":
            value = "Oui"
        if value == "False":
            value = "Non"
        return value

    def _normalize_field(self, field):
        if field == "transfered to":
            return "Transféré à"
        return field

    def __init__(self, field, old, new, revision=None, comment=""):
        self.field = self._normalize_field(field)
        self.old = self._normalize_value(old)
        self.new = self._normalize_value(new)
        self.comment = comment

        if revision:
            self.date_created = revision.date_created
            if revision.user:
                self.agent = revision.user.agent
                self.structure = self.agent.structure


def get_diff_from_comment_version(version):
    comment = version.revision.get_comment()
    if not comment:
        return None
    try:
        field = version.revision.customrevisionmetadata.extra_data.get("field")
    except ObjectDoesNotExist:
        field = ""
    return Diff(field, "", "", version.revision, comment)


def create_manual_version(obj, comment, user=None):
    revision = Revision.objects.create(user=user, comment=comment, date_created=timezone.now())

    options = _get_options(obj.__class__)
    Version.objects.create(
        revision=revision,
        content_type=ContentType.objects.get_for_model(obj),
        object_id=obj.pk,
        object_repr=str(obj),
        format=options.format,
        serialized_data={},
        db="default",
    )
    return revision


class CompareMixin(CompareMethodsMixin, OriginalCompareMixin):
    def _get_pretty_field(self, field, prefix=""):
        value = str(field)
        if hasattr(field, "verbose_name"):
            value = field.verbose_name
        elif isinstance(field, ManyToOneRel):
            value = str(field.related_model.__name__)
        if prefix:
            return f"{prefix} - {value}"
        return value

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
                    diff.append(Diff(self._get_pretty_field(field), "", new, version2.revision))
                for item in change["added_items"]:
                    new = f"Objet ajouté : {item._object_version.object.__class__.__name__} {item}"
                    diff.append(Diff(self._get_pretty_field(field), "", new, version2.revision))
                for item_1, _item_2 in change["changed_items"]:
                    model_name = item_1._object_version.object._meta.verbose_name.title()
                    prefix = f"{model_name} ({str(item_1._object_version.object)})"
                    nested_diff = self.compare(item_1._object_version.object, item_1, _item_2)[0]
                    for change in nested_diff:
                        pretty_field = self._get_pretty_field(change.field, prefix=prefix)
                        diff.append(Diff(pretty_field, change.old, change.new, version2.revision))
            elif hasattr(field, "get_internal_type") and field.get_internal_type() == "ManyToManyField":
                change = obj_compare.get_m2m_change_info()
                if change["removed_items"]:
                    new = f"Élement(s) retiré(s) {', '.join([str(item) for item in change['removed_items']])}"
                    diff.append(Diff(self._get_pretty_field(field), "", new, version2.revision))
                if change["added_items"] or change["added_missing_objects"]:
                    items = change["added_items"] + change["added_missing_objects"]
                    new = f"Élement(s) ajouté(s) {', '.join([str(item) for item in items])}"
                    diff.append(Diff(self._get_pretty_field(field), "", new, version2.revision))
            else:
                old = obj_compare.compare_obj1.to_string()
                new = obj_compare.compare_obj2.to_string()
                diff.append(Diff(self._get_pretty_field(field), old, new, version2.revision))

        comment_diff = get_diff_from_comment_version(version2)
        if comment_diff:
            diff.append(comment_diff)
        return diff, has_unfollowed_fields
