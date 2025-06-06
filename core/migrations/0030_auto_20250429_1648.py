# Generated by Django 5.1.8 on 2025-04-29 14:48

from django.db import migrations
from django.contrib.postgres.operations import UnaccentExtension


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0029_create_referent_national_group"),
    ]

    operations = [
        UnaccentExtension(),
        migrations.RunSQL("CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french );"),
        migrations.RunSQL(
            "ALTER TEXT SEARCH CONFIGURATION french_unaccent ALTER MAPPING FOR hword, hword_part, word WITH unaccent, french_stem;"
        ),
    ]
