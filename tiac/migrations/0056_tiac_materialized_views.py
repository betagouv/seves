from django.db import migrations

EVENEMENT_SIMPLE_FORWARD_SQL = """
CREATE MATERIALIZED VIEW tiac_evenementsimple_mv AS
SELECT DISTINCT
    es.*,
    structure.libelle AS createur_structure,
    s.libelle AS structure_contact
FROM tiac_evenementsimple es
LEFT JOIN core_structure structure ON structure.id = es.createur_id
LEFT JOIN tiac_evenementsimple_contacts esc ON esc.evenementsimple_id = es.id
LEFT JOIN core_contact c ON c.id = esc.contact_id
LEFT JOIN core_structure s ON s.id = c.structure_id;

CREATE UNIQUE INDEX tiac_evenementsimple_mv_id_structure_idx ON tiac_evenementsimple_mv (id, structure_contact);
CREATE INDEX tiac_evenementsimple_mv_structure_contact_idx ON tiac_evenementsimple_mv (structure_contact);
"""

EVENEMENT_SIMPLE_REVERSE_SQL = """
DROP MATERIALIZED VIEW IF EXISTS tiac_evenementsimple_mv;
"""

INVESTIGATION_TIAC_FORWARD_SQL = """
CREATE MATERIALIZED VIEW tiac_investigationtiac_mv AS
SELECT DISTINCT
    it.*,
    structure.libelle AS createur_structure,
    s.libelle AS structure_contact
FROM tiac_investigationtiac it
LEFT JOIN core_structure structure ON structure.id = it.createur_id
LEFT JOIN tiac_investigationtiac_contacts itc ON itc.investigationtiac_id = it.id
LEFT JOIN core_contact c ON c.id = itc.contact_id
LEFT JOIN core_structure s ON s.id = c.structure_id;

CREATE UNIQUE INDEX tiac_investigationtiac_mv_id_structure_idx ON tiac_investigationtiac_mv (id, structure_contact);
CREATE INDEX tiac_investigationtiac_mv_structure_contact_idx ON tiac_investigationtiac_mv (structure_contact);
"""

INVESTIGATION_TIAC_REVERSE_SQL = """
DROP MATERIALIZED VIEW IF EXISTS tiac_investigationtiac_mv;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("tiac", "0055_alter_investigationtiac_conclusion_aliment_and_more"),
    ]

    operations = [
        migrations.RunSQL(sql=EVENEMENT_SIMPLE_FORWARD_SQL, reverse_sql=EVENEMENT_SIMPLE_REVERSE_SQL),
        migrations.RunSQL(sql=INVESTIGATION_TIAC_FORWARD_SQL, reverse_sql=INVESTIGATION_TIAC_REVERSE_SQL),
    ]
