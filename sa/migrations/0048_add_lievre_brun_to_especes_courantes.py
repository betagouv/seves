from django.db import migrations

LIEVRE_BRUN = "Lièvre brun (Lièvre d'Europe) (Lepus europaeus)"
MALADIES = ["Tularémie", "Myxomatose", "Rage"]


def add_lievre_brun_to_especes_courantes(apps, schema_editor):
    Espece = apps.get_model("sa", "Espece")
    Maladie = apps.get_model("sa", "Maladie")

    try:
        espece = Espece.objects.get(name=LIEVRE_BRUN)
    except Espece.DoesNotExist:
        raise RuntimeError(f"Espèce introuvable dans le référentiel: {LIEVRE_BRUN}")
    espece.is_highlighted = True
    espece.save()

    maladies = list(Maladie.objects.filter(name__in=MALADIES))
    missing_maladies = set(MALADIES) - {maladie.name for maladie in maladies}
    if missing_maladies:
        raise RuntimeError(f"Maladies introuvables: {sorted(missing_maladies)}")
    espece.maladies_concernees.add(*maladies)


class Migration(migrations.Migration):
    dependencies = [
        ("sa", "0047_populate_maladie_laboratoires_frequents"),
    ]

    operations = [
        migrations.RunPython(add_lievre_brun_to_especes_courantes, migrations.RunPython.noop),
    ]
