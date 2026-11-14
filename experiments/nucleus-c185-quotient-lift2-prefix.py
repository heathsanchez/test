#!/usr/bin/env python3
"""C185: copy exact NDJSON records through Quotient.lift₂._proof_2; never reorder."""
import hashlib
import json
import pathlib
import sys
source, output = map(pathlib.Path, sys.argv[1:3])
names = {0: ""}
target_name = "Quotient.lift₂._proof_2"
matched = None
with source.open("rb") as src, output.open("wb") as dst:
    for lineno, raw in enumerate(src, 1):
        record = json.loads(raw)
        dst.write(raw)
        if "in" in record:
            if "str" in record:
                item = record["str"]
                if item["pre"] not in names:
                    raise RuntimeError(f"undeclared prefix at {lineno}")
                names[record["in"]] = names[item["pre"]] + "." + item["str"]
            elif "num" in record:
                item = record["num"]
                if item["pre"] not in names:
                    raise RuntimeError(f"undeclared prefix at {lineno}")
                names[record["in"]] = names[item["pre"]] + "." + str(item["i"])
        for kind in ("thm", "def", "opaque"):
            value = record.get(kind)
            if isinstance(value, dict) and names.get(value.get("name"), "").lstrip(".") == target_name:
                matched = {
                    "record": lineno, "kind": kind, "target": target_name,
                    "name_id": value["name"], "type_id": value["type"],
                    "value_id": value["value"],
                }
                break
        if matched is not None:
            break
if matched is None:
    output.unlink(missing_ok=True)
    raise RuntimeError("Quotient.lift₂._proof_2 not found in source stream")
matched["prefix_bytes"] = output.stat().st_size
with output.open("rb") as file:
    matched["prefix_sha256"] = hashlib.file_digest(file, "sha256").hexdigest()
matched["full_source_sha256"] = "22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6"
output.with_suffix(".json").write_text(json.dumps(matched, indent=2) + "\n")
print(json.dumps(matched, ensure_ascii=False), flush=True)
