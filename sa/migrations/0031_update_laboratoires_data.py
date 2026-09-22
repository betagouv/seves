from django.db import migrations

NEW_ANSES_SITES = [
    ("LNR_ANSES_PLOUFRAGAN", "ANSES Ploufragan"),
    ("LNR_ANSES_PLOUZANE", "ANSES Plouzané"),
    ("LNR_ANSES_NIORT", "ANSES Niort"),
]

MERGED_LABORATOIRE = {
    "name": "ANSES PLOUFRAGAN - PLOUZANÉ - NIORT",
    "external_id": "LNR_ANSES_PLOUFRAGAN_PLOUZANE_NIORT",
    "code": None,
    "laboratoire_type": "lnr",
}


def update_laboratoires_data(apps, schema_editor):
    Laboratoire = apps.get_model("sa", "Laboratoire")

    Laboratoire.objects.filter(external_id="LAB_AUTRE").update(name="AUTRE (CNR, ÉTRANGER, ETC.)")

    ploufragan_plouzane_niort = Laboratoire.objects.get(external_id=MERGED_LABORATOIRE["external_id"])
    methodes = list(ploufragan_plouzane_niort.methodes_analyse.all())
    ploufragan_plouzane_niort.delete()

    for external_id, name in NEW_ANSES_SITES:
        nouveau_laboratoire, _ = Laboratoire.objects.update_or_create(
            external_id=external_id,
            defaults={"name": name, "code": None, "laboratoire_type": "lnr"},
        )
        nouveau_laboratoire.methodes_analyse.set(methodes)


def reverse_update_laboratoires_data(apps, schema_editor):
    Laboratoire = apps.get_model("sa", "Laboratoire")

    Laboratoire.objects.filter(external_id="LAB_AUTRE").update(name="AUTRE")

    nouveaux_laboratoires = Laboratoire.objects.filter(
        external_id__in=[external_id for external_id, _ in NEW_ANSES_SITES]
    )
    methodes = list(nouveaux_laboratoires.first().methodes_analyse.all()) if nouveaux_laboratoires.exists() else []
    nouveaux_laboratoires.delete()

    ploufragan_plouzane_niort = Laboratoire.objects.create(**MERGED_LABORATOIRE)
    ploufragan_plouzane_niort.methodes_analyse.set(methodes)


class Migration(migrations.Migration):
    dependencies = [
        ("sa", "0030_populate_situation_unite_regle"),
    ]

    operations = [
        migrations.RunPython(update_laboratoires_data, reverse_update_laboratoires_data),
    ]
