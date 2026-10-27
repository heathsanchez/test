"""Fail-closed audit of the pinned H100 LM-head architecture contract.

The current CUDA kernel is compiled for 16 layers. Its LM-head wait reads
Bar[compiled_layers - 1, downproj_opcode - 1, 0], but Python allocates the
barrier tensor with config.num_hidden_layers. Full synthetic 1/2-layer models
cannot satisfy this contract; a stall is not evidence of an upstream defect.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

SOURCE_PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"
REJECTED = "REJECTED_INVALID_LMHEAD_ARCHITECTURE"
ELIGIBLE = "ELIGIBLE_FULL_MODEL_COMPATIBILITY_UNPROVEN"
PARTIAL = "PARTIAL_PATH_LMHEAD_NOT_EXECUTED"


def audit_sources(llama_cuh, rms_lm_head, scheduler_python):
    layers = re.findall(r"(?m)^#define\s+LLAMA_1B_NUM_LAYERS\s+(\d+)\s*$", llama_cuh)
    if len(layers) != 1:
        raise ValueError("Could not identify exactly one compiled layer macro")
    if "globals::num_layers - 1" not in rms_lm_head:
        raise ValueError("Unrecognized LM-head wait layer index")
    if "OPCODE_DownProjResidual - 1" not in rms_lm_head:
        raise ValueError("Unrecognized LM-head barrier opcode index")
    if "EXPECTED_ARRIVAL_COUNT = 512" not in rms_lm_head:
        raise ValueError("Unrecognized LM-head arrival threshold")
    if "config.num_hidden_layers" not in scheduler_python or "barriers = torch.zeros(" not in scheduler_python:
        raise ValueError("Could not establish Python barrier layer dimension")
    if "if nlayers == globs.num_hidden_layers:" not in scheduler_python:
        raise ValueError("Could not establish when Python schedules LM head")
    return {"compiled_layers": int(layers[0]),
            "lmhead_waits_on_compiled_last_layer": True,
            "runtime_barrier_layers_from_config": True,
            "arrival_threshold": 512}


def classify(facts, fixture_layers, executed_layers):
    n = facts["compiled_layers"]
    if fixture_layers < 1 or executed_layers < 1 or executed_layers > fixture_layers:
        return "REJECTED_UNREGISTERED_LAYER_COUNT"
    if fixture_layers > n:
        return "REJECTED_EXCEEDS_COMPILED_LAYERS"
    if executed_layers < fixture_layers:
        return PARTIAL
    if fixture_layers != n:
        return REJECTED
    return ELIGIBLE


def audit_repo(repo):
    root = Path(repo)
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if head != SOURCE_PIN:
        raise ValueError("Pinned megakernel source commit mismatch")
    facts = audit_sources(
        (root / "demos/low-latency-llama/llama.cuh").read_text(),
        (root / "demos/low-latency-llama/rms_lm_head.cu").read_text(),
        (root / "megakernels/demos/latency/scheduler.py").read_text(),
    )
    return {"source_pin": head, **facts}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--fixture-layers", type=int, required=True)
    p.add_argument("--executed-layers", type=int, required=True)
    p.add_argument("--expect", choices=(REJECTED, ELIGIBLE, PARTIAL, "REJECTED_UNREGISTERED_LAYER_COUNT", "REJECTED_EXCEEDS_COMPILED_LAYERS"))
    a = p.parse_args()
    facts = audit_repo(a.repo)
    verdict = classify(facts, a.fixture_layers, a.executed_layers)
    print(json.dumps({**facts, "fixture_layers": a.fixture_layers,
                      "executed_layers": a.executed_layers, "verdict": verdict}, sort_keys=True))
    if a.expect is not None:
        raise SystemExit(0 if verdict == a.expect else 1)
    raise SystemExit(0 if verdict in (PARTIAL, ELIGIBLE) else 2)


if __name__ == "__main__":
    main()
