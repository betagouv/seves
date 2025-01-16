# Generated by Django 5.1.4 on 2025-01-16 14:56

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def add_on_and_statut(apps, schema_editor):
    Evenement = apps.get_model("sv", "Evenement")
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    StatutReglementaire = apps.get_model("sv", "StatutReglementaire")
    statut = StatutReglementaire.objects.get(code="OQ")
    organisme = OrganismeNuisible.objects.get(code_oepp="XYLEFM")

    evenements = Evenement.objects.filter(Q(organisme_nuisible__isnull=True) | Q(statut_reglementaire__isnull=True))
    for evenement in evenements:
        if evenement.organisme_nuisible is None:
            evenement.organisme_nuisible = organisme
        if evenement.statut_reglementaire is None:
            evenement.statut_reglementaire = statut
        evenement.save()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0062_evenement_is_deleted"),
    ]

    operations = [
        migrations.RunPython(add_on_and_statut, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="evenement",
            name="organisme_nuisible",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.organismenuisible",
                verbose_name="OEPP",
            ),
        ),
        migrations.AlterField(
            model_name="evenement",
            name="statut_reglementaire",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.statutreglementaire",
                verbose_name="Statut règlementaire de l'organisme",
            ),
        ),
    ]
