class WithChoicesToJS:
    @classmethod
    def build_options(cls):
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
            path = [p.strip() for p in option.label.split(">")]
            insert_node(path, option.value, options)

        for option in options:
            if option["children"] != []:
                option["isGroupSelectable"] = False
                option["value"] = 2 * option["value"]  # We can pick it we just need a unique value for TreeselectJS

        return options
