from django.db import migrations

CREATE_VIEW_SQL = """
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

DROP_VIEW_SQL = "DROP MATERIALIZED VIEW IF EXISTS ssa_evenementproduit_mv;"


class Migration(migrations.Migration):
    dependencies = [
        ("ssa", "0068_alter_evenementproduit_actions_engagees_and_more"),
    ]

    operations = [
        migrations.RunSQL(sql=CREATE_VIEW_SQL, reverse_sql=DROP_VIEW_SQL),
    ]
