from django.db import migrations


ON = (
    {
        "code_oepp": "ACEETW",
        "libelle_long": "Aclees taiwanensis (charançon noir du figuier)",
        "libelle_court": "Aclees taiwanensis",
    },
    {
        "code_oepp": "RICASC",
        "libelle_long": "Ricania speculum",
        "libelle_court": "Ricania speculum",
    },
)


def add_new_organismes_nuisibles(apps, _):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    for on in ON:
        OrganismeNuisible.objects.get_or_create(
            code_oepp=on["code_oepp"],
            defaults={"libelle_long": on["libelle_long"], "libelle_court": on["libelle_court"]},
        )


def reverse_add_new_organismes_nuisibles(apps, schema_editor):
    OrganismeNuisible = apps.get_model("sv", "OrganismeNuisible")
    for on in ON:
        OrganismeNuisible.objects.get_or_create(
            code_oepp=on["code_oepp"],
            defaults={"libelle_long": on["libelle_long"], "libelle_court": on["libelle_court"]},
        )
        OrganismeNuisible.objects.filter(code_oepp=on["code_oepp"], libelle_court=on["libelle_court"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sv", "0102_auto_20250619_1023"),
    ]

    operations = [
        migrations.RunPython(add_new_organismes_nuisibles, reverse_add_new_organismes_nuisibles),
    ]
