from django.db import migrations

# (external_id, current name, restored name)
LABORATOIRES = [
    ("LAB_AGREE_LDA_68", "Laboratoire Alsacien d'Analyses - Colmar (L2A) (LDA 68)", "L2A COLMAR (68)"),
    ("LAB_AGREE_LDA_67", "Laboratoire Alsacien d'Analyses - Strasbourg (L2A) (LDA 67)", "L2A STRASBOURG (67)"),
    (
        "LAB_AGREE_LDA_40",
        "Laboratoire des Pyrénées et des Landes - Mont-de-Marsan (LDA 40)",
        "LPL MONT-DE-MARSAN (LDA 40)",
    ),
    ("LAB_AGREE_LDA_64", "Laboratoires des Pyrénées et des Landes - Lagor (LDA 64)", "LPL LAGOR (LDA 64)"),
    ("LAB_AGREE_LDA_65", "Laboratoires des Pyrénées et des Landes - Tarbes (LDA 65)", "LPL TARBES (LDA 65)"),
    ("LAB_AGREE_LNCR_94", "Laboratoire National des Contrôles des Reproducteurs (LNCR 94)", "LNCR (94)"),
    ("LAB_AGREE_LDA_20B", "Laboratoire d’Analyses CISMONTE (LDA 20b)", "LDA CISMONTE (LDA 20B)"),
    ("LAB_AGREE_LDA_20A", "Laboratoire d’Analyses Pumonte (LA2A) (LDA 20a)", "LDA PUMONTE (LA2A) (LDA 20A)"),
    ("LAB_AGREE_LDA_66", "Centre d’analyses Méditerranée Pyrénées Tecnosud (LDA 66)", "LDA TECNOSUD (66)"),
    ("LAB_AGREE_LDA_03", "Eurofins laboratoire coeur de France (LDA 03)", "EUROFINS COEUR DE FRANCE (LDA 03)"),
    ("LAB_AGREE_LDA_71", "SEML AGRIVALYS - LDA 71", "SEML AGRIVALYS (71)"),
    ("LAB_AGREE_GIR_49", "GIRPA (GIR 49)", "GIRPA (49)"),
    ("LAB_AGREE_GALILAIT_63", "GALILAIT 63", "GALILAIT (63)"),
    ("LAB_AGREE_LILCO_17", "LILCO 17", "LIL 17"),
    ("LAB_AGREE_LDA_58", "TERANA NIEVRE (LDA 58)", "TERANA NIÈVRE (LDA 58)"),
    ("LAB_AGREE_LILLAB_35", "MYLAB JANZE (LILLAB 35)", "MYLAB JANZÉ (LILLAB 35)"),
    ("LNR_CIRAD_MONTPELLIER_UMR_ASTRE", "CIRAD Montpellier (UMR ASTRE)", "CIRAD MONTPELLIER (UMR ASTRE)"),
    ("LNR_IFREMER_LA_TREMBLADE", "IFREMER La Tremblade", "IFREMER LA TREMBLADE"),
    ("LNR_ANSES_LYON", "ANSES Lyon", "ANSES LYON"),
    ("LNR_ANSES_SOPHIA_ANTIPOLIS", "ANSES Sophia-Antipolis", "ANSES SOPHIA-ANTIPOLIS"),
    ("LNR_ANSES_NANCY", "ANSES Nancy", "ANSES NANCY"),
    ("LNR_ANSES_NORMANDIE_GOUSTRAINVILLE", "ANSES Normandie (Goustrainville)", "ANSES NORMANDIE (GOUSTRAINVILLE)"),
    ("LNR_ANSES_MAISONS_ALFORT", "ANSES Maisons-Alfort", "ANSES MAISONS-ALFORT"),
    ("LNR_ANSES_PLOUFRAGAN", "ANSES Ploufragan", "ANSES PLOUFRAGAN"),
    ("LNR_ANSES_PLOUZANE", "ANSES Plouzané", "ANSES PLOUZANÉ"),
    ("LNR_ANSES_NIORT", "ANSES Niort", "ANSES NIORT"),
    ("LAB_AGREE_BIOCV_35", "BIO Chêne Vert (BIOCV 35)", "BIO CHÊNE VERT (BIOCV 35)"),
    ("LAB_AGREE_LDA_49", "INOVALYS - Angers (LDA 49)", "INOVALYS - ANGERS (LDA 49)"),
    ("LAB_AGREE_LDA_72", "INOVALYS - Le Mans (LDA 72)", "INOVALYS - LE MANS (LDA 72)"),
    ("LAB_AGREE_LDA_44", "INOVALYS - Nantes (LDA 44)", "INOVALYS - NANTES (LDA 44)"),
    ("LAB_AGREE_LDA_37", "INOVALYS - Tours (LDA 37)", "INOVALYS - TOURS (LDA 37)"),
    ("LAB_AGREE_LDA_56B", "INOVALYS - Lorient (LDA 56B)", "INOVALYS - LORIENT (LDA 56B)"),
    ("LAB_AGREE_LDA_56A", "INOVALYS - Vannes (LDA 56A)", "INOVALYS - VANNES (LDA 56A)"),
    ("LAB_AGREE_LDA_27", "LABEO Eure (LDA 27)", "LABEO EURE (LDA 27)"),
    ("LAB_AGREE_LDA_14", "LABEO Frank DUNCOMBE (LDA 14)", "LABEO FRANK DUNCOMBE (LDA 14)"),
    ("LAB_AGREE_LDA_50", "LABEO Manche (LDA 50)", "LABEO MANCHE (LDA 50)"),
    ("LAB_AGREE_LDA_61", "LABEO Orne (LDA 61)", "LABEO ORNE (LDA 61)"),
    ("LAB_AGREE_PROGENUS", "Progenus", "PROGENUS"),
    ("LAB_AGREE_LDA_32", "Public Labos - Gers (LDA 32)", "PUBLIC LABOS - GERS (LDA 32)"),
    ("LAB_AGREE_LDA_46", "Public Labos - Lot (LDA 46)", "PUBLIC LABOS - LOT (LDA 46)"),
    ("LAB_AGREE_LDA_81", "Public Labos - Tarn (LDA 81)", "PUBLIC LABOS - TARN (LDA 81)"),
    ("LAB_AGREE_LDA_79", "QUALYSE - Champdeniers (LDA 79)", "QUALYSE - CHAMPDENIERS (LDA 79)"),
    ("LAB_AGREE_LDA_19", "QUALYSE - Tulle (LDA 19)", "QUALYSE - TULLE (LDA 19)"),
    ("LAB_AGREE_LDA_26", "TERANA Drôme (LDA 26)", "TERANA DRÔME (LDA 26)"),
]

