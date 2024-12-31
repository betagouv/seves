from sentry_sdk.crons import monitor
from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from sv.models import Etat, Evenement


class Command(BaseCommand):
    help = "Mise à jour quotidienne de l'état des événements (nouveau -> en_cours) après 14 jours."

    @monitor(monitor_slug="cron-update-evenement-etat")
    def handle(self, *args, **options):
        cutoff_date = now() - timedelta(days=14)
        etat_nouveau = Etat.objects.get(libelle="nouveau")
        etat_en_cours = Etat.objects.get(libelle="en cours")

        evenements = Evenement.objects.filter(etat=etat_nouveau, date_creation__lte=cutoff_date)
        for evenement in evenements:
            evenement.etat = etat_en_cours
            evenement.save()
            self.stdout.write(self.style.SUCCESS(f"Statut mis à jour pour l'événement {evenement.id}"))
