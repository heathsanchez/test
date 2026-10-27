"""MathGraph's fail-closed, source-pinned H100 megakernel experiment.

CPU-only commands: --self-test, --verify-checkout.
GPU commands (in an H100 SXM environment): --make-fixture, --diff.
The GPU path does not require gated Hugging Face downloads.
"""

import argparse
import json
import math
import os
from pathlib import Path
import runpy
import subprocess
import sys


PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"
FIELDS = ("hidden_states", "k_cache", "v_cache", "logits")
ATOL = 0.05
RTOL = 0.10


def validate_manifest(commit):
    return commit == PIN


def evaluate_summary(metrics):
    """Result contract independent of torch and of the device evaluator."""
    reasons = []
    for name in FIELDS:
        m = metrics.get(name)
        if m is None:
            reasons.append(f"missing:{name}")
            continue
        if not isinstance(m.get("elements"), int) or m["elements"] < 1:
            reasons.append(f"empty:{name}")
        if m.get("nonfinite") != 0:
            reasons.append(f"nonfinite:{name}")
        if m.get("violations") != 0:
            reasons.append(f"mismatch:{name}")
        d = m.get("max_abs_diff")
        if not isinstance(d, (int, float)) or not math.isfinite(d) or d < 0:
            reasons.append(f"invalid_difference:{name}")
    return {"passed": not reasons, "reasons": reasons}


def verify_checkout(repo):
    root = Path(repo)
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if not validate_manifest(commit):
        raise RuntimeError(f"Wrong source revision: {commit}; expected {PIN}")
    status = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"], text=True
    ).strip()
    if status:
        raise RuntimeError("Upstream tracked files are modified; source pin is not pristine")
    return {"source_commit": commit, "tracked_worktree_clean": True}


def make_fixture(folder):
    """Write deterministic, architecture-matched *synthetic* Llama-shaped weights.

    One layer exercises QKV, attention, MLP and LM head while keeping RAM/disk
    manageable. The upstream C++ demo is specialized for Llama 3.2 1B dims;
    matching dimensions does NOT establish full-16-layer model correctness.
    """
    import torch
    from safetensors.torch import save_file
    from transformers import LlamaConfig

    out = Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    config = LlamaConfig(
        vocab_size=128256, hidden_size=2048, intermediate_size=8192,
        num_hidden_layers=1, num_attention_heads=32,
        num_key_value_heads=8, head_dim=64,
        max_position_embeddings=2048, rms_norm_eps=1e-5,
        rope_theta=500000.0, tie_word_embeddings=True,
        torch_dtype="bfloat16",
    )
    config.save_pretrained(out)
    g = torch.Generator(device="cpu").manual_seed(20261027)
    shapes = {
        "model.embed_tokens.weight": (128256, 2048),
        "model.norm.weight": (2048,),
        "model.layers.0.input_layernorm.weight": (2048,),
        "model.layers.0.post_attention_layernorm.weight": (2048,),
        "model.layers.0.self_attn.q_proj.weight": (2048, 2048),
        "model.layers.0.self_attn.k_proj.weight": (512, 2048),
        "model.layers.0.self_attn.v_proj.weight": (512, 2048),
        "model.layers.0.self_attn.o_proj.weight": (2048, 2048),
        "model.layers.0.mlp.gate_proj.weight": (8192, 2048),
        "model.layers.0.mlp.up_proj.weight": (8192, 2048),
        "model.layers.0.mlp.down_proj.weight": (2048, 8192),
    }
    weights = {}
    for name, shape in shapes.items():
        if "norm.weight" in name:
            value = torch.ones(shape, dtype=torch.bfloat16)
        else:
            value = torch.randn(shape, generator=g, dtype=torch.float32).mul_(0.015).to(torch.bfloat16)
        weights[name] = value.contiguous()
    save_file(weights, str(out / "model.safetensors"), metadata={"origin": "mathgraph_synthetic_not_pretrained"})
    print(json.dumps({"fixture": str(out), "tensors": len(weights),
                      "model": "one-layer synthetic 1B-shaped Llama", "seed": 20261027}))


