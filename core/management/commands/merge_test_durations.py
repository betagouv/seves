import contextlib
import glob
import json
from json import JSONDecodeError
from pathlib import Path

from django.core.management.base import BaseCommand

from seves import settings


class Command(BaseCommand):
    help = "Merges multiple pytest-split test durations"

    def add_arguments(self, parser):
        parser.add_argument("pattern", type=str)
        parser.add_argument("dest", type=str)

    def handle(self, pattern, dest, *args, **options):
        result = {}
        for file in glob.glob(pattern, root_dir=settings.BASE_DIR):
            with open(Path(file).resolve()) as f:
                with contextlib.suppress(JSONDecodeError):
                    result.update(json.load(f))

        with open(Path(settings.BASE_DIR) / dest, "w") as f:
            f.write(json.dumps(result, sort_keys=True, indent=4))
