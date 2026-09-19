from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
from pathlib import Path

from runpod_flash import Endpoint, GpuType


@Endpoint(
    name="qckn-gpu-hardware-v1",
    gpu=GpuType.NVIDIA_GEFORCE_RTX_4090,
    dependencies=["torch", "triton"],
)
async def run_hardware_benchmark():
    import torch
    import triton
    import triton.language as tl

    if not torch.cuda.is_available():
        return {
            "status": "GPU_UNAVAILABLE_REMOTE",
            "cuda_available": False,
        }

    @triton.jit
    def affine_kernel(
        x_ptr,
        y_ptr,
        n_elements: tl.constexpr,
        a: tl.constexpr,
        b: tl.constexpr,
        BLOCK: tl.constexpr,
    ):
        offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
        mask = offsets < n_elements
        x = tl.load(x_ptr + offsets, mask=mask, other=0)
        y = a * x + b
        tl.store(y_ptr + offsets, y, mask=mask)

    @triton.jit
    def fused_affine_kernel(
        x_ptr,
        y_ptr,
        n_elements: tl.constexpr,
        a1: tl.constexpr,
        b1: tl.constexpr,
        a2: tl.constexpr,
        b2: tl.constexpr,
        BLOCK: tl.constexpr,
    ):
        offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
        mask = offsets < n_elements
        x = tl.load(x_ptr + offsets, mask=mask, other=0)
        y = a2 * (a1 * x + b1) + b2
        tl.store(y_ptr + offsets, y, mask=mask)

    @triton.jit
    def identity_kernel(
        x_ptr,
        y_ptr,
        n_elements: tl.constexpr,
        BLOCK: tl.constexpr,
    ):
        offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
        mask = offsets < n_elements
        x = tl.load(x_ptr + offsets, mask=mask, other=0)
        tl.store(y_ptr + offsets, x, mask=mask)

    def elapsed_ms(fn):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        fn()
        end.record()
        end.synchronize()
        return float(start.elapsed_time(end))

    def median_ms(fn, *, warmup=12, repeats=60):
        for _ in range(warmup):
            fn()
        torch.cuda.synchronize()
        rows = [elapsed_ms(fn) for _ in range(repeats)]
        return statistics.median(rows), rows

    torch.manual_seed(0)
    n = 1 << 22
    block = 256
    grid = (triton.cdiv(n, block),)

    x = ((torch.arange(n, device="cuda", dtype=torch.int32) % 201) - 100).contiguous()
    tmp = torch.empty_like(x)
    base_two = torch.empty_like(x)
    fused = torch.empty_like(x)
    base_identity = torch.empty_like(x)
    no_identity = torch.empty_like(x)

    a1, b1, a2, b2 = 2, 3, -1, 5

    def two_pass():
        affine_kernel[grid](x, tmp, n, a1, b1, BLOCK=block)
        affine_kernel[grid](tmp, base_two, n, a2, b2, BLOCK=block)

    def fused_pass():
        fused_affine_kernel[grid](
            x, fused, n, a1, b1, a2, b2, BLOCK=block
        )

    def with_identity():
        affine_kernel[grid](x, tmp, n, a1, b1, BLOCK=block)
        identity_kernel[grid](tmp, base_identity, n, BLOCK=block)

    def without_identity():
        affine_kernel[grid](x, no_identity, n, a1, b1, BLOCK=block)

    # Force compilation before correctness/timing.
    two_pass()
    fused_pass()
    with_identity()
    without_identity()
    torch.cuda.synchronize()

    fused_correct = bool(torch.equal(base_two, fused))
    identity_correct = bool(torch.equal(base_identity, no_identity))

    two_ms, two_samples = median_ms(two_pass)
    fused_ms, fused_samples = median_ms(fused_pass)
    identity_ms, identity_samples = median_ms(with_identity)
    no_identity_ms, no_identity_samples = median_ms(without_identity)

    fused_speedup = two_ms / fused_ms
    identity_speedup = identity_ms / no_identity_ms

    props = torch.cuda.get_device_properties(0)
    return {
        "status": "COMPLETED",
        "cuda_available": True,
        "gpu_name": torch.cuda.get_device_name(0),
        "compute_capability": [
            int(props.major),
            int(props.minor),
        ],
        "torch_version": str(torch.__version__),
        "triton_version": str(triton.__version__),
        "n_elements": n,
        "dtype": "int32",
        "coefficients": {
            "a1": a1,
            "b1": b1,
            "a2": a2,
            "b2": b2,
        },
        "correctness": {
            "fused_matches_two_pass": fused_correct,
            "identity_removed_matches_identity_path": identity_correct,
        },
        "timing_ms_median": {
            "two_pass_affine": two_ms,
            "fused_affine": fused_ms,
            "affine_plus_identity": identity_ms,
            "affine_without_identity": no_identity_ms,
        },
        "speedup": {
            "fuse_adjacent_affine": fused_speedup,
            "remove_identity": identity_speedup,
        },
        "sample_counts": {
            "warmup": 12,
            "repeats": 60,
        },
        "sample_summary": {
            "two_pass_min_ms": min(two_samples),
            "two_pass_max_ms": max(two_samples),
            "fused_min_ms": min(fused_samples),
            "fused_max_ms": max(fused_samples),
            "identity_min_ms": min(identity_samples),
            "identity_max_ms": max(identity_samples),
            "no_identity_min_ms": min(no_identity_samples),
            "no_identity_max_ms": max(no_identity_samples),
        },
        "claim_boundary": (
            "Measured Runpod GPU/Triton evidence for two exact retained transformation "
            "shapes only. It is not a universal GPU optimization claim."
        ),
    }


async def _main_async(out: Path) -> int:
    result = await run_hardware_benchmark()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))

    if result.get("status") != "COMPLETED":
        return 2
    correctness = result["correctness"]
    if not all(correctness.values()):
        return 3

    speedup = result["speedup"]
    # Require a meaningful margin over timer noise on both retained transforms.
    if float(speedup["fuse_adjacent_affine"]) <= 1.05:
        return 4
    if float(speedup["remove_identity"]) <= 1.05:
        return 5
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if not os.environ.get("RUNPOD_API_KEY", "").strip():
        raise SystemExit("RUNPOD_API_KEY is required")
    return asyncio.run(_main_async(Path(args.out)))


if __name__ == "__main__":
    raise SystemExit(main())
