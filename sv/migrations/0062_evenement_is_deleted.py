# Generated by Django 5.1.4 on 2025-01-10 10:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0061_update_laboratoires_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="evenement",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
    ]
