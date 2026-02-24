from logging import getLogger
import re

import django.core.validators
from django.db import migrations, models

logger = getLogger(__name__)


def populate_commmunes(apps, _):
    from core.migrations import libelle_pre_proccess

    SSAEtablissement = apps.get_model("ssa", "Etablissement")
    TIACEtablissement = apps.get_model("tiac", "Etablissement")
    Lieu = apps.get_model("sv", "Lieu")
    Commune = apps.get_model("core", "Commune")

    code_insee_list = {
        *SSAEtablissement.objects.exclude(code_insee="").distinct().values_list("code_insee", flat=True),
        *TIACEtablissement.objects.exclude(code_insee="").distinct().values_list("code_insee", flat=True),
        *Lieu.objects.exclude(code_insee="").distinct().values_list("code_insee", flat=True),
    }

    commune_without_code_insee = set()
    (SSAEtablissement.objects.filter(code_insee="").distinct().values_list("commune", flat=True),)
    (TIACEtablissement.objects.filter(code_insee="").distinct().values_list("commune", flat=True),)

    for Model in (TIACEtablissement, SSAEtablissement, Lieu):
        commune_without_code_insee.update(
            Model.objects.annotate(libelle=libelle_pre_proccess("commune"))
            .filter(code_insee="")
            .exclude(libelle="")
            .distinct()
            .values_list("libelle", flat=True)
        )

    if len(code_insee_list) + len(commune_without_code_insee) > 0:
        import json

        from django.conf import settings

        result = {}

        with open(settings.BASE_DIR / "core/seeds/codes-postaux.json") as f:
            cp_json = json.load(f)

        for code in code_insee_list:
            data = cp_json.get(code)
            if not data:
                logger.warn(f"Unknown INSEE code: {code}")
                continue
            result[data["codeCommune"]] = Commune(
                nom=data["nomCommune"],
                libelle_acheminement=data["libelleAcheminement"],
                code_insee=data["codeCommune"],
                code_postal=data["codePostal"],
            )

        if len(commune_without_code_insee) > 0:
            by_libelle_postal = {re.sub(r"\W+", " ", it["libelleAcheminement"]).upper(): it for it in cp_json.values()}

            for libelle in commune_without_code_insee:
                data = by_libelle_postal.get(libelle)
                if not data:
                    logger.warn(f"Unknown libelle postal: {libelle}")
                    continue
                result[data["codeCommune"]] = Commune(
                    nom=data["nomCommune"],
                    libelle_acheminement=data["libelleAcheminement"],
                    code_insee=data["codeCommune"],
                    code_postal=data["codePostal"],
                )

        Commune.objects.bulk_create(result.values())


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0051_auto_20260212_0918"),
    ]

    operations = [
        migrations.CreateModel(
            name="Commune",
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
                    "libelle_acheminement",
                    models.CharField(blank=True, max_length=100, verbose_name="Libellé de tri postal"),
                ),
                (
                    "code_insee",
                    models.CharField(
                        unique=True,
                        blank=True,
                        max_length=5,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="code_postal_must_be_valid_or_empty",
                                message="Le code INSEE doit être valide",
                                regex="^((?:\\d{5}|2A\\d{3}|2B\\d{3}))?$",
                            )
                        ],
                        verbose_name="Code INSEE de la commune",
                    ),
                ),
                (
                    "code_postal",
                    models.CharField(
                        blank=True,
                        max_length=5,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="code_postal_must_be_valid_or_empty",
                                message="Le code postal doit être valide ou vide",
                                regex="^((?:\\d{5}))?$",
                            )
                        ],
                        verbose_name="Code INSEE de la commune",
                    ),
                ),
            ],
        ),
        migrations.RunPython(populate_commmunes),
    ]
