from django.db import migrations


def remove_on_psdms2(apps, _):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.filter(code_oepp="PSDMS2").delete()


def readd_on_psdms2(apps, _):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    OrganismeNuisible.objects.get_or_create(
        code_oepp="PSDMS2",
        libelle_long="Ralstonia solanacearum race 2 (no longer in use) (maladie de Moko du bananier)",
        libelle_court="Ralstonia solanacearum race 2",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0116_auto_20260323_0921"),
    ]

    operations = [migrations.RunPython(remove_on_psdms2, reverse_code=readd_on_psdms2)]
