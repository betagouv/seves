# Generated by Django 5.0.3 on 2024-10-28 09:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0025_zoneinfestee_rayon_zoneinfestee_unite_rayon_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="structurepreleveur",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
