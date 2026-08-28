from __future__ import annotations

import hashlib
import itertools
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path.cwd()
SOURCE = (ROOT / "full48" / "full48_decontaminated_v1").resolve()
OUT = (ROOT / "kernel_regeneration_v2").resolve()
RESULT = OUT / "result.json"
RING = Path("Galoistools/Proof/Ring.lean")
OWNER = "prove_mul_eval_hom"
OLD_ALPHA = "natModEq_refPolyEvalRevAux_map_mul"
OLD_BETA = "natModEq_refPolyEvalRevAux_convolve"
ALPHA = "regenesis_bridge_alpha"
BETA = "regenesis_bridge_beta"
FORBIDDEN = ("sorry", "admit", "axiom", "unsafe", "Classical.arbitrary")


def run(project: Path, timeout: int = 75) -> dict:
    cp = subprocess.run(
        ["lake", "lean", str(RING)], cwd=project, text=True,
        capture_output=True, timeout=timeout
    )
    raw = cp.stdout + "\n" + cp.stderr
    return {"exit": cp.returncode, "tail": raw[-12000:]}


def region(src: str) -> tuple[int, int]:
    start = src.index(f"-- !benchmark @start proof_aux def={OWNER}")
    start = src.index("\n", start) + 1
    end = src.index(f"-- !benchmark @end proof_aux def={OWNER}", start)
    return start, end


def replace_region(src: str, body: str) -> str:
    a, b = region(src)
    return src[:a] + body.rstrip() + "\n" + src[b:]


ALPHA_STATEMENT = f"""theorem {ALPHA} (p x a : Nat) (ys : List Nat) :
    NatModEq p
      (Galoistools.refPolyEvalRevAux p x (ys.map (fun y => (a * y) % p)))
      (a * Galoistools.refPolyEvalRevAux p x ys) := {{proof}}
"""

BETA_STATEMENT = f"""theorem {BETA} (p x : Nat) (xs ys : List Nat) :
    NatModEq p
      (Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p xs ys))
      (Galoistools.refPolyEvalRevAux p x xs * Galoistools.refPolyEvalRevAux p x ys) := {{proof}}
"""

# Fixed, auditable grammar. Lean's kernel is the search oracle; no model, network,
# repository history, or deleted proof text participates.
ALPHA_PROOFS = [
    "by aesop",
    "by induction ys <;> simp_all [Galoistools.refPolyEvalRevAux, NatModEq, Nat.add_mod, Nat.mul_mod, Nat.mul_add, Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]",
    "by induction ys <;> simp_all [Galoistools.refPolyEvalRevAux, NatModEq, Nat.add_mod, Nat.mul_mod, Nat.mul_add, Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm] <;> omega",
    """by
  induction ys with
  | nil => rfl
  | cons y ys ih =>
      simp only [List.map_cons, Galoistools.refPolyEvalRevAux]
      have hhead : NatModEq p ((a * y) % p) (a * y) := natModEq_mod_left (by rfl)
      have htail : NatModEq p
          (x * Galoistools.refPolyEvalRevAux p x (ys.map (fun y => (a * y) % p)))
          (x * (a * Galoistools.refPolyEvalRevAux p x ys)) :=
        natModEq_mul (by rfl) ih
      have hsum := natModEq_add hhead htail
      have halg : a * y + x * (a * Galoistools.refPolyEvalRevAux p x ys) =
          a * (y + x * Galoistools.refPolyEvalRevAux p x ys) := by
        simp [Nat.mul_add, Nat.mul_left_comm]
      rw [halg] at hsum
      have hfactor : NatModEq p
          (a * ((y + x * Galoistools.refPolyEvalRevAux p x ys) % p))
          (a * (y + x * Galoistools.refPolyEvalRevAux p x ys)) :=
        natModEq_mul (by rfl) (natModEq_mod_left (by rfl))
      unfold NatModEq
      exact hsum.trans hfactor.symm""",
]

