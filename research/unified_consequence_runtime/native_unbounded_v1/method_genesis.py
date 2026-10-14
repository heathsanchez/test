#!/usr/bin/env python3
"""Native-source method search for parametric (infinite-state) CSLib transitions.

The previously complete finite-active constructor parser is tried first and
must decline these native sources.  The only supplied meta-construction
substrate is a small explicit program grammar: arbitrary Nat stride 1..3,
UP/DOWN orientation, source-typed Lean proof atoms, and two independently
kernel-checked parametric induction laws.  The chosen full scripts and source
orientations are NOT supplied.  Every candidate is tested by the *original*
CSLib Lean checker.  This is not autonomous invention of the meta-grammar.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path


def canonical(x):
    return json.dumps(x, indent=2, sort_keys=True) + "\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(repo), *arguments], text=True).strip()


def verify_sources(repo, protocol):
    if git(repo, "rev-parse", "HEAD") != protocol["upstream"]["sha"]:
        raise ValueError("UPSTREAM_CHECKOUT_MISMATCH")
    for spec in protocol["source_sets"]:
        if git(repo, "hash-object", spec["file"]) != spec["blob_sha"]:
            raise ValueError("SOURCE_GIT_BLOB_MISMATCH:" + spec["file"])
        if spec["source_symbol"] not in (repo / spec["file"]).read_text():
            raise ValueError("SOURCE_SYMBOL_NOT_PRESENT:" + spec["source_symbol"])


# Same parametric proof term, byte-for-byte, irrespective of native source
# term, transition grammar or arbitrary natural-number starting state.
UNBOUNDED_METHOD = """import Cslib.Foundations.Semantics.LTS.ExampleTermination
import CslibTests.LTS

namespace SourceInducedInfinite
open Cslib Cslib.LTS

theorem forward {Label : Type} (sys : LTS Nat Label) (label : Label)
    (delta : Nat) (step : ∀ n, sys.Tr n label (n + delta))
    (n k : Nat) :
    sys.MTr n (List.replicate k label) (n + k * delta) := by
  induction k generalizing n with
  | zero =>
      simpa using (MTr.refl : sys.MTr n [] n)
  | succ k ih =>
      have chain := MTr.stepL (step n) (ih (n + delta))
      simpa [List.replicate_succ, Nat.succ_mul, Nat.add_assoc,
        Nat.add_comm, Nat.add_left_comm] using chain

theorem backward {Label : Type} (sys : LTS Nat Label) (label : Label)
    (delta : Nat) (step : ∀ n, sys.Tr (n + delta) label n)
    (n k : Nat) :
    sys.MTr (n + k * delta) (List.replicate k label) n := by
  induction k with
  | zero =>
      simpa using (MTr.refl : sys.MTr n [] n)
  | succ k ih =>
      have chain := MTr.stepL (step (n + k * delta)) ih
      simpa [List.replicate_succ, Nat.succ_mul, Nat.add_assoc,
        Nat.add_comm, Nat.add_left_comm] using chain

end SourceInducedInfinite
"""


def old_method_residual(protocol, cslib, old_source):
    old = runpy.run_path(str(old_source))
    residuals = []
    for row in protocol["source_sets"]:
        source = (cslib / row["file"]).read_text()
        try:
            edges = old["extract_edges"](source, {
                "transition": row["source_symbol"], "source_label": "Nat"})
        except ValueError as exc:
            residuals.append({
                "file": row["file"],
                "symbol": row["source_symbol"],
                "kind": "UNKNOWN_PREVIOUS_FINITE_GRAMMAR",
                "diagnostic": str(exc),
                "not_an_global_impossibility_proof": True,
            })
        else:
            raise AssertionError(
                "OLD_METHOD_WAS_NOT_AN_OBSTRUCTION:" + str(edges))
    return residuals


def native_script(spec, direction, delta, atom):
    sysname, label = spec["system"], spec["label"]
    if direction == "UP":
        start, dest = "n", f"(n + {delta})"
        repeated_start, repeated_end = "n", f"(n + k * {delta})"
        method = "forward"
    elif direction == "DOWN":
        start, dest = f"(n + {delta})", "n"
        repeated_start, repeated_end = f"(n + k * {delta})", "n"
        method = "backward"
    else:
        raise AssertionError(direction)
    goal = f"({sysname}).Tr {start} {label} {dest}"
    definition = f"""theorem generated_step (n : Nat) : {goal} := by
  {atom.replace('SYSTEM', sysname)}
