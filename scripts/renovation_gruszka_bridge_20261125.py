"""A bounded comparison adapter for the frozen beta's omitted isReflexive.

isRec and isReflexive are distinct metadata, not aliases. Susz 0.4 requires
both; the frozen beta omits isReflexive. For one nonrecursive, nonindexed,
nonnested family, establish absence of the family in every constructor
binder domain, then add only isReflexive=false to the comparator copy.
Gruszka independently recomputes and checks this flag (induct.rs:785-858).
No Nucleus input, version, feature flag, declaration, or term is changed.
This is a declared derived-input comparison, not an exact-byte upstream run.
"""
import copy
import hashlib
import json


def unique(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ValueError("duplicate JSON key")
        obj[k] = v
    return obj


def bridge(raw):
    rows = [json.loads(line, object_pairs_hook=unique) for line in raw.splitlines()]
    assert 1 < len(rows) <= 4096
    assert rows[0]["meta"]["format"]["version"] == "3.2.0"
    blocks = [r["inductive"] for r in rows if "inductive" in r]
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block["types"]) == 1
    ind = block["types"][0]
    assert ind["isRec"] is False and ind["numNested"] == ind["numIndices"] == 0
    assert "isReflexive" not in ind
    exprs = {}
    for row in rows:
        assert not any(k in row for k in ("axiom", "opaque", "quot"))
        if "ie" in row:
            idx = row["ie"]
            assert type(idx) is int and idx == len(exprs)
            exprs[idx] = row

    def children(row):
        if "app" in row:
            return [row["app"]["fn"], row["app"]["arg"]]
        for tag in ("forallE", "lam"):
            if tag in row:
                return [row[tag]["type"], row[tag]["body"]]
        if "proj" in row:
            return [row["proj"]["struct"]]
        assert any(k in row for k in ("const", "sort", "bvar")), "unsupported field expression"
        return []

    visited = set()
    def no_family(root):
        todo = [root]
        while todo:
            idx = todo.pop()
            if idx in visited:
                continue
            visited.add(idx)
            row = exprs[idx]
            assert row.get("const", {}).get("name") != ind["name"], "recursive domain"
            for child in children(row):
                assert type(child) is int and 0 <= child < idx
                todo.append(child)

    for ctor in block["ctors"]:
        assert ctor["induct"] == ind["name"] and ctor["numParams"] == ind["numParams"]
        idx = ctor["type"]
        for _ in range(ctor["numParams"] + ctor["numFields"]):
            binder = exprs[idx]["forallE"]
            no_family(binder["type"])
            assert 0 <= binder["body"] < idx
            idx = binder["body"]
    adapted = copy.deepcopy(rows)
    adapted_ind = next(r["inductive"]["types"][0] for r in adapted if "inductive" in r)
    adapted_ind["isReflexive"] = False
    check = copy.deepcopy(adapted)
    del next(r["inductive"]["types"][0] for r in check if "inductive" in r)["isReflexive"]
    assert check == rows
    output = b"".join((json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n").encode() for r in adapted)
    receipt = {"boundary": "nonrecursive-single-family-derived-input",
               "only_added_metadata": "isReflexive=false",
               "source_sha256": hashlib.sha256(raw).hexdigest(),
               "comparator_input_sha256": hashlib.sha256(output).hexdigest(),
               "constructor_domain_nodes_checked": len(visited)}
    return output, receipt


def self_test():
    from renovation_dependent_projection_20261125 import fixture
    source = fixture("type_field")
    def pack(rows):
        return b"".join((json.dumps(r) + "\n").encode() for r in rows)
    original = pack(source)
    derived, receipt = bridge(original)
    assert derived != original and receipt["constructor_domain_nodes_checked"] > 0
    negatives = []
    for key, value in (("isRec", True), ("isReflexive", False), ("numIndices", 1), ("numNested", 1)):
        mutant = copy.deepcopy(source)
        next(r["inductive"]["types"][0] for r in mutant if "inductive" in r)[key] = value
        negatives.append(pack(mutant))
    mutant = copy.deepcopy(source)
    table = {r["ie"]: r for r in mutant if "ie" in r}
    b = next(r["inductive"] for r in mutant if "inductive" in r)
    domain = table[b["ctors"][0]["type"]]["forallE"]["type"]
    table[domain].clear()
    table[domain].update({"ie": domain, "const": {"name": b["types"][0]["name"], "us": []}})
    negatives.append(pack(mutant))
    negatives.append(original.replace(b'"numNested": 0', b'"numNested": 0, "numNested": 0'))
    for raw in negatives:
        assert raw != original
        try:
            bridge(raw)
        except (AssertionError, ValueError, KeyError):
            pass
        else:
            raise AssertionError("adapter admitted unsupported input")
    print("SCHEMA_BRIDGE_CONTROLS", {"positive": 1, "negative": len(negatives), "unexpected": 0})


if __name__ == "__main__":
    self_test()