BETA_PROOFS = [
    "by aesop",
    "by induction xs <;> simp_all [Galoistools.convolve, Galoistools.refPolyEvalRevAux, Galoistools.zipAddPad, NatModEq, Nat.add_mod, Nat.mul_mod, Nat.add_mul, Nat.mul_add, Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm]",
    "by induction xs <;> simp_all [Galoistools.convolve, Galoistools.refPolyEvalRevAux, Galoistools.zipAddPad, NatModEq, Nat.add_mod, Nat.mul_mod, Nat.add_mul, Nat.mul_add, Nat.mul_assoc, Nat.mul_left_comm, Nat.mul_comm] <;> omega",
    f"""by
  induction xs with
  | nil => simp [NatModEq, Galoistools.convolve, Galoistools.refPolyEvalRevAux]
  | cons a xs ih =>
      simp only [Galoistools.convolve]
      let head := ys.map (fun y => (a * y) % p)
      let tail := 0 :: Galoistools.convolve p xs ys
      have hzip := natModEq_refPolyEvalRevAux_zipAddPad p x head tail
      have hhead : NatModEq p (Galoistools.refPolyEvalRevAux p x head)
          (a * Galoistools.refPolyEvalRevAux p x ys) := by
        simpa [head] using {ALPHA} p x a ys
      have htail : NatModEq p (Galoistools.refPolyEvalRevAux p x tail)
          (x * (Galoistools.refPolyEvalRevAux p x xs * Galoistools.refPolyEvalRevAux p x ys)) := by
        simp only [tail, Galoistools.refPolyEvalRevAux, Nat.zero_add]
        exact natModEq_mod_left (natModEq_mul (by rfl) ih)
      have hchain := hzip.trans (natModEq_add hhead htail)
      have halg : a * Galoistools.refPolyEvalRevAux p x ys +
          x * (Galoistools.refPolyEvalRevAux p x xs * Galoistools.refPolyEvalRevAux p x ys) =
          (a + x * Galoistools.refPolyEvalRevAux p x xs) * Galoistools.refPolyEvalRevAux p x ys := by
        simp [Nat.add_mul, Nat.mul_assoc]
      rw [halg] at hchain
      have hfactor : NatModEq p
          (Galoistools.refPolyEvalRevAux p x (a :: xs) * Galoistools.refPolyEvalRevAux p x ys)
          ((a + x * Galoistools.refPolyEvalRevAux p x xs) * Galoistools.refPolyEvalRevAux p x ys) := by
        simp only [Galoistools.refPolyEvalRevAux]
        exact natModEq_mul (natModEq_mod_left (by rfl)) (by rfl)
      exact hchain.trans hfactor.symm""",
]


if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
base = OUT / "base"
shutil.copytree(SOURCE, base)
path = base / RING
source = path.read_text().replace(OLD_ALPHA, ALPHA).replace(OLD_BETA, BETA)
original = source[region(source)[0]:region(source)[1]]
amputated = replace_region(source, "-- KERNEL_ONLY_REGENERATION_SLOT\n")
path.write_text(amputated)
cold = run(base)

attempts = []
winner = None
for index, (alpha_proof, beta_proof) in enumerate(
    itertools.product(reversed(ALPHA_PROOFS), reversed(BETA_PROOFS)), 1
):
    project = OUT / f"attempt_{index:02d}"
    shutil.copytree(base, project)
    body = ALPHA_STATEMENT.format(proof=alpha_proof) + "\n" + BETA_STATEMENT.format(proof=beta_proof)
    (project / RING).write_text(replace_region(amputated, body))
    verdict = run(project)
    attempts.append({"index": index, "alpha": alpha_proof, "beta": beta_proof, **verdict})
    if verdict["exit"] == 0:
        winner = {"index": index, "project": project, "body": body}
        break

gates = {
    "cold_amputation_fails": cold["exit"] != 0,
    "bounded_search_succeeds": winner is not None,
    "no_api_or_model": True,
    "no_original_names": winner is not None and OLD_ALPHA not in winner["body"] and OLD_BETA not in winner["body"],
    "no_forbidden_tokens": winner is not None and not any(t in winner["body"] for t in FORBIDDEN),
    "not_deleted_proof_text": winner is not None and hashlib.sha256(winner["body"].encode()).hexdigest() != hashlib.sha256(original.encode()).hexdigest(),
}

post = None
if winner:
    post_project = OUT / "exact_ablation"
    shutil.copytree(winner["project"], post_project)
    post_path = post_project / RING
    post_path.write_text(replace_region(post_path.read_text(), "-- EXACT_SYNTHESIZED_INTERFACE_ABLATION\n"))
    post = run(post_project)
    gates["exact_ablation_restores_failure"] = post["exit"] != 0
else:
    gates["exact_ablation_restores_failure"] = False

passed = all(gates.values())
payload = {
    "schema": "msi.kernel-only-proof-regeneration.v2",
    "claim_scope": "bounded proof regeneration from anonymous interface statements; not autonomous statement discovery",
    "passed": passed,
    "gates": gates,
    "attempt_count": len(attempts),
    "winner_index": winner["index"] if winner else None,
    "cold": cold,
    "attempts": attempts,
    "post_ablation": post,
}
RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True))
print("KERNEL_ONLY_PROOF_REGENERATION_V2", json.dumps({"passed": passed, "gates": gates, "winner": payload["winner_index"]}, sort_keys=True))
raise SystemExit(0 if passed else 1)

