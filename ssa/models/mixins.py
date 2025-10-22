import unicodedata


def normalize(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()


def sort_tree(tree):
    tree.sort(key=lambda x: normalize(x["name"]))
    for node in tree:
        if node["children"]:
            sort_tree(node["children"])


def build_combined_options(*enums, sorted_results=False):
    all_options = []
    for enum in enums:
        all_options.extend(enum.build_options(sorted_results=False))
    if sorted_results:
        sort_tree(all_options)
    return all_options


class WithChoicesToJS:
    @classmethod
    def build_options(cls, sorted_results=False):
        def insert_node(path, value, tree):
            current_level = tree
            for label in path[:-1]:
                existing = next((n for n in current_level if n["name"] == label), None)
                if not existing:
                    existing = {"name": label, "value": value, "children": []}
                    current_level.append(existing)
                current_level = existing["children"]
            current_level.append({"name": path[-1], "value": value, "children": []})

        options = []
        for option in cls:
            if hasattr(option, "short_name"):
                path = [p.strip() for p in option.short_name.split(">")]
            else:
                path = [p.strip() for p in option.label.split(">")]
            insert_node(path, option.value, options)

        for option in options:
            if option["children"] != []:
                option["isGroupSelectable"] = False
                option["value"] = 2 * option["value"]  # We can pick it we just need a unique value for TreeselectJS

        if sorted_results:
            sort_tree(options)

        return options
