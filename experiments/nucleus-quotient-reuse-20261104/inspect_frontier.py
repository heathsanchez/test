#!/usr/bin/env python3
"""Read-only source-specific exploration of a pinned Lean 4 NDJSON export."""

import argparse
from collections import deque
import json
from pathlib import Path


def main(source: Path, targets: list[int], depth: int, path_from=None, path_to=None):
    names = {0: ""}
    terms = {}
    for line in source.open():
        item = json.loads(line)
        if "in" in item:
            part = item.get("str", item.get("num"))
            if part:
                parent = names.get(part["pre"], f"#{part['pre']}")
                names[item["in"]] = parent + ("." if parent else "") + str(part.get("str", part.get("i")))
        if "ie" in item:
            terms[item["ie"]] = {k:v for k,v in item.items() if k != "ie"}

    def describe(index: int, remaining: int, seen=frozenset()):
        if remaining < 0 or index in seen:
            return f"e{index}"
        item = terms.get(index)
        if not item:
            return f"e{index} (missing)"
        k,v = next(iter(item.items()))
        follow = seen | {index}
        if k == "const": return f"{names.get(v['name'], '#'+str(v['name']))} {v['us']}"
        if k == "app": return f"({describe(v['fn'],remaining-1,follow)} {describe(v['arg'],remaining-1,follow)})"
        if k == "lam" or k == "forallE":
            symbol = "λ" if k == "lam" else "Π"
            return f"({symbol} {names.get(v['name'],'_')} : {describe(v['type'],remaining-1,follow)} . {describe(v['body'],remaining-1,follow)})"
        if k == "letE":
            return f"(let {names.get(v['name'],'_')} : {describe(v['type'],remaining-1,follow)} := {describe(v['value'],remaining-1,follow)} in {describe(v['body'],remaining-1,follow)})"
        if k == "bvar": return f"bvar#{v}"
        if k == "sort": return f"Sort({v})"
        if k == "nat": return f"NatLit({v})"
        if k == "proj": return f"proj({names.get(v['typeName'],v['typeName'])},{v['idx']},{describe(v['struct'],remaining-1,follow)})"
        return str(item)

    print(f"Source: {source} names={len(names)} terms={len(terms)}")
    for index in targets:
        print(f"e{index} {terms.get(index)}")
        print(describe(index,depth))

    if path_from is not None:
        def successors(index):
            item = terms.get(index, {})
            if "app" in item:
                return [item["app"][key] for key in ("fn", "arg")]
            if "lam" in item or "forallE" in item:
                binder = item.get("lam", item.get("forallE"))
                return [binder["type"], binder["body"]]
            if "letE" in item:
                return [item["letE"][key] for key in ("type", "value", "body")]
            if "proj" in item:
                return [item["proj"]["struct"]]
            return []
        queue = deque([path_from]); parent = {path_from: None}
        while queue and path_to not in parent:
            current = queue.popleft()
            for child in successors(current):
                if child not in parent:
                    parent[child] = current
                    queue.append(child)
        if path_to in parent:
            chain = []
            current = path_to
            while current is not None:
                chain.append(current)
                current = parent[current]
            print("SOURCE_DEPENDENCY_PATH", " -> ".join("e"+str(x) for x in reversed(chain)))
        else:
            print(f"NO_SOURCE_DEPENDENCY_PATH e{path_from} -> e{path_to}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    parser.add_argument("indices",type=int,nargs="+")
    parser.add_argument("--depth",type=int,default=5)
    parser.add_argument("--path-from",type=int)
    parser.add_argument("--path-to",type=int)
    args=parser.parse_args()
    main(args.source,args.indices,args.depth,args.path_from,args.path_to)
