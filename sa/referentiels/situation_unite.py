LEVELS = ("type_lieu", "mode_elevage", "type_production", "type_elevage")


def fetch_rows():
    from sa.models import SituationUniteRegle

    return list(
        SituationUniteRegle.objects.select_related("espece")
        .order_by("pk")
        .values_list("espece__name", "type_lieu", "mode_elevage", "type_production", "type_elevage")
    )


def build_tree(rows=None):
    if rows is None:
        rows = fetch_rows()

    tree = {}
    for espece_name, *values in rows:
        node = tree.setdefault(espece_name, {})
        for value in values:
            if not value:
                break
            node = node.setdefault(value, {})
    return tree


def _choices_from_rows(rows, level_index):
    seen = []
    seen_set = set()
    for row in rows:
        value = row[level_index]
        if value and value not in seen_set:
            seen_set.add(value)
            seen.append(value)
    return [(value, value) for value in seen]


def choices_by_level(rows=None):
    if rows is None:
        rows = fetch_rows()

    return {level: _choices_from_rows(rows, index + 1) for index, level in enumerate(LEVELS)}


def is_valid_combination(espece_name, type_lieu, mode_elevage="", type_production="", type_elevage="", tree=None):
    node = (tree if tree is not None else build_tree()).get(espece_name)
    if node is None:
        return False

    for value in (type_lieu, mode_elevage, type_production, type_elevage):
        if not value:
            break
        if value not in node:
            return False
        node = node[value]

    return node == {}


def build_tree_json_for_especes(rows=None):
    from sa.models import Espece

    tree = build_tree(rows)
    return {
        str(espece_pk): tree[espece_name]
        for espece_pk, espece_name in Espece.objects.filter(name__in=tree).values_list("pk", "name")
    }
