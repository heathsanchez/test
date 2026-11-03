"""Source-pinned official-Lean differential controls for EvalInformation.

Fixtures mutate only the terminal source declaration and preserve every
preceding declaration byte-for-byte.  No expected verdict is inferred from
the fact that a mutation was constructed: the official checker is the oracle.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path


SOURCE_SHA = "f37e9434b2cee5f9623a2218fb6418c58d43dbe5ac3582cadd9cc844dfa215b4"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.read_bytes()
    assert digest(source) == SOURCE_SHA, "Refuse different or drifting source"
    lines = source.splitlines(keepends=True)
    terminal = json.loads(lines[-1])
    original = terminal["inductive"]
    assert len(original["types"]) == len(original["ctors"]) == len(original["recs"]) == 1
    assert original["types"][0]["name"] == 13129
    assert original["types"][0]["numParams"] == 2
    assert original["ctors"][0]["numFields"] == 3
    assert original["recs"][0]["rules"][0]["nfields"] == 3
    args.out.mkdir(parents=True, exist_ok=True)
    prefix = b"".join(lines[:-1])

    def change_induct_params(block):
        block["types"][0]["numParams"] = 3

    def change_ctor_params(block):
        block["ctors"][0]["numParams"] = 1

    def change_ctor_fields_up(block):
        block["ctors"][0]["numFields"] = 4

    def change_ctor_fields_down(block):
        block["ctors"][0]["numFields"] = 2

    def change_rec_params(block):
        block["recs"][0]["numParams"] = 1

    def change_rec_minors(block):
        block["recs"][0]["numMinors"] = 2

    def change_rec_motives(block):
        block["recs"][0]["numMotives"] = 2

    def change_rule_fields(block):
        block["recs"][0]["rules"][0]["nfields"] = 2

    def change_k(block):
        block["recs"][0]["k"] = True

    def change_rec_levels(block):
        block["recs"][0]["levelParams"][1:] = list(reversed(block["recs"][0]["levelParams"][1:]))

    def change_ctor_levels(block):
        block["ctors"][0]["levelParams"].reverse()

    def change_owner(block):
        block["ctors"][0]["induct"] = 13130

    def change_rule_ctor(block):
        block["recs"][0]["rules"][0]["ctor"] = 13129

    mutations = [
        ("authentic", None),
        ("forged-inductive-params", change_induct_params),
        ("forged-constructor-params", change_ctor_params),
        ("forged-constructor-extra-field", change_ctor_fields_up),
        ("forged-constructor-missing-field", change_ctor_fields_down),
        ("forged-recursor-params", change_rec_params),
        ("forged-recursor-minors", change_rec_minors),
        ("forged-recursor-motives", change_rec_motives),
        ("forged-recursor-rule-fields", change_rule_fields),
        ("forged-k-on", change_k),
        ("forged-recursor-level-order", change_rec_levels),
        ("forged-constructor-level-order", change_ctor_levels),
        ("forged-constructor-owner", change_owner),
        ("forged-recursor-rule-owner", change_rule_ctor),
    ]
    manifest = []
    for name, edit in mutations:
        block = copy.deepcopy(original)
        if edit is not None:
            edit(block)
        data = prefix + (json.dumps({"inductive": block}, separators=(",", ":")) + "\n").encode()
        path = args.out / f"{name}.ndjson"
        path.write_bytes(data)
        manifest.append({"case": name, "file": path.name, "sha256": digest(data), "expect_reference": 0 if edit is None else 1})
    (args.out / "inputs.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(manifest)} source-pinned EvalInformation fixtures")


if __name__ == "__main__":
    main()
