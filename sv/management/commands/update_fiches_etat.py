from sentry_sdk.crons import monitor
from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from sv.models import FicheDetection, Etat, FicheZoneDelimitee


class Command(BaseCommand):
    help = (
        "Mise à jour quotidienne de l'état des Fiches détection et zone délimitée (nouveau -> en_cours) après 14 jours."
    )

    @monitor(monitor_slug="cron-update-fiches-etat")
    def handle(self, *args, **options):
        cutoff_date = now() - timedelta(days=14)
        etat_nouveau = Etat.objects.get(libelle="nouveau")
        etat_en_cours = Etat.objects.get(libelle="en cours")

        for model in (FicheDetection, FicheZoneDelimitee):
            fiches_to_update = model.objects.filter(etat=etat_nouveau, date_creation__lte=cutoff_date)
            for fiche in fiches_to_update:
                fiche.etat = etat_en_cours
                fiche.save()
                self.stdout.write(self.style.SUCCESS(f"Statut mis à jour pour la fiche {fiche.id}"))
