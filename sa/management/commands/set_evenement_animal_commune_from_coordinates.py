from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
import requests

from core.models import Departement
from sa.models import EvenementAnimal


class Command(BaseCommand):
    help = "Renseigne la commune, le code INSEE et le département du foyer des événements SA à partir de leurs coordonnées."

    def handle(self, *args, **options):
        departements = {departement.numero: departement for departement in Departement.objects.all()}
        evenements = EvenementAnimal._base_manager.filter(Q(code_insee="") | Q(departement__isnull=True)).exclude(
            coordinates__isnull=True
        )

        updated, not_found = 0, 0
        for evenement in evenements:
            if evenement.code_insee:
                fields = {"departement": self._get_departement(departements, evenement.code_insee)}
            else:
                commune = self._fetch_commune(evenement.coordinates)
                if not commune:
                    not_found += 1
                    self.stdout.write(f"Aucune commune trouvée pour l'événement {evenement.pk}")
                    continue
                fields = {
                    "commune": commune["nom"],
                    "code_insee": commune["code"],
                    "departement": departements.get(commune["departement"]["code"]),
                }

            EvenementAnimal._base_manager.filter(pk=evenement.pk).update(**fields)
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"{updated} événement(s) mis à jour, {not_found} sans commune trouvée."))

    def _get_departement(self, departements, code_insee):
        return departements.get(code_insee[:2]) or departements.get(code_insee[:3])

    def _fetch_commune(self, point):
        response = requests.get(
            f"{settings.GEO_API_ROOT}/communes",
            params={"lat": point.y, "lon": point.x, "fields": "nom,code,departement"},
            timeout=10,
        )
        response.raise_for_status()
        communes = response.json()
        return communes[0] if communes else None
