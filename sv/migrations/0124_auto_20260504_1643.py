from django.db import migrations

from sv.constants import SiteInspection


def prevent_empty_site_inspection(apps, _):
    Lieu = apps.get_model("sv", "Lieu")
    Lieu.objects.filter(site_inspection="").update(site_inspection=SiteInspection.INCONNU)


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0123_alter_lieu_site_inspection"),
    ]

    operations = [migrations.RunPython(prevent_empty_site_inspection, reverse_code=migrations.RunPython.noop)]
