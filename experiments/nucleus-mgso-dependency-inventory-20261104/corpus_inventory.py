"""Source-inventory coverage and independent native verdict census on fixtures."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time

from qualification import RUN_ENV
from semantic_inventory import InventoryError, inventory


def survey(directory: Path, binary: Path | None = None):
    directory = Path(directory).resolve(strict=True)
    files = sorted(directory.glob("*.ndjson"))
    if not files or len(files) > 1000:
        raise ValueError("fixture corpus absent or unexpectedly broad")
    if binary is not None:
        binary = Path(binary).resolve(strict=True)
        if not binary.is_file():
            raise ValueError("Nucleus binary unavailable")
    rows = []
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise ValueError("unsafe fixture")
        source = path.read_bytes()
        start = time.perf_counter_ns()
        try:
            view = inventory(source)
            status = view["status"]
            declarations = len(view["declarations"])
            reason = None
        except (InventoryError, RecursionError) as err:
            status, declarations, reason = "UNKNOWN", 0, str(err)
        candidate_ns = time.perf_counter_ns() - start
        row = {"case": path.name, "source_sha256": hashlib.sha256(source).hexdigest(),
               "source_size": len(source), "inventory_status": status,
               "declarations": declarations, "inventory_refusal": reason,
               "inventory_wall_ns": candidate_ns, "proof_skips": 0,
               "verification_reuse_authority": "NONE"}
        if binary is not None:
            start = time.perf_counter_ns()
            result = subprocess.run([str(binary)], input=source, capture_output=True,
                                    env=RUN_ENV, timeout=30, check=False)
            elapsed = time.perf_counter_ns() - start
            if result.returncode not in (0, 1, 2, 3) or result.stdout:
                raise ValueError(f"unexpected Nucleus outcome for {path.name}")
            row.update({"native_exit_code": result.returncode,
                        "native_wall_ns": elapsed,
                        "native_stderr_sha256": hashlib.sha256(result.stderr).hexdigest()})
        rows.append(row)
    counts = Counter(row["inventory_status"] for row in rows)
    native = Counter(row.get("native_exit_code") for row in rows if binary is not None)
    return {"type": "nucleus.source-inventory-corpus-observation.v1",
            "source_directory": "metatron-kernel/tests/fixtures",
            "fixture_count": len(rows),
            "candidate_count": counts["CANDIDATE_ONLY"],
            "refused_count": counts["UNKNOWN"],
            "native_invocations": len(rows) if binary is not None else 0,
            "native_verdict_counts": {str(key): n for key, n in sorted(native.items())},
            "median_inventory_ms": statistics.median(
                [r["inventory_wall_ns"] / 1e6 for r in rows]),
            "median_native_ms": statistics.median(
                [r["native_wall_ns"] / 1e6 for r in rows]) if binary is not None else None,
            "complete_kernel_dependency_closure": "UNKNOWN",
            "verification_reuse_authority": "NONE", "proof_skips": 0,
            "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    report = survey(options.fixtures, options.binary)
    options.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"},
                     sort_keys=True))


if __name__ == "__main__":
    main()
