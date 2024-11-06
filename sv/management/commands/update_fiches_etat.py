from sentry_sdk.crons import monitor
from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from sv.models import FicheDetection, Etat


class Command(BaseCommand):
    help = "Mise à jour quotidienne de l'état des Fiches détection (nouveau -> en_cours) après 14 jours."

    @monitor(monitor_slug="cron-update-fichedetection-etat")
    def handle(self, *args, **options):
        # Calculer la date limite pour filtrer les fiches qui ont plus de 14 jours
        cutoff_date = now() - timedelta(days=14)

        # Récupérer toutes les fiches avec le statut 'nouveau' et créées il y a plus de 14 jours
        etat_nouveau = Etat.objects.get(libelle="nouveau")
        fiches_to_update = FicheDetection.objects.filter(etat=etat_nouveau, date_creation__lte=cutoff_date)

        # Mettre à jour le statut pour les fiches sélectionnées
        etat_en_cours = Etat.objects.get(libelle="en cours")
        for fiche in fiches_to_update:
            fiche.etat = etat_en_cours
            fiche.save()
            self.stdout.write(self.style.SUCCESS(f"Statut mis à jour pour la fiche {fiche.id}"))