def run_diff(repo, fixture, sched, out):
    import torch

    repo = Path(repo).resolve()
    manifest = verify_checkout(repo)
    fixture = Path(fixture).resolve()
    if not (fixture / "config.json").is_file() or not (fixture / "model.safetensors").is_file():
        raise RuntimeError("Missing local synthetic fixture (no Hugging Face fallback permitted)")
    if not torch.cuda.is_available():
        raise RuntimeError("No CUDA GPU available")
    prop = torch.cuda.get_device_properties(0)
    if prop.name.lower().find("h100") < 0 or prop.multi_processor_count != 132:
        raise RuntimeError(f"Expected H100 SXM 132 SM; found {prop.name} ({prop.multi_processor_count} SM)")
    if sched not in ("rr", "dag"):
        raise ValueError("Unregistered scheduler")

    # Unlike upstream BaseGlobals.diff(), this comparator fails the process
    # when outputs disagree or are nonfinite, and writes machine-readable data.
    sys.path.insert(0, str(repo))
    from megakernels.instructions import BaseGlobals
    import megakernels.dispatch as dispatch

    original = BaseGlobals.diff
    original_make_pyvm = dispatch.make_pyvm_interpreter
    pyvm_completed = [0]
    captured = []

    def traced_pyvm_factory(*args, **kwargs):
        inner = original_make_pyvm(*args, **kwargs)

        class TracedReference:
            def interpret(self, *a, **kw):
                result = inner.interpret(*a, **kw)
                pyvm_completed[0] += 1
                return result

        return TracedReference()

    def gated_diff(self, other, skip_kv_cache=False):
        if pyvm_completed[0] < 1:
            raise AssertionError("Python reference never completed; refusing comparison")
        original(self, other, skip_kv_cache=skip_kv_cache)
        records = {}
        for name in FIELDS:
            a = getattr(self, name).detach().float()
            b = getattr(other, name).detach().float()
            if a.shape != b.shape:
                records[name] = {"elements": 0, "nonfinite": 1,
                                 "violations": 1, "max_abs_diff": None}
                continue
            finite = torch.isfinite(a) & torch.isfinite(b)
            delta = (a - b).abs()
            allowed = ATOL + RTOL * a.abs()
            violations = ((delta > allowed) & finite).sum().item()
            records[name] = {
                "elements": a.numel(),
                "nonfinite": (~finite).sum().item(),
                "violations": int(violations),
                "max_abs_diff": float(delta[finite].max().item()) if finite.any() else None,
            }
        verdict = evaluate_summary(records)
        record = {**manifest, "scheduler": sched, "model_kind": "synthetic_1_layer",
                  "tolerances": {"atol": ATOL, "rtol": RTOL},
                  "pyvm_completed_calls": pyvm_completed[0],
                  "fields": records, **verdict}
        captured.append(record)
        Path(out).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print("MATHGRAPH_GPU_GATE " + json.dumps(record, sort_keys=True), flush=True)
        if not verdict["passed"]:
            raise AssertionError("Independent GPU tensor gate rejected: " + ",".join(verdict["reasons"]))

    BaseGlobals.diff = gated_diff
    dispatch.make_pyvm_interpreter = traced_pyvm_factory
    # Do not pass skip_pyvm=false: the pinned parser may treat presence
    # of a boolean option as enabled. Upstream defaults skip_pyvm to False.
    # The reference interpreter must run before any comparison can be warranted.
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(repo / "megakernels/scripts/diff_test.py"),
                    f"model={fixture}", f"sched={sched}", "layer_limit=1",
                    "prompt_len=10", "ntok=10", "exec_reps=1",
                    "setting=latency", "device=cuda:0"]
        os.chdir(repo)
        runpy.run_path(sys.argv[0], run_name="__main__")
    finally:
        sys.argv = old_argv
        BaseGlobals.diff = original
        dispatch.make_pyvm_interpreter = original_make_pyvm
    if len(captured) != 1:
        raise RuntimeError(f"Expected one comparison; received {len(captured)}")


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--self-test", action="store_true")
    action.add_argument("--verify-checkout", action="store_true")
    action.add_argument("--make-fixture", action="store_true")
    action.add_argument("--diff", choices=("rr", "dag"))
    parser.add_argument("--repo", default="megakernels_upstream")
    parser.add_argument("--fixture", default="synthetic_llama_1b_shape")
    parser.add_argument("--out", default="gpu_diff.json")
    args = parser.parse_args()
    if args.self_test:
        import unittest
        class Smoke(unittest.TestCase):
            def test_good(self):
                self.assertTrue(evaluate_summary({k: {"elements": 1, "nonfinite": 0,
                    "violations": 0, "max_abs_diff": 0.0} for k in FIELDS})["passed"])
            def test_bad(self):
                self.assertFalse(evaluate_summary({})["passed"])
        result = unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Smoke))
        if not result.wasSuccessful():
            raise SystemExit(1)
    elif args.verify_checkout:
        print(json.dumps(verify_checkout(args.repo)))
    elif args.make_fixture:
        make_fixture(args.fixture)
    else:
        run_diff(args.repo, args.fixture, args.diff, args.out)


if __name__ == "__main__":
    main()
