import pytest


@pytest.fixture
def assert_models_are_equal():
    def _assert_models_are_equal(obj_1, obj_2, to_exclude=None):
        if not to_exclude:
            to_exclude = []

        obj_1_data = {k: v for k, v in obj_1.__dict__.items() if k not in to_exclude}
        obj_2_data = {k: v for k, v in obj_2.__dict__.items() if k not in to_exclude}
        assert obj_1_data == obj_2_data

    return _assert_models_are_equal
