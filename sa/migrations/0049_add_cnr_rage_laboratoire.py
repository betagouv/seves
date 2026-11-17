from django.db import migrations

CNR_RAGE = {
    "external_id": "LAB_CNR_RAGE_INSTITUT_PASTEUR",
    "name": "CNR RAGE INSTITUT PASTEUR",
    "code": "CNR RAGE",
    "laboratoire_type": "lda",
}
LAB_AUTRE = "LAB_AUTRE"
AUTRE_OLD_NAME = "AUTRE (CNR, ÉTRANGER, ETC.)"
AUTRE_NEW_NAME = "AUTRE (EX: LABORATOIRE ÉTRANGER)"
RAGE = "Rage"


def add_cnr_rage_laboratoire(apps, schema_editor):
    Laboratoire = apps.get_model("sa", "Laboratoire")
    Maladie = apps.get_model("sa", "Maladie")

    autre = Laboratoire.objects.get(external_id=LAB_AUTRE)
    autre.name = AUTRE_NEW_NAME
    autre.save()

    cnr_rage = Laboratoire.objects.create(**CNR_RAGE)
    cnr_rage.methodes_analyse.set(autre.methodes_analyse.all())

    rage = Maladie.objects.get(name=RAGE)
    rage.laboratoires_frequents.remove(autre)
    rage.laboratoires_frequents.add(cnr_rage)


def remove_cnr_rage_laboratoire(apps, schema_editor):
    Laboratoire = apps.get_model("sa", "Laboratoire")
    Maladie = apps.get_model("sa", "Maladie")

    autre = Laboratoire.objects.get(external_id=LAB_AUTRE)
    autre.name = AUTRE_OLD_NAME
    autre.save()

    Maladie.objects.get(name=RAGE).laboratoires_frequents.add(autre)
    Laboratoire.objects.filter(external_id=CNR_RAGE["external_id"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sa", "0048_add_lievre_brun_to_especes_courantes"),
    ]

    operations = [
        migrations.RunPython(add_cnr_rage_laboratoire, remove_cnr_rage_laboratoire),
    ]
