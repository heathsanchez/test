#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


KNOWN_EXPR_TAGS = {"bvar", "sort", "const", "app", "lam", "forallE", "letE"}
DECL_TAGS = {"axiom", "def", "thm", "inductive"}


@dataclass(frozen=True)
class CasePath:
    number: int
    path: Path
    expected_exit: int


def numbered_cases(root: Path, start: int = 1, end: int = 141) -> list[CasePath]:
    root = root.resolve()
    result: list[CasePath] = []
    for number in range(start, end + 1):
        matches = sorted(root.glob(f"*/{number:03d}_*.ndjson"))
        if len(matches) != 1:
            raise ValueError(
                f"tutorial {number:03d}: expected exactly one NDJSON file, found {len(matches)}"
            )
        path = matches[0]
        if path.parent.name == "good":
            expected = 0
        elif path.parent.name == "bad":
            expected = 1
        else:
            raise ValueError(
                f"tutorial {number:03d}: unexpected parent directory {path.parent.name!r}"
            )
        result.append(CasePath(number, path, expected))
    return result


def load_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: record is not an object")
        records.append(value)
    if not records or "meta" not in records[0]:
        raise ValueError(f"{path}: missing first metadata record")
    return records


def record_expr_tag(record: dict[str, Any]) -> str | None:
    if "ie" not in record:
        return None
    candidates = sorted(k for k in record if k != "ie")
    if len(candidates) == 1:
        return candidates[0]
    return "multi:" + ",".join(candidates)


def record_level_tag(record: dict[str, Any]) -> str | None:
    if "il" not in record:
        return None
    candidates = sorted(k for k in record if k != "il")
    if len(candidates) == 1:
        return candidates[0]
    return "multi:" + ",".join(candidates)


def unsupported_decl_tags(record: dict[str, Any]) -> list[str]:
    if any(k in record for k in ("meta", "in", "il", "ie")):
        return []
    if any(k in record for k in DECL_TAGS):
        return []
    return sorted(record)


def name_leaf(record: dict[str, Any]) -> str | None:
    if "in" not in record:
        return None
    if isinstance(record.get("str"), dict):
        value = record["str"].get("str")
        return value if isinstance(value, str) else None
    return None


def inductive_summary(value: dict[str, Any]) -> dict[str, Any]:
    types = value.get("types") if isinstance(value.get("types"), list) else []
    ctors = value.get("ctors") if isinstance(value.get("ctors"), list) else []
    recs = value.get("recs") if isinstance(value.get("recs"), list) else []

    type_rows = [row for row in types if isinstance(row, dict)]
    ctor_rows = [row for row in ctors if isinstance(row, dict)]
    rec_rows = [row for row in recs if isinstance(row, dict)]
    rules = [
        rule
        for rec in rec_rows
        for rule in (rec.get("rules") if isinstance(rec.get("rules"), list) else [])
        if isinstance(rule, dict)
    ]

    def nums(rows: Iterable[dict[str, Any]], key: str) -> list[int]:
        return [int(row.get(key, 0)) for row in rows]

    return {
        "types": len(type_rows),
        "constructors": len(ctor_rows),
        "recursors": len(rec_rows),
        "type_num_params": nums(type_rows, "numParams"),
        "type_num_indices": nums(type_rows, "numIndices"),
        "type_num_nested": nums(type_rows, "numNested"),
        "type_level_param_counts": [
            len(row.get("levelParams", [])) if isinstance(row.get("levelParams"), list) else 0
            for row in type_rows
        ],
        "recursive": any(bool(row.get("isRec")) for row in type_rows),
        "reflexive": any(bool(row.get("isReflexive")) for row in type_rows),
        "unsafe_type": any(bool(row.get("isUnsafe")) for row in type_rows),
        "ctor_num_fields": nums(ctor_rows, "numFields"),
        "ctor_num_params": nums(ctor_rows, "numParams"),
        "ctor_level_param_counts": [
            len(row.get("levelParams", [])) if isinstance(row.get("levelParams"), list) else 0
            for row in ctor_rows
        ],
        "unsafe_ctor": any(bool(row.get("isUnsafe")) for row in ctor_rows),
        "rec_num_params": nums(rec_rows, "numParams"),
        "rec_num_indices": nums(rec_rows, "numIndices"),
        "rec_num_motives": nums(rec_rows, "numMotives"),
        "rec_num_minors": nums(rec_rows, "numMinors"),
        "rec_level_param_counts": [
            len(row.get("levelParams", [])) if isinstance(row.get("levelParams"), list) else 0
            for row in rec_rows
        ],
        "rec_k": any(bool(row.get("k")) for row in rec_rows),
        "unsafe_rec": any(bool(row.get("isUnsafe")) for row in rec_rows),
        "rule_count": len(rules),
        "rule_field_counts": [int(rule.get("nfields", 0)) for rule in rules],
    }


