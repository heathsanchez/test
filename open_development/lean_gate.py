"""Exact finite refinement certificates checked by the Lean kernel.

The declared finite model is the semantic authority. This gate proves the
candidate's strict refinement and admission relative to that model; it does
not certify the model's origin or the optimality of the Python search policy.
"""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any, Mapping

from .runtime import canonical, digest


ROOT = Path(__file__).resolve().parent / "lean"


def certificate_source(tables: Mapping[str, tuple[Any, ...]], old: tuple[str, ...],
                       candidate: str) -> str:
    names = tuple(sorted(tables))
    if not names or candidate not in tables:
        raise ValueError("unknown candidate")
    n = len(tables[candidate])
    if n == 0 or any(len(tables[name]) != n for name in names):
        raise ValueError("incomplete finite table")
    if any(name not in tables for name in old):
        raise ValueError("unknown retained observation")
    # Canonical equality classes preserve all observational equalities.
    values = sorted({canonical(value) for row in tables.values() for value in row})
    codes = {value: i for i, value in enumerate(values)}
    rows = [[codes[canonical(value)] for value in tables[name]] for name in names]

    def row_expr(row):
        expr = "0"
        for i in range(n - 1, -1, -1):
            expr = f"if x.val == {i} then {row[i]} else ({expr})"
        return expr

    table_expr = "0"
    for i in range(len(names) - 1, -1, -1):
        table_expr = f"if c.val == {i} then ({row_expr(rows[i])}) else ({table_expr})"
    k = len(names)
    indices = tuple(names.index(name) for name in old)
    c = names.index(candidate)
    witness = next(((x, y) for x in range(n) for y in range(x + 1, n)
                    if all(rows[i][x] == rows[i][y] for i in indices)
                    and rows[c][x] != rows[c][y]), None)
    if witness is None:
        raise ValueError("candidate does not strictly refine the retained interface")
    x, y = witness

    def list_expr(items):
        return "[" + ", ".join(f"({i} : Fin {k})" for i in items) + "]"

    def old_proof(items, indent="  "):
        if not items:
            return indent + f"exact EquivalentOn.nil observation ({x} : Fin {n}) ({y} : Fin {n})"
        head, *tail = items
        rest = list_expr(tail)
        return (indent + f"apply (EquivalentOn.cons observation ({head} : Fin {k}) {rest} ({x} : Fin {n}) ({y} : Fin {n})).2\n"
                + indent + "constructor\n" + indent + "· decide\n"
                + indent + "·\n" + old_proof(tail, indent + "  "))

    return f'''import Core

namespace FiniteCertificate
open OpenDevelopment

-- Every number below is generated from the frozen input table.
def observation (x : Fin {n}) (c : Fin {k}) : Nat :=
  {table_expr}

def initial : State (Fin {k}) :=
  {{ observations := {list_expr(indices)} }}

theorem old_same :
    Interface observation initial ({x} : Fin {n}) ({y} : Fin {n}) := by
  change EquivalentOn observation {list_expr(indices)} ({x} : Fin {n}) ({y} : Fin {n})
{old_proof(list(indices))}

theorem new_diff :
    ¬ Interface observation (apply initial (.observe ({c} : Fin {k})))
      ({x} : Fin {n}) ({y} : Fin {n}) := by
  intro h
  have heq := ((observe_meet observation initial ({c} : Fin {k}) ({x} : Fin {n}) ({y} : Fin {n})).mp h).1
  exact (by decide : observation ({x} : Fin {n}) ({c} : Fin {k}) ≠ observation ({y} : Fin {n}) ({c} : Fin {k})) heq

def valid : Repair (Fin {k}) → Prop
  | .observe c => c = ({c} : Fin {k}) ∧
      Interface observation initial ({x} : Fin {n}) ({y} : Fin {n}) ∧
      ¬ Interface observation (apply initial (.observe c)) ({x} : Fin {n}) ({y} : Fin {n})
  | _ => False

def check : Repair (Fin {k}) → Bool
  | .observe c => decide (c = ({c} : Fin {k}))
  | _ => false

def authority : Authority (Fin {k}) where
  valid := valid
  check := check
  sound := by
    intro r h
    cases r with
    | observe c =>
        have hc : c = ({c} : Fin {k}) := of_decide_eq_true (by simpa [check] using h)
        subst c
        exact ⟨rfl, old_same, new_diff⟩
    | acquire c => simp [check] at h
    | revisePolicy p => simp [check] at h

def checked : CheckedRepair (Fin {k}) valid :=
  ⟨.observe {c}, authority.sound _ (by decide)⟩

theorem candidate_refines :
    ∃ x y : Fin {n},
      Interface observation initial x y ∧
      ¬ Interface observation (applyChecked initial checked) x y := by
  exact ⟨{x}, {y}, old_same, new_diff⟩

theorem candidate_admitted :
    develop authority initial (.observe {c}) =
      some (apply initial (.observe {c})) := by
  decide

end FiniteCertificate
'''


