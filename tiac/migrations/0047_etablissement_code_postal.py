import logging
from logging import getLogger

import django.core.validators
from django.db import migrations, models

logger = getLogger("tiac.migrations.0047_etablissement_code_postal")


def populate_code_postal(apps, _):
    Etablissement = apps.get_model("tiac", "Etablissement")

    code_insee_list = set(Etablissement.objects.exclude(code_insee="").distinct().values_list("code_insee", flat=True))

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
            count += Etablissement.objects.filter(code_insee=code).update(code_postal=data["codePostal"])
        logging.info(f"Updated {count} records from code_insee")


class Migration(migrations.Migration):
    dependencies = [
        ("tiac", "0046_alter_evenementsimple_follow_up"),
    ]

    operations = [
        migrations.AddField(
            model_name="etablissement",
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
            model_name="etablissement",
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
        migrations.RunPython(populate_code_postal, reverse_code=migrations.RunPython.noop),
    ]
