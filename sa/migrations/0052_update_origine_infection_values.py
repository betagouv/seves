import random

from django.db import migrations, models


def replace_old_origines_infection(apps, schema_editor):
    EvenementAnimal = apps.get_model("sa", "EvenementAnimal")
    new_values = [value for value, _ in EvenementAnimal._meta.get_field("origine_infection").choices]
    evenements = list(EvenementAnimal.objects.exclude(origine_infection__in=["", *new_values]))
    for evenement in evenements:
        evenement.origine_infection = random.choice(new_values)
    EvenementAnimal.objects.bulk_update(evenements, ["origine_infection"])


class Migration(migrations.Migration):
    dependencies = [
        ("sa", "0051_evenementanimal_import_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="evenementanimal",
            name="origine_infection",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ALIMENTATION_DECHETS_ALIMENTAIRES", "Alimentation à base de déchets alimentaires"),
                    (
                        "ALIMENTATION_PRODUITS_CRUS_AQUATIQUES",
                        "Alimentation à base de produits crus d'origine aquatique",
                    ),
                    ("ANIMAUX_EN_TRANSIT", "Animaux en transit"),
                    ("CONTACT_ESPECES_SAUVAGES", "Contact avec des espèces sauvages"),
                    ("CONTACT_ETABLISSEMENT_VOISIN_INFECTE", "Contact avec un établissement voisin infecté"),
                    (
                        "CONTACT_ANIMAUX_INFECTES_PATURAGE_ABREUVEMENT",
                        "Contact avec un ou des animaux infectés sur des lieux de pâturage ou d’abreuvement",
                    ),
                    ("DEPLACEMENT_ILLEGAL_ANIMAUX", "Déplacement illégal d’animaux"),
                    ("DEPLACEMENT_LEGAL_ANIMAUX", "Déplacement légal d’animaux"),
                    ("INCONNU_OU_NON_CONCLUANT", "Inconnu ou non concluant"),
                    ("INTRODUCTION_ANIMAUX_VIVANTS", "Introduction de nouveaux animaux vivants"),
                    (
                        "INTRODUCTION_PRODUITS_ANIMAUX_NON_VIABLES",
                        "Introduction de nouveaux produits d’origine animale non viables",
                    ),
                    ("PROPAGATION_HORIZONTALE_EAU", "Propagation horizontale par l’eau"),
                    ("PROPAGATION_AERIENNE", "Propagation par voie aérienne"),
                    (
                        "TRANSMISSION_VERTICALE_APPARENTE",
                        "Transmission verticale apparente (via des œufs ou des gamètes contaminés)",
                    ),
                    (
                        "TRANSMISSION_VERTICALE_VRAIE",
                        "Transmission verticale vraie (via des œufs ou des gamètes infectés)",
                    ),
                    ("VECTEUR_PASSIF", "Vecteur passif de transmission (humains, véhicules, aliments, etc.)"),
                    ("VECTEURS", "Vecteurs"),
                    ("AUTRE", "Autre"),
                ],
                max_length=100,
                verbose_name="Origine de l'infection",
            ),
        ),
        migrations.RunPython(replace_old_origines_infection, migrations.RunPython.noop),
    ]