def derive_dimensions(
    expr_tags: Counter[str],
    level_tags: Counter[str],
    decl_counts: Counter[str],
    unsupported_tags: Counter[str],
    inductives: list[dict[str, Any]],
    name_leaves: set[str],
    filename: str,
) -> list[str]:
    dims: set[str] = set()

    if decl_counts["inductive"]:
        dims.add("inductive")
    if decl_counts["axiom"]:
        dims.add("axiom")
    if decl_counts["def"]:
        dims.add("definition")
    if decl_counts["thm"]:
        dims.add("theorem")

    if expr_tags["letE"]:
        dims.add("let")
    if expr_tags["lam"]:
        dims.add("lambda")
    if expr_tags["forallE"]:
        dims.add("dependent_function_space")
    if level_tags["param"]:
        dims.add("universe_polymorphism")
    if level_tags["imax"]:
        dims.add("universe_imax")
    if level_tags["max"]:
        dims.add("universe_max")

    for tag in sorted(expr_tags):
        if tag not in KNOWN_EXPR_TAGS:
            dims.add(f"unsupported_expr:{tag}")
            lower = tag.lower()
            if "proj" in lower:
                dims.add("projection")
            if "lit" in lower:
                dims.add("literal")
    for tag in sorted(unsupported_tags):
        dims.add(f"unsupported_decl:{tag}")

    for block in inductives:
        if block["types"] > 1:
            dims.add("mutual_inductive")
        if block["constructors"] == 0:
            dims.add("zero_constructor")
        if block["constructors"] == 1:
            dims.add("single_constructor")
        if block["constructors"] > 1:
            dims.add("multiple_constructors")
        if any(v > 0 for v in block["type_num_params"]):
            dims.add("parameters")
        if any(v > 0 for v in block["type_num_indices"]) or any(
            v > 0 for v in block["rec_num_indices"]
        ):
            dims.add("indices")
        if any(v > 0 for v in block["type_num_nested"]):
            dims.add("nested_inductive")
        if block["recursive"]:
            dims.add("recursive_inductive")
        if block["reflexive"]:
            dims.add("reflexive_inductive")
        if block["unsafe_type"] or block["unsafe_ctor"] or block["unsafe_rec"]:
            dims.add("unsafe_inductive")
        if any(v > 0 for v in block["ctor_num_fields"]):
            dims.add("constructor_fields")
        elif block["constructors"] > 0:
            dims.add("nullary_constructors")
        if block["rec_k"]:
            dims.add("recursor_rule_K")
        if block["recursors"]:
            dims.add("recursor_metadata")
        if block["rule_count"]:
            dims.add("recursor_rules")

    lower_filename = filename.lower()
    lowered_names = {name.lower() for name in name_leaves}
    if "eqtype" in lower_filename or "eq" in lowered_names:
        dims.add("equality_family")
    if "quot" in lower_filename or any(name.startswith("quot") for name in lowered_names):
        dims.add("quotient_family")
    if "proj" in lower_filename:
        dims.add("projection")
    if "eta" in lower_filename:
        dims.add("eta")
    if "proofirrelevance" in lower_filename:
        dims.add("proof_irrelevance")
    if "lit" in lower_filename:
        dims.add("literal")
    if "reduction" in lower_filename or "eqns" in lower_filename:
        dims.add("computation_observation")

    return sorted(dims)


def checker_exit(checker: Path | None, path: Path) -> int | None:
    if checker is None:
        return None
    with path.open("rb") as stream:
        completed = subprocess.run(
            [str(checker.resolve())],
            stdin=stream,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
        )
    return completed.returncode


