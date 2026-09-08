from django.db import migrations

ESPECES_COURANTES = [
    "Abeille mellifère (Apis mellifera)",
    "Alpaga (Vicugna pacos)",
    "Âne (Equus asinus)",
    "Autruche (Struthio camelus)",
    "Bovin (Bos taurus)",
    "Buffle (Bubalus bubalis)",
    "Caille commune (Coturnix coturnix)",
    "Caille japonaise (Coturnix japonica)",
    "Canard colvert (Anas platyrhynchos)",
    "Canard de Barbarie (Musqué) (Cairina moschata)",
    "Canard de Pékin (Anas platyrhynchos domesticus)",
    "Canard mulard",
    "Caprin (Capra hircus)",
    "Cerf (Cervus elaphus)",
    "Chameau (Camelus bactrianus)",
    "Chat domestique (Felis catus)",
    "Cheval (Equus caballus)",
    "Chevreuil (Capreolus capreolus)",
    "Chien (Canis lupus familiaris)",
    "Dinde (Meleagris gallopavo)",
    "Dromadaire (Camelus dromedarius)",
    "Émeu (Dromaius novaehollandiae)",
    "Faisan commun (Phasianus colchicus)",
    "Lama (Lama glama)",
    "Lapin européen (Oryctolagus cuniculus)",
    "Oie de Chine (Anser cygnoides)",
    "Oie domestique (Anser anser)",
    "Ovin (Ovis aries)",
    "Perdrix à pattes rouges (Alectoris rufa)",
    "Perdrix grise (Perdix perdix)",
    "Pigeon biset (Columba livia)",
    "Pintade commune (Numida meleagris)",
    "Porc (Sus scrofa domesticus)",
    "Poule/poulet (Gallus gallus)",
    "Sanglier (Sus scrofa)",
]


def populate_especes_courantes(apps, schema_editor):
    Espece = apps.get_model("sa", "Espece")
    updated = Espece.objects.filter(name__in=ESPECES_COURANTES).update(is_highlighted=True)
    if updated != len(ESPECES_COURANTES):
        found = set(Espece.objects.filter(name__in=ESPECES_COURANTES).values_list("name", flat=True))
        missing = sorted(set(ESPECES_COURANTES) - found)
        raise RuntimeError(f"Espèces courantes introuvables dans le référentiel: {missing}")


class Migration(migrations.Migration):
    dependencies = [
        ("sa", "0016_espece_is_highlighted_maladie_especes_concernees"),
    ]

    operations = [
        migrations.RunPython(populate_especes_courantes, migrations.RunPython.noop),
    ]
