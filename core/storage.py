import datetime
import os


def get_timestamped_filename(instance, filename):
    name, ext = os.path.splitext(filename)
    new_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{name[:150]}{ext}"
    return os.path.join("documents/", new_filename)


def get_timestamped_filename_export(instance, filename):
    new_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{instance.id}_{filename}"
    return os.path.join("export/", new_filename)
