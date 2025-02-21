# Generated by Django 5.1.4 on 2025-02-03 15:02
import datetime
from django.db import migrations, models


def add_fake_numero(apps, schema_editor):
    Evenement = apps.get_model("sv", "Evenement")

    for evenement in Evenement._base_manager.all():
        annee_courante = datetime.datetime.now().year
        last_fiche = Evenement.objects.filter(numero_annee=annee_courante).order_by("-numero_evenement").first()
        numero_evenement = last_fiche.numero_evenement + 1 if last_fiche else 1
        evenement.numero_evenement = numero_evenement
        evenement.numero_annee = annee_courante
        evenement.save()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0072_remove_fichezonedelimitee_numero"),
    ]

    operations = [
        migrations.AddField(
            model_name="evenement",
            name="numero_annee",
            field=models.IntegerField(null=True, verbose_name="Année"),
        ),
        migrations.AddField(
            model_name="evenement",
            name="numero_evenement",
            field=models.IntegerField(null=True, verbose_name="Numéro"),
        ),
        migrations.AddConstraint(
            model_name="evenement",
            constraint=models.UniqueConstraint(
                fields=("numero_annee", "numero_evenement"),
                name="unique_evenement_numero",
            ),
        ),
        migrations.RemoveField(
            model_name="evenement",
            name="numero",
        ),
        migrations.RunPython(add_fake_numero, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="evenement",
            name="numero_annee",
            field=models.IntegerField(verbose_name="Année"),
        ),
        migrations.AlterField(
            model_name="evenement",
            name="numero_evenement",
            field=models.IntegerField(verbose_name="Numéro"),
        ),
    ]
