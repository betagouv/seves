import itertools

import pytest

from sv.constants import SiteInspection


def test_site_inspection_groups():
    grouped = set(itertools.chain(*SiteInspection.create_named_groups().values()))
    diff = set(SiteInspection) - grouped
    if len(diff):
        pytest.fail(
            f"Enum members {diff} don't have a named group; "
            f"edit {SiteInspection.create_named_groups.__qualname__} to add it to a group"
        )
