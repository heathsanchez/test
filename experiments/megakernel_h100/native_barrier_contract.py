"""CPU-only compatibility check for pinned public H100 megakernel.

Checks the architecture-dependent LM-head barrier index, without claiming
anything about actual GPU execution or modifying public upstream source.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

SOURCE_PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"


def audit_native_barriers(repo: Path, model_layers: int, executed_layers: int) -> dict:
    root = Path(repo)
    head = (root / "demos/low-latency-llama/llama.cuh").read_text()
    lmhead = (root / "demos/low-latency-llama/rms_lm_head.cu").read_text()
    scheduler = (root / "megakernels/demos/latency/scheduler.py").read_text()

    macro = re.search(r"^\s*#define\s+LLAMA_1B_NUM_LAYERS\s+(\d+)\s*$", head, re.M)
    native_type = re.search(r"typedef\s+globals_t<\s*LLAMA_1B_NUM_LAYERS\s*,", head)
    wait = re.search(
        r"g\.Bar\[\{\s*globals::num_layers\s*-\s*1\s*,\s*"
        r"OPCODE_DownProjResidual\s*-\s*1\s*,\s*0\s*\}\]", lmhead
    )
    python_barrier = (
        "config.num_hidden_layers" in scheduler
        and re.search(r"barriers\s*=\s*torch\.zeros\s*\(", scheduler) is not None
    )
    if not (macro and native_type and wait and python_barrier):
        return {"status": "UNKNOWN_SOURCE_CONTRACT", "eligible": False,
                "reason": "fixed-depth barrier indexing contract not independently recognized",
                "source_pin": SOURCE_PIN}
    if model_layers < 1 or executed_layers < 1 or executed_layers > model_layers:
        return {"status": "BLOCKED_INVALID_MODEL_SCOPE", "eligible": False,
                "source_pin": SOURCE_PIN}

    compiled_layers = int(macro.group(1))
    lm_head_active = executed_layers == model_layers
    barrier_index = compiled_layers - 1
    entry = {
        "schema": "mathgraph-native-barrier-compatibility-v1",
        "source_pin": SOURCE_PIN,
        "model_layers": model_layers,
        "executed_layers": executed_layers,
        "compiled_layers": compiled_layers,
        "python_barrier_layer_capacity": model_layers,
        "lm_head_active": lm_head_active,
        "lm_head_wait_barrier_layer_index": barrier_index,
        "barrier_index_in_bounds": barrier_index < model_layers,
        "eligible": False,
    }
    if not lm_head_active:
        entry["status"] = "PARTIAL_NO_LMHEAD_SCOPE"
        entry["eligible"] = True
        entry["reason"] = "fixed last-layer wait is not on the scheduled path"
    elif barrier_index >= model_layers:
        entry["status"] = "BLOCKED_NATIVE_BARRIER_OUT_OF_BOUNDS"
        entry["reason"] = "compiled LM-head waiter indexes beyond Python barrier layer capacity"
    elif model_layers != compiled_layers:
        entry["status"] = "UNKNOWN_NATIVE_DEPTH_CONTRACT"
        entry["reason"] = "model depth differs from compiled template; no full-model admission"
    else:
        entry["status"] = "ELIGIBLE_FULL_DEPTH_UNVERIFIED"
        entry["eligible"] = True
        entry["reason"] = "depth indices match; no claim about device execution correctness"
    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--model-layers", type=int, required=True)
    parser.add_argument("--executed-layers", type=int, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit_native_barriers(args.repo, args.model_layers, args.executed_layers)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["eligible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
