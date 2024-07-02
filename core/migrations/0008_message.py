# Generated by Django 5.0.3 on 2024-07-03 09:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("core", "0007_alter_document_document_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="Message",
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
                    "message_type",
                    models.CharField(
                        choices=[("message", "Message"), ("note", "Note")],
                        max_length=100,
                    ),
                ),
                ("title", models.CharField(max_length=512)),
                ("content", models.TextField()),
                (
                    "date_creation",
                    models.DateTimeField(auto_now_add=True, verbose_name="Date de création"),
                ),
                ("object_id", models.PositiveIntegerField()),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "ordering": ["-date_creation"],
                "indexes": [
                    models.Index(
                        fields=["content_type", "object_id"],
                        name="core_messag_content_b4320c_idx",
                    )
                ],
            },
        ),
    ]