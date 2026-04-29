from django.db import migrations, models
from django.db.models import F, TextField, Value
import django.db.models.deletion
from django.db.models.functions import Concat, Trim


def migrate_vegetaux_infestes(apps, _):
    FicheDetection = apps.get_model("sv", "FicheDetection")
    FicheDetection.objects.exclude(vegetaux_infestes="").update(
        vegetaux_infestes="",
        commentaire=Trim(
            Concat(
                F("commentaire"),
                Value("\n\nQuantité de végétaux infestés : ", output_field=TextField()),
                F("vegetaux_infestes"),
            )
        ),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0125_remove_evenement_date_derniere_mise_a_jour_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ElementInfeste",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            (None, "Choisir dans la liste"),
                            (
                                "VEGETAUX_A_REPLANTER",
                                "Végétaux destinés à être (re)plantés ou reproduits",
                            ),
                            (
                                "VEGETAUX_DEJA_PLANTES",
                                "Végétaux déjà plantés, ne devant pas être reproduits ni déplacés",
                            ),
                            (
                                "AUTRES_VEGETAUX",
                                "Autres végétaux, parties de végétaux ou produits végétaux",
                            ),
                            ("VEGETAUX_NON_SPECIFIES", "Végétaux\xa0: non spécifiés"),
                            ("PIEGE", "Objet\xa0: piège"),
                            ("SOL", "Objet\xa0: sol"),
                            ("EAU", "Objet\xa0: eau"),
                            ("AUTRES_OBJETS", "Autres objets"),
                            ("AUCUN", "Aucun"),
                            ("INCONNU", "Inconnu"),
                        ],
                        verbose_name="Type",
                    ),
                ),
                (
                    "quantite",
                    models.CharField(blank=True, verbose_name="Quantité d'éléments infestés"),
                ),
                (
                    "quantite_unite",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("METRE_CARRE", "m²"),
                            ("KILOMETRE_CARRE", "km²"),
                            ("HECTAR", "ha"),
                            ("METRE_CUBE", "m³"),
                            ("KILOGRAMME", "kg"),
                            ("PIECE", "pièce"),
                        ],
                        verbose_name="Unité",
                    ),
                ),
                ("comments", models.TextField(blank=True, verbose_name="Commentaire")),
                (
                    "espece",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.especeechantillon",
                        verbose_name="Espèce végétale",
                    ),
                ),
                (
                    "fiche_detection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="elements_infestes",
                        to="sv.fichedetection",
                        verbose_name="Fiche de détection",
                    ),
                ),
            ],
        ),
        migrations.RunPython(migrate_vegetaux_infestes, reverse_code=migrations.RunPython.noop),
    ]
