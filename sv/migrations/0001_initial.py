# Generated by Django 5.0.3 on 2024-04-11 20:02

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Administration",
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
                ("nom", models.CharField(max_length=100, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Administration",
                "verbose_name_plural": "Administrations",
            },
        ),
        migrations.CreateModel(
            name="Contexte",
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
                ("nom", models.CharField(max_length=100, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Contexte",
                "verbose_name_plural": "Contextes",
            },
        ),
        migrations.CreateModel(
            name="Departement",
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
                    "numero",
                    models.CharField(max_length=3, unique=True, verbose_name="Numéro"),
                ),
                (
                    "nom",
                    models.CharField(max_length=100, unique=True, verbose_name="Nom"),
                ),
            ],
            options={
                "verbose_name": "Département",
                "verbose_name_plural": "Départements",
                "ordering": ["numero"],
            },
        ),
        migrations.CreateModel(
            name="EspeceEchantillon",
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
                    "code_oepp",
                    models.CharField(max_length=100, verbose_name="Code OEPP"),
                ),
                ("libelle", models.CharField(max_length=100, verbose_name="Libellé")),
            ],
            options={
                "verbose_name": "Espèce de l'échantillon",
                "verbose_name_plural": "Espèces de l'échantillon",
                "db_table": "sv_espece_echantillon",
            },
        ),
        migrations.CreateModel(
            name="LaboratoireAgree",
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
                ("nom", models.CharField(max_length=100, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Laboratoire agréé",
                "verbose_name_plural": "Laboratoires agréés",
                "db_table": "sv_laboratoire_agree",
                "ordering": ["nom"],
            },
        ),
        migrations.CreateModel(
            name="LaboratoireConfirmationOfficielle",
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
                ("nom", models.CharField(max_length=100, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Laboratoire de confirmation officielle",
                "verbose_name_plural": "Laboratoires de confirmation officielle",
                "db_table": "sv_laboratoire_confirmation_officielle",
                "ordering": ["nom"],
            },
        ),
        migrations.CreateModel(
            name="MatricePrelevee",
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
                ("libelle", models.CharField(max_length=100, verbose_name="Libellé")),
            ],
            options={
                "verbose_name": "Matrice prélevée",
                "verbose_name_plural": "Matrices prélevées",
                "db_table": "sv_matrice_prelevee",
            },
        ),
        migrations.CreateModel(
            name="OrganismeNuisible",
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
                ("code_oepp", models.CharField(verbose_name="Code OEPP")),
                ("libelle_court", models.CharField(max_length=255, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Organisme nuisible",
                "verbose_name_plural": "Organismes nuisibles",
                "db_table": "sv_organisme_nuisible",
            },
        ),
        migrations.CreateModel(
            name="PositionChaineDistribution",
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
                ("libelle", models.CharField(max_length=100, verbose_name="Libellé")),
            ],
            options={
                "verbose_name": "Position dans la chaîne de distribution",
                "verbose_name_plural": "Positions dans la chaîne de distribution",
                "db_table": "sv_position_chaine_distribution",
            },
        ),
        migrations.CreateModel(
            name="Region",
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
                    "nom",
                    models.CharField(max_length=100, unique=True, verbose_name="Nom"),
                ),
            ],
            options={
                "verbose_name": "Région",
                "verbose_name_plural": "Régions",
                "ordering": ["nom"],
            },
        ),
        migrations.CreateModel(
            name="SiteInspection",
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
                ("nom", models.CharField(max_length=100, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Site d'inspection",
                "verbose_name_plural": "Sites d'inspection",
                "db_table": "sv_site_inspection",
            },
        ),
        migrations.CreateModel(
            name="StatutEtablissement",
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
                ("libelle", models.CharField(max_length=100, verbose_name="Libellé")),
            ],
            options={
                "verbose_name": "Statut de l'établissement",
                "verbose_name_plural": "Statuts de l'établissement",
                "db_table": "sv_statut_etablissement",
            },
        ),
        migrations.CreateModel(
            name="StatutEvenement",
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
                ("libelle", models.CharField(max_length=100, verbose_name="Libellé")),
            ],
            options={
                "verbose_name": "Statut de l'événement",
                "verbose_name_plural": "Statuts de l'événement",
                "db_table": "sv_statut_evenement",
            },
        ),
        migrations.CreateModel(
            name="StatutReglementaire",
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
                ("code", models.CharField(max_length=10, verbose_name="Code")),
                ("libelle", models.CharField(max_length=100, verbose_name="Libellé")),
            ],
            options={
                "verbose_name": "Statut règlementaire de l'organisme",
                "verbose_name_plural": "Statuts règlementaires de l'organisme",
                "db_table": "sv_statut_reglementaire",
            },
        ),
        migrations.CreateModel(
            name="StructurePreleveur",
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
                ("nom", models.CharField(max_length=100, verbose_name="Nom")),
            ],
            options={
                "verbose_name": "Structure préleveur",
                "verbose_name_plural": "Structures préleveur",
                "db_table": "sv_structure_preleveur",
                "ordering": ["nom"],
            },
        ),
        migrations.CreateModel(
            name="TypeExploitant",
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
                ("libelle", models.CharField(max_length=100, verbose_name="Libellé")),
            ],
            options={
                "verbose_name": "Type d'exploitant",
                "verbose_name_plural": "Types d'exploitant",
                "db_table": "sv_type_exploitant",
            },
        ),
        migrations.CreateModel(
            name="FicheDetection",
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
                    "numero_europhyt",
                    models.CharField(blank=True, max_length=8, verbose_name="Numéro Europhyt"),
                ),
                (
                    "numero_rasff",
                    models.CharField(blank=True, max_length=9, verbose_name="Numéro RASFF"),
                ),
                (
                    "date_premier_signalement",
                    models.DateField(blank=True, null=True, verbose_name="Date premier signalement"),
                ),
                (
                    "commentaire",
                    models.TextField(blank=True, verbose_name="Commentaire"),
                ),
                (
                    "mesures_conservatoires_immediates",
                    models.TextField(blank=True, verbose_name="Mesures conservatoires immédiates"),
                ),
                (
                    "mesures_consignation",
                    models.TextField(blank=True, verbose_name="Mesures de consignation"),
                ),
                (
                    "mesures_phytosanitaires",
                    models.TextField(blank=True, verbose_name="Mesures phytosanitaires"),
                ),
                (
                    "mesures_surveillance_specifique",
                    models.TextField(blank=True, verbose_name="Mesures de surveillance spécifique"),
                ),
                (
                    "contexte",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.contexte",
                        verbose_name="Contexte",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fiche détection",
                "verbose_name_plural": "Fiches détection",
                "db_table": "sv_fiche_detection",
            },
        ),
        migrations.CreateModel(
            name="Lieu",
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
                    "nom",
                    models.CharField(blank=True, max_length=100, verbose_name="Nom"),
                ),
                (
                    "wgs84_longitude",
                    models.FloatField(blank=True, null=True, verbose_name="Longitude WGS84"),
                ),
                (
                    "wgs84_latitude",
                    models.FloatField(blank=True, null=True, verbose_name="Latitude WGS84"),
                ),
                (
                    "adresse_lieu_dit",
                    models.CharField(blank=True, max_length=100, verbose_name="Adresse ou lieu-dit"),
                ),
                ("commune", models.CharField(max_length=100, verbose_name="Commune")),
                (
                    "code_insee",
                    models.CharField(
                        blank=True,
                        max_length=5,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_code_insee",
                                message="Le code INSEE doit contenir exactement 5 chiffres",
                                regex="^[0-9]{5}$",
                            )
                        ],
                        verbose_name="Code INSEE de la commune",
                    ),
                ),
                (
                    "departement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.departement",
                        verbose_name="Département",
                    ),
                ),
                (
                    "fiche_detection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lieux",
                        to="sv.fichedetection",
                        verbose_name="Fiche de détection",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lieu",
                "verbose_name_plural": "Lieux",
            },
        ),
        migrations.CreateModel(
            name="NumeroFiche",
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
                ("annee", models.IntegerField(verbose_name="Année")),
                ("numero", models.IntegerField(verbose_name="Numéro")),
            ],
            options={
                "verbose_name": "Numéro de fiche",
                "verbose_name_plural": "Numéros de fiche",
                "db_table": "sv_numero_fiche",
                "unique_together": {("annee", "numero")},
            },
        ),
        migrations.AddField(
            model_name="fichedetection",
            name="numero",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.numerofiche",
                verbose_name="Numéro de fiche",
            ),
        ),
        migrations.AddField(
            model_name="fichedetection",
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
            model_name="departement",
            name="region",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.region",
                verbose_name="Région",
            ),
        ),
        migrations.AddField(
            model_name="fichedetection",
            name="statut_evenement",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.statutevenement",
                verbose_name="Statut de l'événement",
            ),
        ),
        migrations.AddField(
            model_name="fichedetection",
            name="statut_reglementaire",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.statutreglementaire",
                verbose_name="Statut règlementaire de l'organisme",
            ),
        ),
        migrations.CreateModel(
            name="PrelevementOfficiel",
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
                    "numero_echantillon",
                    models.CharField(blank=True, max_length=100, verbose_name="Numéro d'échantillon"),
                ),
                (
                    "date_prelevement",
                    models.DateField(blank=True, null=True, verbose_name="Date de prélèvement"),
                ),
                (
                    "numero_phytopass",
                    models.CharField(blank=True, max_length=100, verbose_name="Numéro Phytopass"),
                ),
                (
                    "espece_echantillon",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.especeechantillon",
                        verbose_name="Espèce de l'échantillon",
                    ),
                ),
                (
                    "fiche_detection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sv.fichedetection",
                        verbose_name="Fiche de détection",
                    ),
                ),
                (
                    "laboratoire_agree",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.laboratoireagree",
                        verbose_name="Laboratoire agréé",
                    ),
                ),
                (
                    "laboratoire_confirmation_officielle",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.laboratoireconfirmationofficielle",
                        verbose_name="Laboratoire de confirmation officielle",
                    ),
                ),
                (
                    "lieu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sv.lieu",
                        verbose_name="Lieu",
                    ),
                ),
                (
                    "matrice_prelevee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.matriceprelevee",
                        verbose_name="Matrice prélevée",
                    ),
                ),
                (
                    "site_inspection",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.siteinspection",
                        verbose_name="Site d'inspection",
                    ),
                ),
                (
                    "structure_preleveur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.structurepreleveur",
                        verbose_name="Structure préleveur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prélèvement officiel",
                "verbose_name_plural": "Prélèvements officiels",
                "db_table": "sv_prelevement_officiel",
            },
        ),
        migrations.CreateModel(
            name="PrelevementNonOfficiel",
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
                    "numero_echantillon",
                    models.CharField(blank=True, max_length=100, verbose_name="Numéro d'échantillon"),
                ),
                (
                    "date_prelevement",
                    models.DateField(blank=True, null=True, verbose_name="Date de prélèvement"),
                ),
                (
                    "espece_echantillon",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.especeechantillon",
                        verbose_name="Espèce de l'échantillon",
                    ),
                ),
                (
                    "fiche_detection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sv.fichedetection",
                        verbose_name="Fiche de détection",
                    ),
                ),
                (
                    "lieu",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sv.lieu",
                        verbose_name="Lieu",
                    ),
                ),
                (
                    "matrice_prelevee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.matriceprelevee",
                        verbose_name="Matrice prélevée",
                    ),
                ),
                (
                    "site_inspection",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.siteinspection",
                        verbose_name="Site d'inspection",
                    ),
                ),
                (
                    "structure_preleveur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.structurepreleveur",
                        verbose_name="Structure préleveur",
                    ),
                ),
            ],
            options={
                "verbose_name": "Prélèvement non officiel",
                "verbose_name_plural": "Prélèvements non officiels",
                "db_table": "sv_prelevement_non_officiel",
            },
        ),
        migrations.CreateModel(
            name="Etablissement",
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
                    "nom",
                    models.CharField(blank=True, max_length=100, verbose_name="Nom"),
                ),
                (
                    "activite",
                    models.CharField(blank=True, max_length=100, verbose_name="Activité"),
                ),
                (
                    "pays",
                    models.CharField(blank=True, max_length=100, verbose_name="Pays"),
                ),
                (
                    "raison_sociale",
                    models.CharField(blank=True, max_length=100, verbose_name="Raison sociale"),
                ),
                (
                    "adresse",
                    models.CharField(blank=True, max_length=100, verbose_name="Adresse"),
                ),
                (
                    "identifiant",
                    models.CharField(blank=True, max_length=100, verbose_name="Identifiant"),
                ),
                (
                    "fiche_detection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="sv.fichedetection",
                        verbose_name="Fiche de détection",
                    ),
                ),
                (
                    "position_chaine_distribution",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.positionchainedistribution",
                        verbose_name="Position dans la chaîne de distribution",
                    ),
                ),
                (
                    "statut",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.statutetablissement",
                        verbose_name="Statut",
                    ),
                ),
                (
                    "type_exploitant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.typeexploitant",
                        verbose_name="Type d'exploitant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Etablissement",
                "verbose_name_plural": "Etablissements",
            },
        ),
        migrations.CreateModel(
            name="Unite",
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
                ("nom", models.CharField(max_length=100, verbose_name="Nom")),
                (
                    "type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="sv.administration",
                        verbose_name="Type",
                    ),
                ),
            ],
            options={
                "verbose_name": "Unité",
                "verbose_name_plural": "Unités",
                "ordering": ["-type", "nom"],
            },
        ),
        migrations.AddField(
            model_name="fichedetection",
            name="createur",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="sv.unite",
                verbose_name="Créateur",
            ),
        ),
    ]
