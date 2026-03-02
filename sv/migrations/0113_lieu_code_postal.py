import logging
from logging import getLogger

import django.core.validators
from django.db import migrations, models

logger = getLogger("sv.migrations.0113_lieu_code_postal")


def populate_commmunes(apps, _):
    Lieu = apps.get_model("sv", "Lieu")

    code_insee_list = set(Lieu.objects.exclude(code_insee="").distinct().values_list("code_insee", flat=True))

    if len(code_insee_list) > 0:
        import json

        from django.conf import settings

        with open(settings.BASE_DIR / "core/seeds/codes-postaux.json") as f:
            cp_json = json.load(f)

        count = 0
        for code in code_insee_list:
            data = cp_json.get(code)
            if not data:
                logger.warning(f"Unknown INSEE code: {code}")
                continue
            count += Lieu.objects.filter(code_insee=code).update(code_postal=data["codePostal"])
        logging.info(f"Updated {count} records from code_insee")


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0112_auto_20260114_1435"),
    ]

    operations = [
        migrations.AddField(
            model_name="lieu",
            name="code_postal",
            field=models.CharField(
                blank=True,
                max_length=5,
                validators=[
                    django.core.validators.RegexValidator(
                        code="invalid_code_postal",
                        message="Le code postal doit être valide",
                        regex="^(?:\\d{5})$",
                    )
                ],
                verbose_name="Code postal de la commune",
            ),
        ),
        migrations.AlterField(
            model_name="lieu",
            name="departement",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="%(app_label)s_%(class)s_set",
                to="core.departement",
                verbose_name="Département",
            ),
        ),
        migrations.RunPython(populate_commmunes, reverse_code=migrations.RunPython.noop),
    ]
