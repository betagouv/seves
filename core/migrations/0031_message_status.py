# Generated by Django 5.1.8 on 2025-05-13 09:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0030_auto_20250429_1648"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="status",
            field=models.CharField(
                choices=[("brouillon", "Brouillon"), ("finalise", "Finalisé")],
                default="finalise",
                max_length=20,
                verbose_name="Statut",
            ),
        ),
    ]
