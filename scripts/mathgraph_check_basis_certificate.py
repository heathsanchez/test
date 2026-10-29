"""Finite minimum detection-basis certificate for three TestSuiteBench suites.

Input is the unmodified GitHub Actions evaluation artifact ZIP. The output is
only a certificate about its observed mutant/test matrix, not a general claim
about correctness or future mutants. No mutant source is read or executed.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import io
import itertools
import json
from pathlib import Path
import sys
import zipfile

MODES = ("baseline", "signature", "obligations")
TASK = "sitkevij__hex.61ae69b"
EXPECTED_SOURCE_JSON_SHA256 = {
    "baseline": "e64178dc20614cf5d7db4e92aadcaefc3ed2d9b7dd5f44f4ef88a47df277b9b4",
    "signature": "7f42d6757cdcf044f614925287aaa9f4845208bdfb2a3dbef00d6b0e0363e3df",
    "obligations": "7c5540801c8cc1e440a7cbf1603dbccd8d44677f62c3e6e1c9642f8cf628f10d",
}


def calculate(archive: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        files = {mode: f"{mode}/{TASK}/{TASK}.test_eval.json" for mode in MODES}
        original = {mode: z.read(path) for mode, path in files.items()}
    source_hashes = {mode: hashlib.sha256(blob).hexdigest() for mode, blob in original.items()}
    assert source_hashes == EXPECTED_SOURCE_JSON_SHA256, ("evidence hash mismatch", source_hashes)
    sources = {mode: json.loads(blob) for mode, blob in original.items()}

    mutants_by_mode = {}
    for mode, doc in sources.items():
        assert doc["error_code"] is None, (mode, doc["error_code"])
        binaries = doc["binary_results"]
        references = [r for r in binaries if r["role"] == "ground_truth"]
        assert len(references) == 1, (mode, "ground truth missing or duplicated")
        reference = references[0]
        assert reference["error_code"] is None, (mode, "ground truth errored")
        assert len(reference["test_results"]) == 48, (mode, "incorrect test budget")
        assert all(t["status"] == "passed" for t in reference["test_results"]), (mode, "invalid reference tests")
        mutants = [r for r in binaries if r["role"] != "ground_truth"]
        assert len(mutants) == 54, (mode, "mutant universe changed")
        assert all(r["error_code"] is None for r in mutants), (mode, "binary evaluation error")
        mutants_by_mode[mode] = {r["binary_id"] for r in mutants}
    assert mutants_by_mode["baseline"] == mutants_by_mode["signature"] == mutants_by_mode["obligations"]

    killed_by_test: dict[str, set[str]] = defaultdict(set)
    killed_by_mode: dict[str, set[str]] = defaultdict(set)
    for mode, doc in sources.items():
        for binary in doc["binary_results"]:
            if binary["role"] == "ground_truth":
                continue
            for test in binary["test_results"]:
                if test["status"] != "passed":
                    assert test["name"].startswith(f"tests.{mode}."), test["name"]
                    killed_by_test[test["name"]].add(binary["binary_id"])
                    killed_by_mode[mode].add(binary["binary_id"])

    mutant_union = sorted(set.union(*(killed_by_mode[m] for m in MODES)))
    assert len(mutant_union) == 19, len(mutant_union)
    mutant_bits = {name: 1 << index for index, name in enumerate(mutant_union)}
    representative_by_mask: dict[int, str] = {}
    for test, mutants in killed_by_test.items():
        mask = sum(mutant_bits[m] for m in mutants)
        if mask and (mask not in representative_by_mask or test < representative_by_mask[mask]):
            representative_by_mask[mask] = test

    full = (1 << len(mutant_union)) - 1
    candidates = sorted(representative_by_mask.items(), key=lambda p: (-p[0].bit_count(), p[1]))
    assert len(candidates) == 20, len(candidates)

    # Construct a real witness without assuming a particular test name/order.
    remaining = full
    selected = []
    while remaining:
        mask, name = max(candidates, key=lambda p: (p[0] & remaining).bit_count())
        assert mask & remaining
        selected.append(name)
        remaining &= ~mask

    # Independent, exhaustive minimality proof: enumerate all strictly smaller
    # subsets of the 20 distinct detection vectors. Deduplicating equal masks
    # cannot remove a smaller solution (equal masks are interchangeable).
    distinct_masks = sorted(representative_by_mask)
    checked = 0
    for size in range(len(selected)):
        for subset in itertools.combinations(distinct_masks, size):
            checked += 1
            cover = 0
            for mask in subset:
                cover |= mask
            if cover == full:
                raise AssertionError(f"found smaller cover of size {size}")

    assert len(selected) == 11 and checked == 616666, (len(selected), checked)
    actual = set.union(*(killed_by_test[t] for t in selected))
    assert actual == set(mutant_union)
    return {
        "claim": "MINIMUM_OBSERVED_MUTANT_DETECTION_BASIS",
        "epistemic_status": "WARRANTED_BOUNDED_EXHAUSTIVE_IN_SAMPLE",
        "task": TASK,
        "benchmark_commit": "583d2eb1ffa19f3aa0c04b7455fd13d846b4c8d9",
        "actions_run_id": 40802435111,
        "actions_artifact_id": 12867250385,
        "reference_test_count_by_suite": {mode: 48 for mode in MODES},
        "source_json_sha256": source_hashes,
        "source_total_tests": 48 * len(MODES),
        "total_mutants": len(mutants_by_mode["baseline"]),
        "observed_union_mutants": mutant_union,
        "mutant_kills_by_suite": {mode: sorted(killed_by_mode[mode]) for mode in MODES},
        "distinct_nonempty_detection_vectors": len(distinct_masks),
        "minimum_basis_size": len(selected),
        "selected_tests": [
            {"name": name, "kills": sorted(killed_by_test[name])}
            for name in selected
        ],
        "proof": {
            "method": "exhaustive_enumeration_of_distinct_detection_vector_subsets",
            "subsets_checked_below_witness_size": checked,
            "smaller_full_cover_exists": False,
            "witness_covers_all_observed_mutants": True,
        },
        "claim_boundary": "Minimum is relative ONLY to these 19 observed mutants and 144 tests; hidden/novel defects UNKNOWN. Not a mandate to delete other tests.",
    }


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("archive", help="Path to the official artifact zip, or - for standard input")
    cli.add_argument("--output", type=Path, help="Optional JSON output file")
    args = cli.parse_args()
    content = sys.stdin.buffer.read() if args.archive == "-" else Path(args.archive).read_bytes()
    result = calculate(content)
    packet = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(packet)
    print(f"CERTIFIED basis={result['minimum_basis_size']} observed_mutants={len(result['observed_union_mutants'])} exhaustive_subsets={result['proof']['subsets_checked_below_witness_size']}")


if __name__ == "__main__":
    main()
