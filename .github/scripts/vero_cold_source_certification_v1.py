from __future__ import annotations

import hashlib
import difflib
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path.cwd()
SOURCE = (ROOT / "full48" / "full48_decontaminated_v1").resolve()
OUT = (ROOT / "cold_source_certification_v1").resolve()
PROJECT = OUT / "project"
RING = PROJECT / "Galoistools" / "Proof" / "Ring.lean"
RESULT = OUT / "result.json"

REPAIRS = {
    "mul_eval_hom f g p x hp": "mul_eval_hom f g",
    "mul_eval_hom g f p x hp": "mul_eval_hom g f",
    "mul_eval_hom g h p x hp": "mul_eval_hom g h",
    "mul_eval_hom (Galoistools.gfMul f g p) h p x hp":
        "mul_eval_hom (Galoistools.gfMul f g p) h",
    "mul_eval_hom f (Galoistools.gfMul g h p) p x hp":
        "mul_eval_hom f (Galoistools.gfMul g h p)",
    "mul_eval_hom f (Galoistools.gfAdd g h p) p x hp":
        "mul_eval_hom f (Galoistools.gfAdd g h p)",
    "mul_eval_hom f h p x hp": "mul_eval_hom f h",
}
EXPECTED_OCCURRENCES = 9
FORBIDDEN = ("sorry", "admit", "axiom", "unsafe", "Classical.arbitrary")


def run(cmd: list[str], timeout: int = 360) -> dict:
    cp = subprocess.run(cmd, cwd=PROJECT, text=True, capture_output=True, timeout=timeout)
    raw = cp.stdout + "\n" + cp.stderr
    return {"exit": cp.returncode, "tail": raw[-24000:]}


def prove_blocks(src: str) -> list[tuple[str, str]]:
    start = re.compile(r"-- !benchmark @start proof def=([A-Za-z0-9_]+) kind=prove[^\n]*\n")
    blocks = []
    for match in start.finditer(src):
        name = match.group(1)
        end = src.index(f"-- !benchmark @end proof def={name}", match.end())
        blocks.append((name, src[match.end():end]))
    return blocks


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
shutil.copytree(SOURCE, PROJECT)

# Cache independence is the point of this gate.
for cache in PROJECT.rglob(".lake"):
    if cache.is_dir():
        shutil.rmtree(cache)

before = RING.read_text()
after = before
counts = {}
for old, new in REPAIRS.items():
    count = after.count(old)
    counts[old] = count
    after = after.replace(old, new)
RING.write_text(after)

# Every repair is a one-line substitution; count the removed and added lines.
line_delta = [
    line for line in difflib.ndiff(before.splitlines(), after.splitlines())
    if line.startswith("- ") or line.startswith("+ ")
]

blocks = prove_blocks(after)
taint = {
    name: [token for token in FORBIDDEN if re.search(rf"\b{re.escape(token)}\b", body)]
    for name, body in blocks
}
taint = {name: hits for name, hits in taint.items() if hits}

explicit_ring = run(["lake", "lean", "Galoistools/Proof/Ring.lean"])
subprocess.run(["lake", "clean"], cwd=PROJECT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
cold_build = run(["lake", "build"])

gates = {
    "source_artifact_present": SOURCE.is_dir(),
    "exactly_nine_captured_argument_repairs": sum(counts.values()) == EXPECTED_OCCURRENCES,
    "only_nine_source_lines_changed": len(line_delta) == 2 * EXPECTED_OCCURRENCES,
    "forty_eight_prove_blocks_present": len(blocks) == 48,
    "prove_blocks_have_no_forbidden_tokens": not taint,
    "explicit_ring_compiles": explicit_ring["exit"] == 0,
    "cold_full_build_compiles": cold_build["exit"] == 0,
}
passed = all(gates.values())
payload = {
    "schema": "msi.vero-cold-source-certification.v1",
    "passed": passed,
    "gates": gates,
    "repair_counts": counts,
    "line_delta": line_delta,
    "before_sha256": hashlib.sha256(before.encode()).hexdigest(),
    "after_sha256": hashlib.sha256(after.encode()).hexdigest(),
    "prove_block_taint": taint,
    "explicit_ring": explicit_ring,
    "cold_build": cold_build,
}
RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True))
print("VERO_COLD_SOURCE_CERTIFICATION_V1", json.dumps({"passed": passed, "gates": gates}, sort_keys=True))
raise SystemExit(0 if passed else 1)

