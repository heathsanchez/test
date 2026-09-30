"""Extract the dependency closure of the real Arena no-confusion helper.

Preserves source order and whole inductive blocks. Names and universe records
are retained; unrelated declarations and expression nodes are removed.
This is a dependency slice, not a claim of globally minimal syntax.
"""
import json
import pathlib
import sys


def slice_prefix(source, target="_private.Init.Prelude.0.noConfusion_of_Nat.aux._f"):
    records, names, expressions, declarations = [], {0: ""}, {}, {}
    root = None
    for line in source.read_text().splitlines():
        record = json.loads(line)
        records.append(record)
        if "in" in record:
            value = record.get("str", record.get("num"))
            names[record["in"]] = names[value["pre"]] + ("." if value["pre"] else "") + str(value.get("str", value.get("i")))
        if "ie" in record:
            expressions[record["ie"]] = record
        if "inductive" in record:
            for kind in ("types", "ctors", "recs"):
                for declaration in record["inductive"][kind]:
                    declarations[declaration["name"]] = record
                    if names[declaration["name"]] == target:
                        root = declaration["name"]
        for kind in ("def", "thm", "axiom", "opaque"):
            if kind in record:
                name = record[kind]["name"]
                declarations[name] = record
                if names[name] == target:
                    root = name
        if root is not None:
            break
    assert root is not None, f"Target declaration absent: {target}"
    needed_expressions, needed_declarations = set(), set()

    def expression(index):
        if index in needed_expressions:
            return
        needed_expressions.add(index)
        record = expressions[index]
        if "const" in record:
            declaration(record["const"]["name"])
        for kind, fields in (("app", ("fn", "arg")), ("lam", ("type", "body")), ("forallE", ("type", "body")), ("letE", ("type", "value", "body")), ("proj", ("struct",))):
            if kind in record:
                for field in fields:
                    expression(record[kind][field])
        if "proj" in record:
            declaration(record["proj"]["typeName"])

    def declaration(name):
        record = declarations[name]
        if id(record) in needed_declarations:
            return
        needed_declarations.add(id(record))

        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in ("type", "value", "rhs") and isinstance(child, int):
                        expression(child)
                    elif isinstance(child, (list, dict)):
                        visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(record)

    declaration(root)
    output = [record for record in records if "meta" in record or "in" in record or "il" in record or ("ie" in record and record["ie"] in needed_expressions) or id(record) in needed_declarations]
    return "\n".join(json.dumps(record, separators=(",", ":")) for record in output) + "\n"


if __name__ == "__main__":
    pathlib.Path(sys.argv[2]).write_text(slice_prefix(pathlib.Path(sys.argv[1]), *sys.argv[3:]))
