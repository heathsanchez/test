from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path.cwd()
SOURCE = (ROOT / "full48" / "full48_decontaminated_v1").resolve()
OUT = (ROOT / "division_compounding_v1").resolve()
RESULT = OUT / "result.json"
DIVISION = Path("Galoistools/Proof/Division.lean")

# Repairs certified independently by Vero cold source certification V1.
CAPTURE_REPAIRS = {
    "mul_eval_hom f g p x hp": "mul_eval_hom f g",
    "mul_eval_hom g f p x hp": "mul_eval_hom g f",
    "mul_eval_hom g h p x hp": "mul_eval_hom g h",
    "mul_eval_hom (Galoistools.gfMul f g p) h p x hp": "mul_eval_hom (Galoistools.gfMul f g p) h",
    "mul_eval_hom f (Galoistools.gfMul g h p) p x hp": "mul_eval_hom f (Galoistools.gfMul g h p)",
    "mul_eval_hom f (Galoistools.gfAdd g h p) p x hp": "mul_eval_hom f (Galoistools.gfAdd g h p)",
    "mul_eval_hom f h p x hp": "mul_eval_hom f h",
}


def run(project: Path) -> dict:
    cp = subprocess.run(
        ["lake", "lean", str(DIVISION)], cwd=project, text=True,
        capture_output=True, timeout=180
    )
    raw = cp.stdout + "\n" + cp.stderr
    errors = [line for line in raw.splitlines() if "error:" in line]
    return {"exit": cp.returncode, "error_count": len(errors), "errors": errors[:40], "tail": raw[-16000:]}


def global_bridge_span(src: str) -> tuple[int, int]:
    start = src.index("theorem gfStrip_eq_refGfStrip")
    end = src.index("-- !benchmark @end global_aux", start)
    return start, end


def chain_seed_span(src: str) -> tuple[int, int]:
    start = src.index("  have strip_len : ∀ xs : List Nat,")
    end = src.index("  have norm_head_mod_eq : ∀ a as,", start)
    return start, end


def replace_span(src: str, span: tuple[int, int], replacement: str) -> str:
    a, b = span
    return src[:a] + replacement.rstrip() + "\n" + src[b:]


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

clean = SOURCE / DIVISION
source = clean.read_text()

a0, a1 = global_bridge_span(source)
b0, b1 = chain_seed_span(source)
bridge_a = source[a0:a1]
bridge_b = source[b0:b1]

cut_a = """theorem gfStrip_eq_refGfStrip (f : List Nat) :
    Galoistools.gfStrip f = Galoistools.refGfStrip f := by
  exact False.elim (by omega)"""
cut_b = """  have strip_len : ∀ xs : List Nat,
      (Galoistools.refGfStrip xs).length ≤ xs.length := by
    intro xs
    exact Nat.zero_le _"""

# Spans shift, so apply B first (it occurs later in the file), then A.
def state(has_a: bool, has_b: bool) -> str:
    s = source
    if not has_b:
        s = replace_span(s, (b0, b1), cut_b)
    if not has_a:
        s = replace_span(s, (a0, a1), cut_a)
    return s


matrix = {}
for label, has_a, has_b in (
    ("neither", False, False),
    ("normalization_bridge_only", True, False),
    ("chain_seed_only", False, True),
    ("joint_compounded", True, True),
):
    project = OUT / label
    shutil.copytree(SOURCE, project)
    for cache in project.rglob(".lake"):
        if cache.is_dir(): shutil.rmtree(cache)
    ring = project / "Galoistools/Proof/Ring.lean"
    ring_src = ring.read_text()
    for old, new in CAPTURE_REPAIRS.items(): ring_src = ring_src.replace(old, new)
    ring.write_text(ring_src)
    (project / DIVISION).write_text(state(has_a, has_b))
    matrix[label] = run(project)

# Confirm the joint state is not merely compiling from a cache.
joint = OUT / "joint_compounded"
subprocess.run(["lake", "clean"], cwd=joint, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
cold_full = subprocess.run(["lake", "build"], cwd=joint, text=True, capture_output=True, timeout=300)

joint_src = (joint / DIVISION).read_text()
chain_names = [
    "strip_len", "norm_head_mod_eq", "norm_lead_coprime",
    "monic_leadCoeff_one", "monic_norm",
]
chain_present = all(re.search(rf"\b{re.escape(name)}\b", joint_src) for name in chain_names)

gates = {
    "neither_fails": matrix["neither"]["exit"] != 0,
    "normalization_bridge_alone_insufficient": matrix["normalization_bridge_only"]["exit"] != 0,
    "chain_seed_alone_insufficient": matrix["chain_seed_only"]["exit"] != 0,
    "joint_interfaces_compile": matrix["joint_compounded"]["exit"] == 0,
    "five_stage_downstream_chain_present": chain_present,
    "joint_state_cold_full_builds": cold_full.returncode == 0,
}
passed = all(gates.values())
payload = {
    "schema": "msi.vero-division-interface-compounding.v1",
    "claim_scope": "cross-family replication of interface-mediated capability compounding; interfaces are extracted, not autonomously discovered",
    "passed": passed,
    "gates": gates,
    "matrix": matrix,
    "downstream_chain": chain_names,
    "cold_full_build": {"exit": cold_full.returncode, "tail": (cold_full.stdout + cold_full.stderr)[-16000:]},
}
RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True))
print("VERO_DIVISION_COMPOUNDING_V1", json.dumps({"passed": passed, "gates": gates}, sort_keys=True))
raise SystemExit(0 if passed else 1)