"""
    repetition = f"""theorem generated_unbounded (n k : Nat) :
    ({sysname}).MTr {repeated_start} (List.replicate k {label}) {repeated_end} := by
  exact SourceInducedInfinite.{method} {sysname} {label} {delta} generated_step n k

"""
    return UNBOUNDED_METHOD + f"""\nnamespace GeneratedSourceMethod
{definition}
{repetition}
end GeneratedSourceMethod
"""


def lean_check(cslib, path, timeout):
    try:
        p = subprocess.run(["lake", "env", "lean", str(path)],
                           cwd=cslib, capture_output=True, text=True,
                           timeout=timeout, check=False)
        return p.returncode == 0, p.returncode, (p.stdout+p.stderr)[-3500:]
    except subprocess.TimeoutExpired:
        return False, 124, "NATIVE_LEAN_CHECK_TIMED_OUT"


def run_all(cslib, protocol, old_source, output, timeout):
    verify_sources(cslib, protocol)
    output.mkdir(parents=True, exist_ok=True)
    residuals = old_method_residual(protocol, cslib, old_source)
    (output / "source-method-compiled.lean").write_text(UNBOUNDED_METHOD)
    generic_ok, generic_rc, generic_diag = lean_check(
        cslib, output / "source-method-compiled.lean", timeout)
    if not generic_ok:
        raise RuntimeError("GENERIC_PARAMETRIC_INDUCTION_NOT_VERIFIED\n" + generic_diag)
    meta = protocol["constructor_substrate"]
    allowed_atoms = tuple(meta["proof_atoms"])
    costs = []
    accepted = []
    method_acquired = None
    checked_candidates = 0
    for source in protocol["source_sets"]:
        if source["stage"] == "HELDOUT" and method_acquired is None:
            raise AssertionError("NO_PRIOR_METHOD_TO_REUSE")
        trials = []
        wins = []
        # Compare the acquired method FIRST. If it does not fit a source,
        # the generator tries other combinations in the declared algebra.
        directions = tuple(meta["step_directions"])
        deltas = tuple(meta["step_delta_candidates"])
        ordered = [(direction,delta) for direction in directions for delta in deltas]
        if method_acquired is not None:
            plan = (method_acquired["direction"], method_acquired["delta"])
            ordered = [plan] + [option for option in ordered if option != plan]
        for direction, delta in ordered:
            if wins:
                break
            for atom in allowed_atoms:
                chosen = native_script(source, direction, delta, atom)
                candidate = output / "candidate.lean"
                candidate.write_text(chosen)
                ok, ret, diag = lean_check(cslib, candidate, timeout)
                checked_candidates += 1
                trial = {"direction":direction,"delta":delta,"atom":atom,
                         "native_exit":ret,"accepted":ok,
                         "diagnostic_digest":sha(diag.encode()),
                         "diagnostic_tail":diag[-250:]}
                trials.append(trial)
                if ok:
                    proofname = (source["stage"].lower() + ".lean")
                    proof = output / proofname
                    proof.write_text(chosen)
                    wins.append({
                        "stage":source["stage"],"file":source["file"],
                        "source_blob_sha":source["blob_sha"],"system":source["system"],
                        "source_symbol":source["source_symbol"],
                        "direction":direction,"delta":delta,"proof_atom":atom,
                        "unbounded_for_all_n_and_k":True,
                        "native_proof_file":proofname,
                        "native_proof_sha256":sha(proof.read_bytes()),
                        "method_sha256":sha(UNBOUNDED_METHOD.encode()),
                        "native_lean":"PASS"
                    })
                    break
            if checked_candidates > meta["budget_max_native_search_trials"]:
                raise ValueError("SOURCE_METHOD_SEARCH_BUDGET_EXCEEDED")
        costs.append({"stage":source["stage"],"attempts":len(trials),
                      "trials":trials})
        if not wins:
            raise ValueError("UNKNOWN_NO_SOURCE_NATIVE_METHOD_FOR:" + source["system"])
        accepted.extend(wins)
        if source["stage"] == "ACQUIRE":
            method_acquired = {
                "direction":wins[0]["direction"],"delta":wins[0]["delta"],
                "proof_atom":wins[0]["proof_atom"]
            }
        if source["stage"] == "HELDOUT":
            if (wins[0]["direction"], wins[0]["delta"]) != (
                    method_acquired["direction"], method_acquired["delta"]):
                raise AssertionError("SOURCE_DISTINCT_METHOD_TRANSFER_DID_NOT_REUSE")
        if source["stage"] == "GENERATOR_REVISION":
            if wins[0]["direction"] == method_acquired["direction"]:
                raise AssertionError("ORIENTATION_RESIDUAL_WAS_NOT_SEPARATED")
    (output / "candidate.lean").unlink(missing_ok=True)
    # Build negative: deliberately opposite orientation for infinite
    # countdown source, no proof language adjustment may make it true.
    inverted = next(s for s in protocol["source_sets"]
                    if s["stage"] == "GENERATOR_REVISION")
    bad = native_script(inverted, "UP", 1, "simp [SYSTEM]")
    (output / "negative-opposite-direction.lean").write_text(bad)
    negative_ok, negative_rc, negative_diag = lean_check(
        cslib, output / "negative-opposite-direction.lean", timeout)
    if negative_ok:
        raise AssertionError("FALSE_UNBOUNDED_DIRECTION_WAS_NATIVE_ACCEPTED")
    report = {
        "schema":"metalogic.native-unbounded-method-genesis-result.v1",
        "upstream_commit":protocol["upstream"]["sha"],
        "source_protocol_sha256":sha(canonical(protocol).encode()),
        "method_sha256":sha(UNBOUNDED_METHOD.encode()),
        "old_method_residuals":residuals,
        "native_generic_induction":"PASS",
        "native_source_methods":accepted,
        "native_feedback_history":costs,
        "total_native_calls":checked_candidates + 2,
        "acquisition_native_calls":costs[0]["attempts"] + 1,
        "heldout_native_calls":costs[1]["attempts"],
        "revision_native_calls":costs[2]["attempts"],
        "negative_direction_check":"REJECTED_NATIVE",
        "negative_direction_exit":negative_rc,
        "negative_direction_diagnostic_sha256":sha(negative_diag.encode()),
        "full_unbounded_Nat_state_and_k":"PASS_FOR_THREE_SOURCE_GRAMMARS",
        "allowed_method_language_human_defined":True,
        "generated_method_unrestricted":"UNKNOWN",
        "native_new_open_theorem":"NOT_CLAIMED",
        "claimed_lifetime_advantage":"NOT_ESTABLISHED",
        "equal_information_stateless_method_search":"ALSO_AVAILABLE",
        "scientific_e2e_system":"UNKNOWN",
        "science_l7":"UNKNOWN",
        "basis":"unchanged native CSLib definitions, exact source bytes, kernel checked candidate induction and source one-step methods",
    }
    (output / "report.json").write_text(canonical(report))
    print("SOURCE_NATIVE_INFINITE_METHODS_CHECKED=" + str(len(accepted)))
    print("SOURCE_METHOD_NATIVE_CALLS=" + str(checked_candidates + 2))
    for entry in accepted:
        print("SOURCE_RESULT=" + canonical({
            "stage":entry["stage"],"direction":entry["direction"],
            "delta":entry["delta"],"proof_atom":entry["proof_atom"],
            "source":entry["file"],"sha":entry["native_proof_sha256"]
        }).strip())
    print("GENERATOR_SELF_INVENTION=UNKNOWN")
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cslib", type=Path, required=True)
    p.add_argument("--previous-source-method", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--timeout", type=int, default=30)
    args=p.parse_args()
    protocol=json.loads(args.protocol.read_bytes())
    if protocol.get("schema")!="metalogic.native-unbounded-method-genesis.v1":
        raise ValueError("UNSUPPORTED_NATIVE_METHOD_PROTOCOL")
    run_all(args.cslib.resolve(), protocol, args.previous_source_method.resolve(),
            args.out.resolve(), args.timeout)


if __name__ == "__main__":
    main()
