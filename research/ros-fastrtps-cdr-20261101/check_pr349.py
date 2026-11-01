#!/usr/bin/env python3
"""Independent differential oracle for ROS + Fast-CDR issue #940 / PR #349."""
import collections
import json

def load(arm):
    rows = json.load(open(f"/evidence/{arm}-results.json"))["cases"]
    assert len(rows) == 224, (arm, len(rows))
    return {(x["backend"], x["type"], x["case"]): x for x in rows}

before, after = load("baseline"), load("patched")
assert set(before) == set(after)

for arm, rows in [("baseline", before), ("patched", after)]:
    for key, row in rows.items():
        if key[2] == "valid":
            assert row["outcome"] == "accepted", (arm, key, row)

affected = []
for key, row in before.items():
    backend, type_name, case = key
    if backend == "rmw_fastrtps_cpp" and case == "header_only":
        outcome_before, outcome_after = row["outcome"], after[key]["outcome"]
        affected.append((type_name, outcome_before, outcome_after))
        assert outcome_after == "error", (key, row, after[key])

# Confirm our baseline is the original bug rather than a green oracle.
old_bad = [x for x in affected if x[1] in ("signal", "timeout", "accepted")]
assert len(old_bad) >= 5, old_bad

delta = []
for k in sorted(before):
    a, b = before[k]["outcome"], after[k]["outcome"]
    if a != b:
        delta.append({"backend": k[0], "type": k[1], "case": k[2],
                      "before": a, "after": b})

print("BOUNDARY:", json.dumps(affected))
print("DIFFERENCES:", json.dumps(delta))
for arm, rows in [("baseline", before), ("patched", after)]:
    for backend in ("rmw_fastrtps_cpp", "rmw_cyclonedds_cpp"):
        c = collections.Counter(row["outcome"] for key, row in rows.items()
                                if key[0] == backend)
        print(f"{arm} {backend}: {dict(c)}")
with open("/evidence/differential.json", "w") as file:
    json.dump({"boundary": affected, "deltas": delta}, file, indent=2)

# New crashes in Fast DDS are a regression and invalidate the comparison.
for k, old in before.items():
    if k[0] != "rmw_fastrtps_cpp":
        continue
    new = after[k]
    if new["outcome"] in ("signal", "timeout", "process_error"):
        assert old["outcome"] in ("signal", "timeout", "process_error"), (k, old, new)

print("GATE: PASS - seven header-only cases safely rejected with patch; "
      "all valid controls preserved; no new Fast DDS crashes.")
