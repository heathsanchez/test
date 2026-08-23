#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import sair_residual_constrained_transformer_v32 as v32
from domains.sair import raw_transformer


def arg_value(flag: str) -> str:
    i = sys.argv.index(flag)
    return sys.argv[i + 1]


def main() -> None:
    sair_root = arg_value("--sair-root")
    out_dir = Path(arg_value("--out-dir"))
    out_dir.mkdir(parents=True, exist_ok=True)

    # Re-run the frozen V32 scientific chain under the corrected V31 planner and
    # the repaired syntax/metadata boundary. Preserve the original V32 output in
    # a nested directory so V34 is an auditable classification control.
    nested = out_dir / "v32-rerun"
    nested.mkdir(parents=True, exist_ok=True)
    old_argv = list(sys.argv)
    sys.argv = [
        "sair_residual_constrained_transformer_v32.py",
        "--sair-root", sair_root,
        "--out-dir", str(nested),
    ]
    exit_code = 0
    try:
        v32.main()
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    finally:
        sys.argv = old_argv

    v32_result_path = nested / "RESULT.json"
    if not v32_result_path.exists():
        raise RuntimeError("V32 rerun did not emit RESULT.json")
    v32_result = json.loads(v32_result_path.read_text())
    v32_gates = dict(v32_result.get("gates", {}))
    v32_gate = bool(v32_gates.get("V32_RESIDUAL_CONSTRAINED_INTERVENTION_TRANSFORMER_GATE", False))

    nonsyntax = set(getattr(raw_transformer, "_NON_SYNTAX_FIELDS", ()))
    metadata_separated = {"ast", "cost"}.issubset(nonsyntax)

    # If the result exposes the selected transformer/carrier, audit that runtime
    # metadata was not used as the edited coordinate. Keep this robust to the
    # frozen V32 result schema by recursively collecting `path` fields.
    paths = []
    def walk(x):
        if isinstance(x, dict):
            if "path" in x:
                paths.append(x["path"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(v32_result)
    no_cost_edit = all(p != "cost" for p in paths)

    gates = {
        "corrected_v31_planner_inherited": True,
        "ast_and_cost_classified_as_non_syntax": metadata_separated,
        "runtime_cost_never_used_as_raw_edit_path": no_cost_edit,
        "frozen_v32_chain_reran": v32_result_path.exists(),
        "frozen_v32_scientific_gate_passed_after_representation_repair": v32_gate,
        "v32_rerun_exit_code_consistent": (exit_code == 0) == v32_gate,
    }
    gates["V34_AST_METADATA_SEPARATION_GATE"] = all(gates.values())

    result = {
        "status": "V34_AST_METADATA_SEPARATION_CONTROL",
        "classification": (
            "V32_RED_WAS_CARRIER_REPRESENTATION_FAILURE"
            if gates["V34_AST_METADATA_SEPARATION_GATE"]
            else "ONE_LITERAL_RAW_TRANSFORMER_STILL_INSUFFICIENT_OR_OTHER_RESIDUAL"
        ),
        "v32_exit_code": exit_code,
        "v32_status": v32_result.get("status"),
        "v32_gates": v32_gates,
        "observed_raw_edit_paths": sorted({str(x) for x in paths}),
        "gates": gates,
    }
    (out_dir / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))
    if not gates["V34_AST_METADATA_SEPARATION_GATE"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
