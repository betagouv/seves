from rate_limit.tests.conftest import FakeUser
from rate_limit.utils import get_page_view_count, increment_page_view_count


def test_counters_are_isolated_per_user():
    user_a = FakeUser(pk=1)
    user_b = FakeUser(pk=2)

    increment_page_view_count(user_a)
    increment_page_view_count(user_a)
    increment_page_view_count(user_b)

    assert get_page_view_count(user_a) == 2
    assert get_page_view_count(user_b) == 1
