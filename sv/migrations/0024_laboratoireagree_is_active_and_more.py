# Generated by Django 5.0.3 on 2024-10-17 13:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0023_prelevement_numero_resytal"),
    ]

    operations = [
        migrations.AddField(
            model_name="laboratoireagree",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="laboratoireconfirmationofficielle",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]
