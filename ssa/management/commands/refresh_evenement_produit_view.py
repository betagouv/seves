from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Refresh the ssa_evenementproduit_mv materialized view."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY ssa_evenementproduit_mv;")
        self.stdout.write("Refreshed ssa_evenementproduit_mv")