def analyze_case(case: CasePath, checker: Path | None = None) -> dict[str, Any]:
    records = load_records(case.path)
    expr_tags: Counter[str] = Counter()
    level_tags: Counter[str] = Counter()
    decl_counts: Counter[str] = Counter()
    unsupported: Counter[str] = Counter()
    inductives: list[dict[str, Any]] = []
    leaves: set[str] = set()

    for record in records:
        expr = record_expr_tag(record)
        if expr is not None:
            expr_tags[expr] += 1
        level = record_level_tag(record)
        if level is not None:
            level_tags[level] += 1
        leaf = name_leaf(record)
        if leaf:
            leaves.add(leaf)
        for tag in DECL_TAGS:
            if tag in record:
                decl_counts[tag] += 1
        for tag in unsupported_decl_tags(record):
            unsupported[tag] += 1
        value = record.get("inductive")
        if isinstance(value, dict):
            inductives.append(inductive_summary(value))

    current_exit = checker_exit(checker, case.path)
    if current_exit is None:
        current_status = "not_measured"
    elif current_exit == case.expected_exit:
        current_status = "already_matches"
    elif current_exit == 2:
        current_status = "unknown"
    elif current_exit == 3:
        current_status = "error"
    else:
        current_status = "mismatch"

    dimensions = derive_dimensions(
        expr_tags,
        level_tags,
        decl_counts,
        unsupported,
        inductives,
        leaves,
        case.path.name,
    )
    structural = {
        "expr_tags": dict(sorted(expr_tags.items())),
        "level_tags": dict(sorted(level_tags.items())),
        "declarations": dict(sorted(decl_counts.items())),
        "unsupported_declaration_tags": dict(sorted(unsupported.items())),
        "inductives": inductives,
        "dimensions": dimensions,
    }
    signature = hashlib.sha256(
        json.dumps(structural, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]

    return {
        "number": case.number,
        "path": f"{case.path.parent.name}/{case.path.name}",
        "sha256": hashlib.sha256(case.path.read_bytes()).hexdigest(),
        "expected_exit": case.expected_exit,
        "g15_exit": current_exit,
        "g15_status": current_status,
        "name_leaves": sorted(leaves),
        "structural": structural,
        "structural_signature": signature,
    }


def build_atlas(
    cases: list[CasePath],
    checker: Path | None,
    sealed_end: int,
    report_start: int,
) -> dict[str, Any]:
    rows = [analyze_case(case, checker) for case in cases]
    first_seen: dict[str, int] = {}
    sealed_dims: set[str] = set()

    for row in rows:
        for dim in row["structural"]["dimensions"]:
            first_seen.setdefault(dim, row["number"])
            if row["number"] <= sealed_end:
                sealed_dims.add(dim)

    report_rows = [row for row in rows if row["number"] >= report_start]
    for row in report_rows:
        dims = row["structural"]["dimensions"]
        row["new_dimensions_vs_sealed"] = sorted(set(dims) - sealed_dims)
        row["first_occurrence_dimensions"] = sorted(
            dim for dim in dims if first_seen.get(dim) == row["number"]
        )

    clusters: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for row in report_rows:
        clusters[tuple(row["structural"]["dimensions"])].append(row["number"])

    frontier = [
        {"dimension": dim, "first_case": number}
        for dim, number in sorted(first_seen.items(), key=lambda item: (item[1], item[0]))
        if number >= report_start
    ]

    statuses = Counter(row["g15_status"] for row in report_rows)
    return {
        "schema": "lka-semantic-atlas-v0",
        "authority": {
            "interpretation": "read-only discovery instrument; no checker authority",
            "sealed_end": sealed_end,
            "report_start": report_start,
        },
        "summary": {
            "cases": len(report_rows),
            "g15_status_counts": dict(sorted(statuses.items())),
            "dimension_clusters": len(clusters),
            "new_dimension_first_occurrences": len(frontier),
        },
        "frontier": frontier,
        "clusters": [
            {"dimensions": list(key), "cases": values, "count": len(values)}
            for key, values in sorted(clusters.items(), key=lambda item: item[1][0])
        ],
        "cases": report_rows,
    }


def markdown(atlas: dict[str, Any]) -> str:
    s = atlas["summary"]
    lines = [
        "# LKA Semantic Atlas v0",
        "",
        "READ-ONLY DISCOVERY INSTRUMENT. This file does not grant checker authority.",
        "",
        f"- Cases analyzed: {s['cases']}",
        f"- Structural clusters: {s['dimension_clusters']}",
        f"- First-occurrence dimensions in report range: {s['new_dimension_first_occurrences']}",
        f"- Sealed-checker statuses: {json.dumps(s['g15_status_counts'], sort_keys=True)}",
        "",
        "## First-occurrence frontier",
        "",
        "| Case | Dimension |",
        "| ---: | --- |",
    ]
    for item in atlas["frontier"]:
        lines.append(f"| {item['first_case']:03d} | {item['dimension']} |")

    lines.extend(
        [
            "",
            "## Structural clusters",
            "",
            "| First | Count | Cases | Dimensions |",
            "| ---: | ---: | --- | --- |",
        ]
    )
    for cluster in atlas["clusters"]:
        cases = ", ".join(f"{n:03d}" for n in cluster["cases"])
        dims = ", ".join(cluster["dimensions"])
        lines.append(f"| {cluster['cases'][0]:03d} | {cluster['count']} | {cases} | {dims} |")

    lines.extend(
        [
            "",
            "## Case-level residual view",
            "",
            "| Case | Expected | G15 | New dimensions vs sealed G15 | File |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    verdict_names = {0: "ACCEPT", 1: "REJECT", 2: "UNKNOWN", 3: "ERROR"}
    for row in atlas["cases"]:
        expected = "ACCEPT" if row["expected_exit"] == 0 else "REJECT"
        current = (
            "unmeasured"
            if row["g15_exit"] is None
            else verdict_names.get(row["g15_exit"], str(row["g15_exit"]))
        )
        dims = ", ".join(row["new_dimensions_vs_sealed"]) or "-"
        lines.append(
            f"| {row['number']:03d} | {expected} | {current} | {dims} | {row['path']} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tutorial-output", required=True, type=Path)
    parser.add_argument("--checker", type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=141)
    parser.add_argument("--sealed-end", type=int, default=41)
    parser.add_argument("--report-start", type=int, default=42)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = numbered_cases(args.tutorial_output, args.start, args.end)
    atlas = build_atlas(
        cases,
        checker=args.checker,
        sealed_end=args.sealed_end,
        report_start=args.report_start,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(atlas, indent=2, sort_keys=True) + "\n")
    args.markdown_output.write_text(markdown(atlas))
    print(json.dumps(atlas["summary"], sort_keys=True))
    print("FRONTIER")
    for item in atlas["frontier"]:
        print(f"{item['first_case']:03d}\t{item['dimension']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
