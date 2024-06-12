from django.test import TestCase
from ..models import FicheDetection, Etat
from model_bakery import baker


class FicheDetectionEtatTest(TestCase):
    def setUp(self):
        self.etat_nouveau, _ = Etat.objects.get_or_create(libelle="nouveau")

    def test_etat_initial(self):
        fiche = baker.make(FicheDetection)
        self.assertEqual(fiche.etat, self.etat_nouveau)
