from django.core.management.base import BaseCommand
from django.db import connection

MATERIALIZED_VIEWS = [
    "tiac_evenementsimple_mv",
    "tiac_investigationtiac_mv",
]


class Command(BaseCommand):
    help = "Refresh the tiac materialized views."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            for view in MATERIALIZED_VIEWS:
                cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};")
                self.stdout.write(f"Refreshed {view}")
