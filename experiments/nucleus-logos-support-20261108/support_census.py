"""Read-only, source-qualified census of loose-variable support in Lean exports.

This is a structural diagnostic, not a typing or equality certificate. A cached
type may depend on the *authority* of a used binding even when this tool finds
the same source support across different enclosing frames.
"""

import argparse
import collections
import hashlib
import json
import pathlib


class SourceGraph:
    def __init__(self, nodes):
        self.nodes = nodes
        self._memo = {}

    @classmethod
    def from_rows(cls, rows):
        nodes = {}
        for row in rows:
            if "ie" in row:
                index = row["ie"]
                if index in nodes:
                    raise ValueError(f"duplicate expression {index}")
                nodes[index] = row
        return cls(nodes)

    @classmethod
    def from_file(cls, path):
        with pathlib.Path(path).open(encoding="utf-8") as stream:
            return cls.from_rows(json.loads(line) for line in stream)

    @staticmethod
    def _dependencies(node):
        if "app" in node:
            app = node["app"]
            return ((app["fn"], False), (app["arg"], False))
        if "lam" in node or "forallE" in node:
            binder = node.get("lam", node.get("forallE"))
            return ((binder["type"], False), (binder["body"], True))
        if "letE" in node:
            let = node["letE"]
            return ((let["type"], False), (let["value"], False),
                    (let["body"], True))
        if "proj" in node:
            return ((node["proj"]["struct"], False),)
        if "bvar" in node or any(k in node for k in
                                   ("const", "sort", "natVal", "strVal")):
            return ()
        return None

    def support(self, expression):
        if expression in self._memo:
            return self._memo[expression]
        pending = [(expression, False)]
        active = set()
        while pending:
            current, finishing = pending.pop()
            if current in self._memo:
                continue
            node = self.nodes.get(current)
            deps = self._dependencies(node) if node is not None else None
            if deps is None:
                self._memo[current] = None
                active.discard(current)
                continue
            if not finishing:
                if current in active:
                    # A malformed cyclic DAG cannot justify an absence fact.
                    self._memo[current] = None
                    continue
                active.add(current)
                pending.append((current, True))
                for child, _ in reversed(deps):
                    if child not in self._memo:
                        pending.append((child, False))
                continue
            active.discard(current)
            if "bvar" in node:
                result = (node["bvar"],)
            else:
                used = set()
                for child, under_binder in deps:
                    child_used = self._memo.get(child)
                    if child_used is None:
                        used = None
                        break
                    for index in child_used:
                        if under_binder:
                            if index > 0:
                                used.add(index - 1)
                        else:
                            used.add(index)
                result = tuple(sorted(used)) if used is not None else None
            self._memo[current] = result
        return self._memo.get(expression)


def observer_rows(path):
    calls = collections.Counter()
    completed = collections.Counter()
    included = collections.Counter()
    with pathlib.Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.startswith("NUCLEUS_ORDINARY_WORK:"):
                continue
            record = json.loads(line.partition(":")[2])
            for row in record.get("rows", []):
                expr = int(row["expr"])
                calls[expr] += int(row["calls"])
                completed[expr] += int(row.get("completed", 0))
                included[expr] += int(row.get("inclusive", 0))
    return calls, completed, included


def census(export, observer, limit):
    graph = SourceGraph.from_file(export)
    calls, completed, included = observer_rows(observer)
    hot = []
    for expr, count in calls.most_common(limit):
        support = graph.support(expr)
        node = graph.nodes.get(expr, {})
        tag = next((tag for tag in ("bvar", "app", "lam", "forallE", "letE",
                                     "proj", "const", "sort", "natVal", "strVal")
                    if tag in node), None)
        hot.append({"expression": expr, "tag": tag, "calls": count,
                    "completed": completed[expr], "inclusive_steps": included[expr],
                    "loose_bvars": support})
    digest = hashlib.sha256(pathlib.Path(export).read_bytes()).hexdigest()
    return {"input_sha256": digest, "source_nodes": len(graph.nodes),
            "observer": str(pathlib.Path(observer).name),
            "scope": "literal source AST + observed inference calls, NOT a typing or reuse proof",
            "observations": hot}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export")
    parser.add_argument("observer")
    parser.add_argument("--top", type=int, default=30)
    arguments = parser.parse_args()
    print(json.dumps(census(arguments.export, arguments.observer, arguments.top), indent=2))


if __name__ == "__main__":
    main()