class LeanGate:
    def __init__(self, lean: str = "lean", timeout: int = 30, root: Path = ROOT):
        self.lean = lean
        self.timeout = timeout
        self.root = Path(root).resolve()
        self._version: str | None = None
        self.last_error: str | None = None

    def _run(self, args: list[str], **kwargs):
        env = os.environ.copy()
        env["LEAN_PATH"] = str(self.root) + os.pathsep + env.get("LEAN_PATH", "")
        return subprocess.run(args, cwd=self.root, env=env, capture_output=True,
                              text=True, timeout=self.timeout, **kwargs)

    def prepare(self) -> None:
        if shutil.which(self.lean) is None:
            raise RuntimeError("Lean is not installed")
        version = self._run([self.lean, "--version"])
        if version.returncode != 0:
            raise RuntimeError("Lean version check failed")
        self._version = version.stdout.strip()
        expected = (self.root / "lean-toolchain").read_text().strip().split(":v")[-1]
        if expected not in self._version:
            raise RuntimeError(f"Lean version mismatch: expected {expected}, got {self._version}")
        # Rebuild from pinned sources once per gate instance, not merely
        # because an .olean happens to exist.
        if not getattr(self, "_prepared", False):
            result = subprocess.run(["bash", str(self.root / "check.sh")], cwd=self.root,
                                    capture_output=True, text=True, timeout=max(self.timeout, 120))
            if result.returncode != 0:
                raise RuntimeError("Lean core build failed: " + result.stderr[-2000:])
            self._prepared = True

    @property
    def verifier_id(self) -> str:
        if self._version is None:
            self.prepare()
        sources = {name: sha256((self.root / name).read_bytes()).hexdigest()
                   for name in ("Kernel.lean", "Completeness.lean", "Core.lean")}
        sources["lean_gate.py"] = sha256(Path(__file__).read_bytes()).hexdigest()
        return "lean-refinement-v1:" + digest({"version": self._version, "sources": sources})

    def verify(self, tables: Mapping[str, tuple[Any, ...]], old: tuple[str, ...],
               candidate: str) -> dict[str, Any] | None:
        self.prepare()
        self.last_error = None
        try:
            source = certificate_source(tables, old, candidate)
        except ValueError as exc:
            self.last_error = str(exc)
            return None
        with tempfile.TemporaryDirectory(prefix="open-development-") as tmp:
            path = Path(tmp) / "Candidate.lean"
            path.write_text(source)
            result = self._run([self.lean, str(path)])
        if result.returncode != 0:
            self.last_error = (result.stdout + "\n" + result.stderr).strip()
            return None
        return {"source": source, "source_sha256": sha256(source.encode()).hexdigest(),
                "verifier": self.verifier_id, "lean_version": self._version,
                "theorems": ["candidate_refines", "candidate_admitted"]}
