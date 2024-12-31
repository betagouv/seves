# Generated by Django 5.1.4 on 2025-01-02 10:16

import core.mixins
import django.db.models.deletion
import sv.models.common
from django.db import migrations, models


def add_initial_evenements(apps, schema_editor):
    Evenement = apps.get_model("sv", "Evenement")
    FicheDetection = apps.get_model("sv", "FicheDetection")

    for fiche in FicheDetection.objects.all():
        evenement = Evenement.objects.create(
            organisme_nuisible=fiche.organisme_nuisible,
            statut_reglementaire=fiche.statut_reglementaire,
            visibilite=fiche.visibilite,
            createur=fiche.createur,
        )
        fiche.evenement = evenement
        fiche.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_alter_document_document_type"),
        ("sv", "0058_laboratoire_remove_prelevement_laboratoire_agree_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Evenement",
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
                ("is_ac_notified", models.BooleanField(default=False)),
                (
                    "visibilite",
                    models.CharField(
                        choices=[
                            (
                                "brouillon",
                                "Vous seul pourrez voir la fiche et la modifier",
                            ),
                            (
                                "local",
                                "Seul votre structure et l'administration centrale pourront consulter et modifier la fiche",
                            ),
                            (
                                "national",
                                "La fiche sera et modifiable par toutes les structures",
                            ),
                        ],
                        default="brouillon",
                        max_length=100,
                    ),
                ),
                (
                    "date_creation",
                    models.DateTimeField(auto_now_add=True, verbose_name="Date de création"),
                ),
            ],
            options={
                "verbose_name": "Évènement",
                "verbose_name_plural": "Évènements",
            },
            bases=(core.mixins.WithMessageUrlsMixin, models.Model),
        ),
        migrations.RemoveConstraint(
            model_name="fichedetection",
            name="check_numero_fiche_is_null_when_visibilite_is_brouillon",
        ),
        migrations.RemoveConstraint(
            model_name="fichezonedelimitee",
            name="check_fiche_zone_delimitee_numero_fiche_is_null_when_visibilite_is_brouillon",
        ),
        migrations.RemoveField(
            model_name="fichedetection",
            name="contacts",
        ),
        migrations.RemoveField(
            model_name="fichedetection",
            name="etat",
        ),
        migrations.RemoveField(
            model_name="fichedetection",
            name="is_ac_notified",
        ),
        migrations.RemoveField(
            model_name="fichezonedelimitee",
            name="contacts",
        ),
        migrations.RemoveField(
            model_name="fichezonedelimitee",
            name="etat",
        ),
        migrations.RemoveField(
            model_name="fichezonedelimitee",
            name="organisme_nuisible",
        ),
        migrations.RemoveField(
            model_name="fichezonedelimitee",
            name="statut_reglementaire",
        ),
        migrations.RemoveField(
            model_name="fichezonedelimitee",
            name="visibilite",
        ),
        migrations.AddField(
            model_name="evenement",
            name="contacts",
            field=models.ManyToManyField(blank=True, to="core.contact", verbose_name="Contacts"),
        ),
        migrations.AddField(
            model_name="evenement",
            name="createur",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="core.structure",
                verbose_name="Structure créatrice",
            ),
        ),
        migrations.AddField(
            model_name="evenement",
            name="etat",
            field=models.ForeignKey(
                default=sv.models.common.Etat.get_etat_initial,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.etat",
                verbose_name="État de la fiche",
            ),
        ),
        migrations.AddField(
            model_name="evenement",
            name="fiche_zone_delimitee",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.fichezonedelimitee",
                verbose_name="Fiche zone delimitée",
            ),
        ),
        migrations.AddField(
            model_name="evenement",
            name="numero",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.numerofiche",
                verbose_name="Numéro de fiche",
            ),
        ),
        migrations.AddField(
            model_name="evenement",
            name="organisme_nuisible",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.organismenuisible",
                verbose_name="OEPP",
            ),
        ),
        migrations.AddField(
            model_name="evenement",
            name="statut_reglementaire",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.statutreglementaire",
                verbose_name="Statut règlementaire de l'organisme",
            ),
        ),
        migrations.AddField(
            model_name="fichedetection",
            name="evenement",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="detections",
                to="sv.evenement",
            ),
        ),
        migrations.AddConstraint(
            model_name="evenement",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("visibilite", "brouillon"),
                    ("numero__isnull", False),
                    _negated=True,
                ),
                name="check_evenement_numero_fiche_is_null_when_visibilite_is_brouillon",
            ),
        ),
        migrations.RunPython(add_initial_evenements, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="fichedetection",
            name="organisme_nuisible",
        ),
        migrations.RemoveField(
            model_name="fichedetection",
            name="statut_reglementaire",
        ),
        migrations.RemoveField(
            model_name="fichedetection",
            name="visibilite",
        ),
        migrations.AlterField(
            model_name="fichedetection",
            name="evenement",
            field=models.ForeignKey(
                null=False,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.evenement",
            ),
        ),
    ]
