"""Parse exact nano-lean vstats fields; do not confuse counter-name suffixes.

This is an integrity gate for diagnostic measurements, never a proof checker.
"""

import argparse
import json
from pathlib import Path
import re


_ROW = re.compile(r"^vstats (?P<name>\S+) Stats \{(?P<body>[^}]*)\}(?:\s|$)")
_FIELD = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_]*): (?P<value>\d+)")


def parse_vstats(lines):
    records = {}
    for line in lines:
        if not line.startswith("vstats "):
            continue
        match = _ROW.match(line)
        if not match:
            raise ValueError("Malformed vstats row")
        name = match.group("name")
        if name in records:
            raise ValueError(f"Duplicate vstats declaration: {name}")
        fields = {}
        for part in match.group("body").split(","):
            field = _FIELD.fullmatch(part.strip())
            if field is None:
                raise ValueError(f"Malformed vstats field for {name}")
            key = field.group("key")
            if key in fields:
                raise ValueError(f"Duplicate vstats counter: {name}.{key}")
            fields[key] = int(field.group("value"))
        records[name] = fields
    if not records:
        raise ValueError("No vstats rows emitted")
    return records


def require_counter(records, counter, expectation, declaration=None):
    if expectation not in {"zero", "positive"}:
        raise ValueError(f"Unknown expectation: {expectation}")
    if declaration is not None:
        if declaration not in records:
            raise ValueError(f"Missing vstats declaration: {declaration}")
        selected = {declaration: records[declaration]}
    else:
        selected = records
    if not selected:
        raise ValueError("Missing vstats declarations")
    for name, fields in selected.items():
        if counter not in fields:
            raise ValueError(f"Missing vstats counter: {name}.{counter}")
        value = fields[counter]
        if (expectation == "zero" and value != 0) or (
            expectation == "positive" and value <= 0
        ):
            raise ValueError(f"Unexpected vstats {name}.{counter}={value}: expected {expectation}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stats", required=True, type=Path)
    parser.add_argument("--counter", required=True)
    parser.add_argument("--expect", required=True, choices=("zero", "positive"))
    parser.add_argument("--declaration")
    options = parser.parse_args()
    with options.stats.open(encoding="utf-8") as stream:
        records = parse_vstats(stream)
    require_counter(records, options.counter, options.expect, options.declaration)
    selected = records if options.declaration is None else {options.declaration: records[options.declaration]}
    print(json.dumps({"checked": len(selected), "counter": options.counter,
                      "expect": options.expect, "declarations": list(selected)}))


if __name__ == "__main__":
    main()
