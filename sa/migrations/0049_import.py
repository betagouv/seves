import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0069_message_read"),
        ("sa", "0048_add_lievre_brun_to_especes_courantes"),
    ]

    operations = [
        migrations.CreateModel(
            name="Import",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "file",
                    models.FileField(
                        upload_to="sa/imports/",
                        validators=[django.core.validators.FileExtensionValidator(["csv"])],
                        verbose_name="Fichier",
                    ),
                ),
                ("date_creation", models.DateTimeField(auto_now_add=True, verbose_name="Date de création")),
                (
                    "createur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.structure",
                        verbose_name="Structure créatrice",
                    ),
                ),
            ],
            options={
                "verbose_name": "Import",
                "verbose_name_plural": "Imports",
            },
        ),
    ]
