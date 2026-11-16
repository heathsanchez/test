"""C236: paired, unchanged-source Nucleus inference/conversion ancestry replay.

Never promotes a checker judgment. A trace is an observation, not an equality
warrant or a proof that unlogged evaluator/exposure edges are causally absent.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import zipfile

ARCHIVE_SHA = "5bd679fe1f7a6988575ec469264b24cab8ddf465ae064bcb79d99541658acd2f"
FUELED_SHA = "e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a"
FLAG = "NUCLEUS_C236_INFER_ANCESTRY"
ADDITIONAL_FLAGS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)
CONTROLS = (
    "bad/bugs/eta-ctor-alias.ndjson",
    "bad/bugs/rec-rule-proof-irrel.ndjson",
    "bad/bugs/rec-rule-proof-irrel-nested.ndjson",
    "bad/bugs/rec-type-proof-irrel.ndjson",
    "bad/bugs/rec-rule-wrong-arg.ndjson",
    "good/tutorial/119_reduceCtorParamRefl.mk.ndjson",
    "good/tutorial/126_quotMkType.ndjson",
)
TERMINAL = "NUCLEUS_DOWNSTREAM:name=chain6_datF:stage=theorem.value:verdict=UNKNOWN:reason=application-function-type"
ENTER = re.compile(r"^NUCLEUS_C236_ENTER:id=(\\d+):parent=(-|\\d+):expr=(\\d+):frame=(\\d+):ctx=(\\d+):budget=(\\d+)$")
EXIT = re.compile(r"^NUCLEUS_C236_EXIT:id=(\\d+):status=(PROVEN|REFUTED|UNKNOWN):reason=([^:]+):left=(\\d+)$")
CONVERSION = re.compile(r"^NUCLEUS_C236_CONVERSION:parent=(\\d+):expr=(\\d+):frame=(\\d+):ctx=(\\d+):left=(\\d+):status=(PROVEN|REFUTED|UNKNOWN):reason=([^:]+):actual=(.*):expected=(.*)$")

def parse_trace(log: str) -> dict:
    if "NUCLEUS_C236_TRUNCATED" in log or "NUCLEUS_C236_SCOPE_INCOMPLETE" in log:
        raise ValueError("Incomplete C236 log")
    nodes, active, conversions = {}, [], []
    roots, maximum = 0, 0
    for line in log.splitlines():
        if line.startswith("NUCLEUS_C236_ENTER:"):
            m = ENTER.fullmatch(line)
            if not m:
                raise ValueError("Malformed C236 entry: " + line[:180])
            ident, parent, expr, frame, ctx, budget = m.groups()
            ident = int(ident)
            parent = None if parent == "-" else int(parent)
            if parent != (active[-1] if active else None) or ident in nodes:
                raise ValueError("Missing or mismatched C236 parent")
            if parent is None:
                if (int(expr), int(frame), int(ctx)) != (7199, 0, 0):
                    raise ValueError("Unexpected trace root")
                roots += 1
            nodes[ident] = {"id": ident, "parent": parent,
                            "expr": int(expr), "frame": int(frame),
                            "ctx": int(ctx), "starting_budget": int(budget)}
            active.append(ident)
            maximum = max(maximum, len(active))
        elif line.startswith("NUCLEUS_C236_EXIT:"):
            m = EXIT.fullmatch(line)
            if not m:
                raise ValueError("Malformed C236 exit: " + line[:180])
            ident, status, reason, left = m.groups()
            ident = int(ident)
            if not active or active[-1] != ident:
                raise ValueError("C236 unbalanced inference stack")
            active.pop()
            nodes[ident].update(status=status, reason=reason, ending_budget=int(left))
        elif line.startswith("NUCLEUS_C236_CONVERSION:"):
            m = CONVERSION.fullmatch(line)
            if not m:
                raise ValueError("Malformed C236 conversion: " + line[:180])
            parent, expr, frame, ctx, left, status, reason, actual, expected = m.groups()
            parent = int(parent)
            if not active or active[-1] != parent:
                raise ValueError("C236 conversion parent not active")
            conversions.append({"parent": parent, "expr": int(expr), "frame": int(frame),
                                "ctx": int(ctx), "remaining": int(left),
                                "status": status, "reason": reason,
                                "actual_prefix": actual, "expected_prefix": expected})
    if active or not roots or any("status" not in node for node in nodes.values()):
        raise ValueError("Incomplete inference ancestry")
    def ancestry(ident):
        chain = []
        while ident is not None:
            n = nodes[ident]
            chain.append({"call": ident, "expr": n["expr"], "frame": n["frame"],
                          "ctx": n["ctx"], "result": n["status"], "reason": n["reason"]})
            ident = n["parent"]
        return list(reversed(chain))
    targeted = [row for row in conversions if row["expr"] in (12, 4861)]
    for row in targeted:
        row["ancestry"] = ancestry(row["parent"])
    # Only this Rust function's inference-call edges are complete. Formation,
    # exposure, evaluator and all context/level equality edges are not traced.
    return {
        "status": "WARRANTED_BOUNDED_INFER_CALL_ANCESTRY",
        "roots": roots, "infer_calls": len(nodes), "max_depth": maximum,
        "unknown_infer_calls": sum(n["status"] == "UNKNOWN" for n in nodes.values()),
        "conversion_events": len(conversions),
        "unknown_conversion_events": sum(c["status"] == "UNKNOWN" for c in conversions),
        "target_owner_conversions": targeted[-20:],
        "target_owner_events_total": len(targeted),
        "missing_non_inference_edges": "UNKNOWN",
    }

def unit_tests():
    log = "\\n".join([
        "NUCLEUS_C236_ENTER:id=0:parent=-:expr=7199:frame=0:ctx=0:budget=65536",
        "NUCLEUS_C236_ENTER:id=1:parent=0:expr=12:frame=7:ctx=4:budget=100",
        "NUCLEUS_C236_EXIT:id=1:status=PROVEN:reason=shared-expression-inference:left=90",
        "NUCLEUS_C236_CONVERSION:parent=0:expr=12:frame=7:ctx=4:left=80:status=UNKNOWN:reason=conversion-budget-exhausted:actual=x:expected=y",
        "NUCLEUS_C236_EXIT:id=0:status=UNKNOWN:reason=application-function-type:left=0",
    ])
    out = parse_trace(log)
    assert out["infer_calls"] == 2 and out["target_owner_events_total"] == 1
    assert out["target_owner_conversions"][0]["ancestry"][0]["expr"] == 7199
    for broken in (log.replace("parent=0:expr=12", "parent=4:expr=12"),
                   log.replace("NUCLEUS_C236_EXIT:id=1:", "NUCLEUS_C236_EXIT:id=3:"),
                   log + "\\nNUCLEUS_C236_TRUNCATED:maximum=100000"):
        try:
            parse_trace(broken)
        except ValueError:
            continue
        raise AssertionError("Malformed/incomplete trace must fail closed")

def run(checker: Path, source: bytes, environment: dict, directory: Path,
        label: str, timeout: int = 180):
    start = time.monotonic()
    process = subprocess.run([str(checker)], input=source, env=environment,
                             capture_output=True, timeout=timeout, check=False)
    stderr = process.stderr.decode(errors="replace")
    (directory / (label + ".stderr")).write_text(stderr)
    return {
        "case": label, "exit": process.returncode,
        "time_s": round(time.monotonic() - start, 3),
        "terminal_count": stderr.splitlines().count(TERMINAL),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "stderr_file": label + ".stderr",
        "trace": parse_trace(stderr) if FLAG in environment else None,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", required=True, type=Path)
    p.add_argument("--checker", required=True, type=Path)
    p.add_argument("--flags", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    unit_tests()
    args.out.mkdir(parents=True, exist_ok=True)
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError("Source artifact SHA mismatch")
    flags = json.loads(args.flags.read_text())["flags"]
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("Historical checker flags changed")
    baseline_env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    baseline_env.update(flags)
    baseline_env.update({f"NUCLEUS_EXPERIMENTAL_{k}": "1" for k in ADDITIONAL_FLAGS})
    baseline_env["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"] = "1"
    baseline_env["NUCLEUS_C223_FIRST_OWNER"] = "1"
    baseline_env["NUCLEUS_TRACE_DOWNSTREAM"] = "1"
    with zipfile.ZipFile(args.archive) as archive:
        current = {row["case"]: row for row in json.loads(archive.read("current212.json"))}
        if len(current) != 212:
            raise ValueError("Unexpected source corpus")
        def source(case):
            content = archive.read("inputs/" + case)
            if hashlib.sha256(content).hexdigest() != current[case]["sha256"]:
                raise ValueError("Changed original source: " + case)
            return content
        fueled = source("good/perf/fueled-chain.ndjson")
        if hashlib.sha256(fueled).hexdigest() != FUELED_SHA:
            raise ValueError("Wrong original fueled-chain")
        original = []
        for allowance in (65536, 65600):
            for traced in (False, True):
                environment = baseline_env.copy()
                if allowance != 65536:
                    environment["NUCLEUS_C225_JUDGMENT_STEPS"] = str(allowance)
                if traced:
                    environment[FLAG] = "1"
                label = f"fueled_outer{allowance}_trace{int(traced)}"
                row = run(args.checker, fueled, environment, args.out, label)
                if row["exit"] != 2 or row["terminal_count"] != 1:
                    raise ValueError("Original source/terminal verdict changed: " + str(row))
                if traced and row["trace"]["infer_calls"] == 0:
                    raise ValueError("Observer missed source root")
                row.update(allowance=allowance, traced=traced)
                original.append(row)
                print("C236_ORIGINAL", json.dumps(row, sort_keys=True), flush=True)
        controls = []
        for case in CONTROLS:
            content = source(case)
            for traced in (False, True):
                environment = baseline_env.copy()
                if traced:
                    environment[FLAG] = "1"
                row = run(args.checker, content, environment, args.out,
                          "control_" + case.replace("/", "_").removesuffix(".ndjson")
                          + f"_trace{int(traced)}", timeout=60)
                if row["exit"] != current[case]["expected"] or row["exit"] not in (0, 1):
                    raise ValueError("Protected verdict mismatch: " + str(row))
                row.update(source_case=case, traced=traced)
                controls.append(row)
        if len(original) != 4 or len(controls) != 14:
            raise ValueError("Incomplete paired cohort")
    report = {
        "status": "WARRANTED_BOUNDED_IF_WORKFLOW_GREEN",
        "original_unmodified": True, "source_archive_sha256": ARCHIVE_SHA,
        "fueled_source_sha256": FUELED_SHA,
        "no_semantic_change": True,
        "whole_original_acceptance": "UNKNOWN",
        "original": original, "controls": controls,
        "next": "Locate the first source-authorized missing inference/conversion premise on a complete active ancestor path, then validate independently against the original Lean judgment.",
    }
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\\n")
    print("C236_SUMMARY", json.dumps({
        "original_exits": [x["exit"] for x in original],
        "control_exits": [x["exit"] for x in controls],
        "trace_owners": {str(x["allowance"]): x["trace"]["target_owner_events_total"]
                         for x in original if x["traced"]},
    }, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
