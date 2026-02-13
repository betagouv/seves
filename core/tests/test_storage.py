from core.storage import get_timestamped_filename


def test_storage_filename():
    assert get_timestamped_filename(None, "X" * 300 + "Y.txt").endswith("X.txt")
