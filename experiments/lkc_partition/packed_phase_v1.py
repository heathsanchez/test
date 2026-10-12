#!/usr/bin/env python3
"""Lean Kernel Challenge Partition phase-change experiment V1.

Screen-only implementations: NO impl_correct proof and NO official submission.
Two exact generating-function algorithms are tested against independent integer
partition DP, then evaluated by the pinned Lean kernel benchmark.

Formula (n>=0), B=2^(n+3), S=n(n+1)/2:
p(n) = floor(B^(S+n) / prod_(k=1)^n (B^k-1)) mod B.

Derivation: B^S/A = product_(k=1)^n (1-B^(-k))^(-1).
The integer part of B^n times that formal series contains p_n(0)..p_n(n)
as base-B digits. Coefficients satisfy p_n(j)<=2^(j-1) (j>=1);
tail < 2^n/(B-2) < 1. For j<=n all digits are <B.
This argument is a mathematical hypothesis for formalization, not Lean proof.
"""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

HEAD = """import Spec

namespace Submission

/-
EXPERIMENT ONLY. A universal Lean proof has NOT been constructed here.
Do not submit these files or claim SAIR acceptance.
-/
"""

DIVISION = r"""
/-- Product evaluated at B: A = prod_(k=1)^n (B^k-1). -/
def denominator (w : Nat) : Nat → Nat
  | 0 => 1
  | k + 1 =>
      denominator w k * (((1 : Nat) <<< (w * (k + 1))) - 1)

/--
A single integer quotient extracts the coefficient of x^n from
prod_(k=1)^n (1-x^k)^(-1), using a no-carry base B = 2^(n+3).
This is a candidate computation, not a formal proof.
-/
def packedDivision (n : Nat) : Nat :=
  let w := n + 3
  let degreeSum := n * (n + 1) / 2
  let numerator := (1 : Nat) <<< (w * (degreeSum + n))
  let denom := denominator w n
  let digitMask := ((1 : Nat) <<< w) - 1
  (numerator / denom) &&& digitMask

def impl : Nat → Nat := packedDivision

end Submission
"""

GEOMETRIC = r"""
/-- Truncated product of coefficient-packed geometric series. -/
def geometricProduct (n w : Nat) : Nat → Nat
  | 0 => 1
  | k + 1 =>
      let step := k + 1
      let count := n / step + 1
      let first := ((1 : Nat) <<< (w * (step * count))) - 1
      let second := ((1 : Nat) <<< (w * step)) - 1
      let geometric := first / second
      let trimMask := ((1 : Nat) <<< (w * (n + 1))) - 1
      (geometricProduct n w k * geometric) &&& trimMask

def packedGeometric (n : Nat) : Nat :=
  let w := n + 2
  let acc := geometricProduct n w n
  let digitMask := ((1 : Nat) <<< w) - 1
  (acc >>> (w * n)) &&& digitMask

def impl : Nat → Nat := packedGeometric

end Submission
"""


def reference_partition(n: int) -> int:
    row = [0] * (n + 1)
    row[0] = 1
    for k in range(1, n + 1):
        for j in range(k, n + 1):
            row[j] += row[j-k]
    return row[n]


def quotient_partition(n: int, width: int | None = None) -> int:
    w = n + 3 if width is None else width
    b = 1 << w
    tri = n * (n + 1) // 2
    denom = 1
    for k in range(1, n + 1):
        denom *= (1 << (w*k)) - 1
    return ((1 << (w*(tri+n))) // denom) & (b-1)


def geometric_partition(n: int) -> int:
    w = n+2
    mask = (1 << (w*(n+1))) - 1
    acc = 1
    for k in range(1, n+1):
        count = n//k+1
        geometric = ((1 << (w*k*count))-1)//((1 << (w*k))-1)
        acc = (acc*geometric) & mask
    return (acc >> (w*n)) & ((1 << w)-1)


def self_test() -> dict:
    mismatches = []
    results = {}
    for n in range(0, 81):
        expected = reference_partition(n)
        got_div = quotient_partition(n)
        got_geom = geometric_partition(n)
        if (expected, expected) != (got_div, got_geom):
            mismatches.append({"n":n,"expected":expected,"division":got_div,"geometric":got_geom})
        if n in [0,1,2,14,22,32,36,50,80]:
            results[str(n)] = {"value":expected,"division":got_div,"geometric":got_geom}
    negative = quotient_partition(1, width=1)
    assert negative != reference_partition(1), "Negative control did not detect base-width error"
    assert not mismatches, json.dumps(mismatches)
    result = {"status":"PASS_FINITE_CANDIDATE","domain":"n=0..80","checks":81,
              "arms":["independent_row_dp","single_integer_quotient","truncated_geometric_product"],
              "negative_too_narrow_base":{"n":1,"reference":1,"wrong_base":negative},
              "samples":results,
              "epistemic_boundary":"No universal Lean proof; no official evaluation."}
    return result


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    tests=self_test()
    variants={"packed_division":"Submission_packed_division_probe.lean",
              "packed_geometric":"Submission_packed_geometric_probe.lean"}
    for name,source in [("packed_division",HEAD+DIVISION),("packed_geometric",HEAD+GEOMETRIC)]:
        path=OUT/variants[name]
        path.write_text(source)
        print(f"GENERATED {name} {path} bytes={len(source.encode())} sha256={hashlib.sha256(source.encode()).hexdigest()}")
    OUT.joinpath("packed_phase_v1_finite_results.json").write_text(json.dumps(tests,indent=2)+"\n")
    print(json.dumps(tests,indent=2))


if __name__ == "__main__":
    main()
