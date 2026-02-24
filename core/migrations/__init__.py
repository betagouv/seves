def libelle_pre_proccess(field_name):
    from django.contrib.postgres.lookups import Unaccent
    from django.db.models import Func, Value
    from django.db.models.functions import Trim, Upper

    return Trim(
        Func(
            Func(
                Unaccent(Upper(field_name)),
                Value(r"\W+"),
                Value(" "),
                Value("g"),
                function="regexp_replace",
            ),
            Value(r"\s+CEDEX"),
            Value(""),
            function="regexp_replace",
        )
    )
