from django.conf import settings
from django.contrib.auth.models import Group
from django.db import migrations


def create_group(apps, schema_editor):
    Group.objects.get_or_create(name=settings.SA_GROUP)


def remove_group(apps, schema_editor):
    Group.objects.filter(name=settings.SA_GROUP).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0064_auto_20260727_1357"),
    ]

    operations = [migrations.RunPython(create_group, remove_group)]
