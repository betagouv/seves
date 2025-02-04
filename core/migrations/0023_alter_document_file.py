# Generated by Django 5.1.5 on 2025-02-04 14:05

import core.storage
import core.validators
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0022_alter_document_document_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="file",
            field=models.FileField(
                upload_to=core.storage.get_timestamped_filename,
                validators=[
                    core.validators.validate_upload_file,
                    django.core.validators.FileExtensionValidator(
                        [
                            "png",
                            "jpg",
                            "jpeg",
                            "gif",
                            "pdf",
                            "doc",
                            "docx",
                            "xls",
                            "xlsx",
                            "odt",
                            "ods",
                            "csv",
                            "qgs",
                            "qgz",
                        ]
                    ),
                ],
            ),
        ),
    ]
