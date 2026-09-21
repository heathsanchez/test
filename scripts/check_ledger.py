from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FIELDS = (
    "id",
    "date",
    "arena_sha",
    "baseline",
    "obstruction",
    "residual_class",
    "capability",
    "competing_explanation",
    "falsifier",
    "ablation",
    "protected_suite",
    "primary_metric",
    "decision_rule",
    "implementation_commit",
    "qualification",
    "performance",
    "decision",
)
DECISIONS = {"open", "retained", "rejected", "unknown"}


def load_records(path: Path) -> list[dict]:
    records = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"line {line_number}: record must be an object")
        records.append(value)
    return records


def validate_records(records: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(records, 1):
        prefix = f"record {index}"
        for field in REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"{prefix}: missing {field}")
        ident = record.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{prefix}: id must be a non-empty string")
        elif ident in seen:
            errors.append(f"{prefix}: duplicate id {ident}")
        else:
            seen.add(ident)
        sha = record.get("arena_sha")
        if not isinstance(sha, str) or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
            errors.append(f"{prefix}: arena_sha must be a lowercase 40-hex SHA")
        decision = record.get("decision")
        if decision not in DECISIONS:
            errors.append(f"{prefix}: invalid decision {decision!r}")
        if decision == "retained":
            for field in ("obstruction", "falsifier", "qualification"):
                if not record.get(field):
                    errors.append(f"{prefix}: retained entry requires {field}")
    return errors


def main() -> int:
    path = Path(__file__).resolve().parents[1] / "evidence/ledger.jsonl"
    errors = validate_records(load_records(path))
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
