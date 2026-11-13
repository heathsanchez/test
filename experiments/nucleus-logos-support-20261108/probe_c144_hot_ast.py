#!/usr/bin/env python3
"""C144: source-pinned N7 hot AST nodes and exact application parent roles.

Pure source inspection; no comparison rule, normal-form proof or verdict change.
"""

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
HOT_IDS = (1, 6, 11, 7, 345, 4677, 4678, 4679)


def inspect_hot_ast(source: bytes, ids=HOT_IDS):
    """Read exact exported rows, with *application* parent roles only."""
    assert len(set(ids)) == len(ids), "ambiguous requested ID roster"
    targets = set(ids)
    found = {}
    app_parents = {expr: [] for expr in ids}
    for line in source.splitlines():
        row = json.loads(line)
        expr = row.get("ie")
        if not isinstance(expr, int):
            continue
        if expr in targets:
            assert expr not in found, ("duplicate expression row", expr)
            found[expr] = row
        app = row.get("app")
        if not isinstance(app, dict):
            continue
        for role in ("fn", "arg"):
            if app.get(role) in targets:
                app_parents[app[role]].append({"parent": expr, "role": role})
    assert set(found) == targets, ("missing hot source rows", targets - set(found))
    records = []
    for expr in ids:
        parent_edges = sorted(app_parents[expr], key=lambda item: (item["parent"], item["role"]))
        records.append({"expr": expr, "row": found[expr],
                        "application_parent_count": len(parent_edges),
                        "application_parents": parent_edges[:32],
                        "parents_truncated": len(parent_edges) > 32})
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    source = args.source.read_bytes()
    assert hashlib.sha256(source).hexdigest() == SOURCE_SHA256, "frozen source drift"
    print(json.dumps({"status": "C144_SOURCE_NATIVE_AST_ONLY",
                      "source": "original unchanged magma-list-pair-n7",
                      "sha256": SOURCE_SHA256,
                      "hot_expressions": inspect_hot_ast(source)}, sort_keys=True))


if __name__ == "__main__":
    main()