# (external_id, current code, restored code)
CODES = [
    ("LNR_CIRAD_MONTPELLIER_UMR_ASTRE", "LNR_CIRAD_MONTPELLIER_UMR_ASTRE", None),
    ("LNR_IFREMER_LA_TREMBLADE", "LNR_IFREMER_LA_TREMBLADE", None),
    ("LNR_ANSES_LYON", "LNR_ANSES_LYON", None),
    ("LNR_ANSES_SOPHIA_ANTIPOLIS", "LNR_ANSES_SOPHIA_ANTIPOLIS", None),
    ("LNR_ANSES_NANCY", "LNR_ANSES_NANCY", None),
    ("LNR_ANSES_NORMANDIE_GOUSTRAINVILLE", "LNR_ANSES_NORMANDIE_GOUSTRAINVILLE", None),
    ("LNR_ANSES_MAISONS_ALFORT", "LNR_ANSES_MAISONS_ALFORT", None),
    ("LAB_AGREE_LDA_20A", "LDA 20a", "LDA 20A"),
    ("LAB_AGREE_LDA_20B", "LDA 20b", "LDA 20B"),
]


def restore_laboratoires_labels_and_codes(apps, schema_editor):
    Laboratoire = apps.get_model("sa", "Laboratoire")
    for external_id, _, restored_name in LABORATOIRES:
        Laboratoire.objects.filter(external_id=external_id).update(name=restored_name)
    for external_id, _, restored_code in CODES:
        Laboratoire.objects.filter(external_id=external_id).update(code=restored_code)


def reverse_restore_laboratoires_labels_and_codes(apps, schema_editor):
    Laboratoire = apps.get_model("sa", "Laboratoire")
    for external_id, current_name, _ in LABORATOIRES:
        Laboratoire.objects.filter(external_id=external_id).update(name=current_name)
    for external_id, current_code, _ in CODES:
        Laboratoire.objects.filter(external_id=external_id).update(code=current_code)


class Migration(migrations.Migration):
    dependencies = [
        ("sa", "0051_evenementanimal_import_id"),
    ]

    operations = [
        migrations.RunPython(restore_laboratoires_labels_and_codes, reverse_restore_laboratoires_labels_and_codes),
    ]
