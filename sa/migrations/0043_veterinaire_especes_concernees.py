from django.db import migrations, models


def link_veterinaires_to_especes_concernees(apps, schema_editor):
    Veterinaire = apps.get_model("sa", "Veterinaire")
    EspeceConcernee = apps.get_model("sa", "EspeceConcernee")
    for veterinaire in Veterinaire.objects.prefetch_related("especes"):
        veterinaire.especes_concernees.set(
            EspeceConcernee.objects.filter(evenement_id=veterinaire.evenement_id, espece__in=veterinaire.especes.all())
        )


def link_veterinaires_to_especes(apps, schema_editor):
    Veterinaire = apps.get_model("sa", "Veterinaire")
    for veterinaire in Veterinaire.objects.prefetch_related("especes_concernees"):
        veterinaire.especes.set(
            {espece_concernee.espece_id for espece_concernee in veterinaire.especes_concernees.all()}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("sa", "0042_evenementanimal_dates_arretes_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="veterinaire",
            name="especes_concernees",
            field=models.ManyToManyField(
                blank=True, related_name="veterinaires", to="sa.espececoncernee", verbose_name="Espèces"
            ),
        ),
        migrations.RunPython(link_veterinaires_to_especes_concernees, link_veterinaires_to_especes),
        migrations.RemoveField(
            model_name="veterinaire",
            name="especes",
        ),
    ]
