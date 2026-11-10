from django.db.backends.postgresql.operations import DatabaseOperations


def _non_empty_tables(connection, tables):
    query = " UNION ALL ".join(
        f"SELECT '{table}' WHERE EXISTS (SELECT 1 FROM {connection.ops.quote_name(table)})" for table in tables
    )
    with connection.cursor() as cursor:
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]


def install_fast_flush():
    original_sql_flush = DatabaseOperations.sql_flush

    if getattr(original_sql_flush, "_seves_fast_flush", False):
        return

    def sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False):
        return [f"DELETE FROM {self.quote_name(table)};" for table in _non_empty_tables(self.connection, tables)]

    sql_flush._seves_fast_flush = True
    DatabaseOperations.sql_flush = sql_flush
