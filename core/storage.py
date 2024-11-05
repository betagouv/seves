import os
import datetime


def get_timestamped_filename(instance, filename):
    new_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    return os.path.join("documents/", new_filename)
