from django.db import migrations

EVENEMENT_PRODUIT_FORWARD_SQL = """
DROP MATERIALIZED VIEW IF EXISTS ssa_evenementproduit_mv;

CREATE MATERIALIZED VIEW ssa_evenementproduit_mv AS
SELECT DISTINCT
    ep.*,
    structure.libelle AS createur_structure,
    s.libelle AS structure_contact
FROM ssa_evenementproduit ep
LEFT JOIN core_structure structure ON structure.id = ep.createur_id
LEFT JOIN ssa_evenementproduit_contacts epc ON epc.evenementproduit_id = ep.id
LEFT JOIN core_contact c ON c.id = epc.contact_id
LEFT JOIN core_structure s ON s.id = c.structure_id;

CREATE UNIQUE INDEX ssa_evenementproduit_mv_id_structure_idx ON ssa_evenementproduit_mv (id, structure_contact);
CREATE INDEX ssa_evenementproduit_mv_structure_contact_idx ON ssa_evenementproduit_mv (structure_contact);
"""

EVENEMENT_PRODUIT_REVERSE_SQL = """
DROP MATERIALIZED VIEW IF EXISTS ssa_evenementproduit_mv;

CREATE MATERIALIZED VIEW ssa_evenementproduit_mv AS
SELECT
    ep.*,
    structure.libelle AS createur_structure,
    COALESCE(contacts.structures_contact, ARRAY[]::varchar[]) AS structures_contact
FROM ssa_evenementproduit ep
LEFT JOIN core_structure structure ON structure.id = ep.createur_id
LEFT JOIN LATERAL (
    SELECT array_agg(DISTINCT s.libelle ORDER BY s.libelle) AS structures_contact
    FROM ssa_evenementproduit_contacts epc
    JOIN core_contact c ON c.id = epc.contact_id
    JOIN core_structure s ON s.id = c.structure_id
    WHERE epc.evenementproduit_id = ep.id
) contacts ON true;

CREATE UNIQUE INDEX ssa_evenementproduit_mv_id_idx ON ssa_evenementproduit_mv (id);
"""

EVENEMENT_INVESTIGATION_CAS_HUMAIN_FORWARD_SQL = """
CREATE MATERIALIZED VIEW ssa_evenementinvestigationcashumain_mv AS
SELECT DISTINCT
    eich.*,
    structure.libelle AS createur_structure,
    s.libelle AS structure_contact
FROM ssa_evenementinvestigationcashumain eich
LEFT JOIN core_structure structure ON structure.id = eich.createur_id
LEFT JOIN ssa_evenementinvestigationcashumain_contacts eichc
    ON eichc.evenementinvestigationcashumain_id = eich.id
LEFT JOIN core_contact c ON c.id = eichc.contact_id
LEFT JOIN core_structure s ON s.id = c.structure_id;

CREATE UNIQUE INDEX ssa_evenementinvestigationcashumain_mv_id_structure_idx
    ON ssa_evenementinvestigationcashumain_mv (id, structure_contact);
CREATE INDEX ssa_evenementinvestigationcashumain_mv_structure_contact_idx
    ON ssa_evenementinvestigationcashumain_mv (structure_contact);
"""

EVENEMENT_INVESTIGATION_CAS_HUMAIN_REVERSE_SQL = """
DROP MATERIALIZED VIEW IF EXISTS ssa_evenementinvestigationcashumain_mv;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ssa", "0069_auto_20260723_1713"),
    ]

    operations = [
        migrations.RunSQL(sql=EVENEMENT_PRODUIT_FORWARD_SQL, reverse_sql=EVENEMENT_PRODUIT_REVERSE_SQL),
        migrations.RunSQL(
            sql=EVENEMENT_INVESTIGATION_CAS_HUMAIN_FORWARD_SQL,
            reverse_sql=EVENEMENT_INVESTIGATION_CAS_HUMAIN_REVERSE_SQL,
        ),
    ]
