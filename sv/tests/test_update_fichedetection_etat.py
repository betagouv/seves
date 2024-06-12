from django.test import TestCase
from django.utils.timezone import now, timedelta
from sv.models import FicheDetection
from django.core.management import call_command
from model_bakery import baker


class TestUpdateFicheStatusCommand(TestCase):
    def setUp(self):
        baker.make(FicheDetection, date_creation=now() - timedelta(days=15))

    def test_command_updates_fiche_status(self):
        call_command("update_fichedetection_etat")

        fiche = FicheDetection.objects.first()
        self.assertEqual(fiche.etat.libelle, "en cours")
