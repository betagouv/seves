from dataclasses import dataclass
from datetime import datetime
from functools import cache
import logging

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import ManyToOneRel
from django.utils import timezone
from django.utils.encoding import force_str
from reversion import is_registered
from reversion.models import Revision, Version
from reversion.revisions import _get_options
from reversion_compare.compare import (
    CompareObject as InitialCompareObject,
    CompareObjects as InitialCompareObjects,
)
from reversion_compare.mixins import CompareMethodsMixin as CompareMethodsMixin, CompareMixin as OriginalCompareMixin

from core.models import Agent, Structure

logger = logging.getLogger(__name__)


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

    def __repr__(self):
        return self.field + " " + self.old + " " + self.new

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


@cache
def get_queryset_with_related_objects(old_revision, related_model, target_ids):
    return {
        ver.object_id: ver
        for ver in old_revision.version_set.filter(
            content_type=ContentType.objects.get_for_model(related_model), object_id__in=target_ids
        ).all()
    }


class CompareObject(InitialCompareObject):
    def get_many_to_something(self, target_ids, related_model, is_reverse=False):
        """
        Taken from InitialCompareObject and add select_related to reduce the number of queries
        """
        if not is_registered(related_model):
            # There is no history about not registered relations, so we can't build a diff ;)
            logger.debug("Related model %s has not been registered with django-reversion", related_model.__name__)
            return {}, {}, []

        # get instance of reversion.models.Revision():
        # A group of related object versions.
        old_revision = self.version_record.revision

        # Get a queryset with all related objects.
        versions = get_queryset_with_related_objects(old_revision, related_model, frozenset(target_ids))

        missing_objects_dict = {}
        deleted = []

        if not self.follow:
            # This models was not registered with follow relations
            # Try to fill missing related objects
            potentially_missing_ids = target_ids.difference(frozenset(versions))
            if potentially_missing_ids:
                missing_objects_dict = {
                    force_str(rel.pk): rel
                    for rel in related_model.objects.filter(pk__in=potentially_missing_ids).iterator()
                    if is_registered(rel.__class__) or not self.ignore_not_registered
                }

        if is_reverse:
            content_type = ContentType.objects.get_for_model(related_model)
            missing_objects_dict = {
                v.object_id: v
                for v in (
                    Version.objects.filter(
                        content_type=content_type,
                        object_id__in=[o.pk for o in missing_objects_dict.values()],
                        revision__date_created__lt=old_revision.date_created,
                    ).select_related("revision")
                )
            }

            if is_registered(related_model) or not self.ignore_not_registered:
                # shift query to database
                deleted = list(Version.objects.filter(revision=old_revision).get_deleted(related_model))
            else:
                deleted = []

        return versions, missing_objects_dict, deleted

    def get_reverse_generic_relation(self):
        obj = self.get_object_version().object

        if not isinstance(self.field, GenericRelation):
            raise NotImplementedError

        prefetch_attr = f"_prefetched_{self.field_name}"
        if hasattr(obj, prefetch_attr):
            related_objects = getattr(obj, prefetch_attr)
        else:
            related_objects = getattr(obj, self.field_name).all()

        ids = {str(v.pk) for v in related_objects}

        # Get the related model of the current field:
        related_model = self.field.remote_field.model
        return self.get_many_to_something(ids, related_model, is_reverse=True)

    def get_reverse_foreign_key(self):
        """Adapted from original in order to use prefetched objects when possible"""
        obj = self.get_object_version().object
        if not self.field.related_name or not hasattr(obj, self.field.related_name):
            return {}, {}, []

        if isinstance(self.field, models.fields.related.OneToOneRel):
            try:
                ids = {force_str(getattr(obj, force_str(self.field.related_name)).pk)}
            except ObjectDoesNotExist:
                ids = set()
        else:
            prefetch_attr = f"_prefetched_{self.field.related_name}"
            if hasattr(obj, prefetch_attr):
                related_objects = getattr(obj, prefetch_attr)
            else:
                related_objects = getattr(obj, force_str(self.field.related_name)).all()

            # If there is a _ptr this is a multi-inheritance table and inherits from a non-abstract class
            ids = {force_str(v.pk) for v in related_objects}
            if not ids and any([f.name.endswith("_ptr") for f in obj._meta.get_fields()]):
                # If there is a _ptr this is a multi-inheritance table and inherits from a non-abstract class
                # lets try and get the parent items associated entries for this field
                others = self.version_record.revision.version_set.filter(object_id=self.version_record.object_id).all()
                for p in others:
                    p_obj = p._object_version.object
                    if not isinstance(p_obj, type(obj)) and hasattr(p_obj, force_str(self.field.related_name)):
                        ids = {force_str(v.pk) for v in getattr(p_obj, force_str(self.field.related_name)).all()}

        # Get the related model of the current field:
        related_model = self.field.field.model
        return self.get_many_to_something(ids, related_model, is_reverse=True)


class CompareObjects(InitialCompareObjects):
    def __init__(self, field, field_name, obj, version1, version2, is_reversed):
        self.field = field
        self.field_name = field_name
        self.obj = obj

        # is a related field (ForeignKey, ManyToManyField etc.)
        self.is_related = getattr(self.field, "related_model", None) is not None
        self.is_reversed = is_reversed
        if not self.is_related:
            self.follow = None
        elif self.field_name in _get_options(self.obj.__class__).follow:
            self.follow = True
        else:
            self.follow = False

        self.compare_obj1 = CompareObject(field, field_name, obj, version1, self.follow)
        self.compare_obj2 = CompareObject(field, field_name, obj, version2, self.follow)

        self.value1 = self.compare_obj1.value
        self.value2 = self.compare_obj2.value

        self.M2O_CHANGE_INFO = None
        self.M2M_CHANGE_INFO = None
        self.GENERIC_RELATION_CHANGE_INFO = None

    def get_generic_relation_change_info(self):
        if self.GENERIC_RELATION_CHANGE_INFO is not None:
            return self.GENERIC_RELATION_CHANGE_INFO

        version_1_data = self.compare_obj1.get_reverse_generic_relation()
        version_2_data = self.compare_obj2.get_reverse_generic_relation()

        self.GENERIC_RELATION_CHANGE_INFO = self.get_m2s_change_info(version_1_data, version_2_data)
        return self.GENERIC_RELATION_CHANGE_INFO

    def changed(self) -> bool:
        info = None
        if isinstance(self.field, GenericRelation):
            info = self.get_generic_relation_change_info()
        else:
            if hasattr(self.field, "get_internal_type") and self.field.get_internal_type() == "ManyToManyField":
                info = self.get_m2m_change_info()

            elif self.is_reversed:
                info = self.get_m2o_change_info()
        if info:
            keys = (
                "changed_items",
                "removed_items",
                "added_items",
                "removed_missing_objects",
                "added_missing_objects",
                "deleted_items",
            )
            for key in keys:
                if info[key]:
                    return True
            return False

        return self.compare_obj1 != self.compare_obj2


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
            if isinstance(field, GenericRelation) and f not in fields:
                self.reverse_fields.append(field)

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
                if isinstance(field, GenericRelation):
                    change = obj_compare.get_generic_relation_change_info()
                else:
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
                    if getattr(item_1._object_version.object, "show_nested_diff_in_revision_list", True):
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
