from django.db import migrations


def add_organismes_nuisibles(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.get_or_create(
        code_oepp="PUCCKU",
        defaults={
            "libelle_court": "Puccinia kuehnii",
            "libelle_long": "Puccinia kuehnii",
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0129_auto_20260619_1521"),
    ]

    operations = [
        migrations.RunPython(add_organismes_nuisibles, reverse_code=migrations.RunPython.noop),
    ]
