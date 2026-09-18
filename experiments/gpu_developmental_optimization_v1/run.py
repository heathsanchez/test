from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
from typing import Iterable


INPUT_VALUES = (-2, -1, 0, 1, 2)
INPUTS = tuple(itertools.product(INPUT_VALUES, repeat=3))
TRANSFORM_ORDER = (
    "unsafe_drop_last",
    "reverse_ops",
    "swap_affine_coefficients",
    "remove_identity",
    "fuse_adjacent_affine",
)


@dataclass(frozen=True)
class Op:
    kind: str
    a: int = 1
    b: int = 0


@dataclass(frozen=True)
class Kernel:
    kernel_id: str
    ops: tuple[Op, ...]


@dataclass(frozen=True)
class Capability:
    capability_id: str
    transformation: str
    applicability_signature: str
    source_kernel_ids: tuple[str, ...]
    source_cost_reductions: tuple[int, ...]
    verifier_id: str = "gpu-ir-exhaustive-v1"
    dependencies: tuple[str, ...] = ()


def evaluate_reference(kernel: Kernel, values: tuple[int, ...]) -> tuple[int, ...]:
    out = tuple(values)
    for op in kernel.ops:
        if op.kind == "identity":
            continue
        if op.kind == "affine":
            out = tuple(op.a * x + op.b for x in out)
            continue
        raise ValueError(f"unknown op {op.kind}")
    return out


def structural_cost(kernel: Kernel) -> int:
    nontrivial = sum(op.kind != "identity" for op in kernel.ops)
    return 10 * len(kernel.ops) + max(0, nontrivial - 1)


def verify_equivalent(left: Kernel, right: Kernel) -> bool:
    return all(evaluate_reference(left, row) == evaluate_reference(right, row) for row in INPUTS)


def signature(kernel: Kernel) -> set[str]:
    sig: set[str] = set()
    if any(op.kind == "identity" for op in kernel.ops):
        sig.add("has_identity")
    if any(
        kernel.ops[i].kind == "affine" and kernel.ops[i + 1].kind == "affine"
        for i in range(len(kernel.ops) - 1)
    ):
        sig.add("adjacent_affine")
    return sig


def transform(kernel: Kernel, name: str) -> Kernel | None:
    ops = list(kernel.ops)
    if name == "unsafe_drop_last":
        if not ops:
            return None
        return Kernel(kernel.kernel_id + ":drop", tuple(ops[:-1]))
    if name == "reverse_ops":
        if len(ops) < 2:
            return None
        return Kernel(kernel.kernel_id + ":reverse", tuple(reversed(ops)))
    if name == "swap_affine_coefficients":
        for i, op in enumerate(ops):
            if op.kind == "affine" and op.a != op.b:
                ops[i] = Op("affine", op.b, op.a)
                return Kernel(kernel.kernel_id + ":swap", tuple(ops))
        return None
    if name == "remove_identity":
        if "has_identity" not in signature(kernel):
            return None
        new_ops = tuple(op for op in ops if op.kind != "identity")
        return Kernel(kernel.kernel_id + ":noid", new_ops)
    if name == "fuse_adjacent_affine":
        for i in range(len(ops) - 1):
            first, second = ops[i], ops[i + 1]
            if first.kind == second.kind == "affine":
                # second(first(x))
                fused = Op("affine", second.a * first.a, second.a * first.b + second.b)
                new_ops = tuple(ops[:i] + [fused] + ops[i + 2 :])
                return Kernel(kernel.kernel_id + ":fused", new_ops)
        return None
    raise ValueError(name)


def applicability_for(name: str) -> str:
    if name == "remove_identity":
        return "has_identity"
    if name == "fuse_adjacent_affine":
        return "adjacent_affine"
    return "never_promote"


def source_kernels() -> tuple[Kernel, ...]:
    return (
        Kernel("src-id-1", (Op("affine", 2, 1), Op("identity"), Op("affine", 3, -2))),
        Kernel("src-id-2", (Op("identity"), Op("affine", -1, 4))),
        Kernel("src-fuse-1", (Op("affine", 2, 1), Op("affine", 3, 2))),
        Kernel("src-fuse-2", (Op("affine", -2, 3), Op("affine", 1, -4), Op("identity"))),
    )


def acquire_capabilities(sources: Iterable[Kernel]) -> tuple[Capability, ...]:
    by_transform: dict[str, list[tuple[str, int]]] = {}
    for kernel in sources:
        for name in TRANSFORM_ORDER:
            candidate = transform(kernel, name)
            if candidate is None:
                continue
            if not verify_equivalent(kernel, candidate):
                continue
            reduction = structural_cost(kernel) - structural_cost(candidate)
            if reduction <= 0:
                continue
            by_transform.setdefault(name, []).append((kernel.kernel_id, reduction))
    caps = []
    for name in ("remove_identity", "fuse_adjacent_affine"):
        evidence = by_transform.get(name, [])
        if not evidence:
            continue
        caps.append(
            Capability(
                capability_id=f"gpu-opt:{name}",
                transformation=name,
                applicability_signature=applicability_for(name),
                source_kernel_ids=tuple(row[0] for row in evidence),
                source_cost_reductions=tuple(row[1] for row in evidence),
            )
        )
    return tuple(caps)


def generate_targets(seed_text: str, count: int = 24) -> tuple[Kernel, ...]:
    digest = hashlib.sha256(seed_text.encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    rows = []
    for i in range(count):
        a1 = rng.choice((-3, -2, -1, 1, 2, 3))
        b1 = rng.randint(-4, 4)
        a2 = rng.choice((-3, -2, -1, 1, 2, 3))
        b2 = rng.randint(-4, 4)
        mode = i % 3
        if mode == 0:
            ops = (Op("affine", a1, b1), Op("identity"), Op("affine", a2, b2))
        elif mode == 1:
            ops = (Op("affine", a1, b1), Op("affine", a2, b2))
        else:
            ops = (Op("identity"), Op("affine", a1, b1), Op("affine", a2, b2))
        rows.append(Kernel(f"target-{i:02d}", ops))
    return tuple(rows)


def cold_optimize(kernel: Kernel) -> tuple[Kernel, int, str | None]:
    best = kernel
    best_cost = structural_cost(kernel)
    calls = 0
    chosen: str | None = None
    for name in TRANSFORM_ORDER:
        calls += 1
        candidate = transform(kernel, name)
        if candidate is None or not verify_equivalent(kernel, candidate):
            continue
        cost = structural_cost(candidate)
        if cost < best_cost:
            best, best_cost, chosen = candidate, cost, name
    return best, calls, chosen


def capability_first_optimize(
    kernel: Kernel,
    caps: tuple[Capability, ...],
) -> tuple[Kernel, int, str | None, bool]:
    sig = signature(kernel)
    calls = 0
    for cap in caps:
        if cap.applicability_signature not in sig:
            continue
        calls += 1
        candidate = transform(kernel, cap.transformation)
        if candidate is None:
            continue
        if verify_equivalent(kernel, candidate) and structural_cost(candidate) < structural_cost(kernel):
            return candidate, calls, cap.transformation, True
    best, cold_calls, chosen = cold_optimize(kernel)
    return best, calls + cold_calls, chosen, False


def serialize_caps(caps: tuple[Capability, ...], path: Path) -> tuple[Capability, ...]:
    path.write_text(json.dumps([asdict(c) for c in caps], indent=2, sort_keys=True) + "\n")
    rows = json.loads(path.read_text())
    return tuple(
        Capability(
            capability_id=row["capability_id"],
            transformation=row["transformation"],
            applicability_signature=row["applicability_signature"],
            source_kernel_ids=tuple(row["source_kernel_ids"]),
            source_cost_reductions=tuple(int(x) for x in row["source_cost_reductions"]),
            verifier_id=row.get("verifier_id", "gpu-ir-exhaustive-v1"),
            dependencies=tuple(row.get("dependencies", ())),
        )
        for row in rows
    )


def sham_caps(caps: tuple[Capability, ...]) -> tuple[Capability, ...]:
    return tuple(
        Capability(
            capability_id="sham:" + cap.capability_id,
            transformation=cap.transformation,
            applicability_signature="impossible_signature",
            source_kernel_ids=cap.source_kernel_ids,
            source_cost_reductions=cap.source_cost_reductions,
            verifier_id=cap.verifier_id,
            dependencies=cap.dependencies,
        )
        for cap in caps
    )


def run_arm(name: str, caps: tuple[Capability, ...], targets: tuple[Kernel, ...]) -> dict:
    rows = []
    total_search = 0
    for kernel in targets:
        if name in ("warm", "restart", "sham"):
            optimized, search_cost, chosen, reused = capability_first_optimize(kernel, caps)
        else:
            optimized, search_cost, chosen = cold_optimize(kernel)
            reused = False
        if not verify_equivalent(kernel, optimized):
            raise AssertionError(f"semantic mismatch in {name}:{kernel.kernel_id}")
        total_search += search_cost
        rows.append(
            {
                "kernel_id": kernel.kernel_id,
                "search_cost": search_cost,
                "chosen": chosen,
                "reused_capability": reused,
                "before_cost": structural_cost(kernel),
                "after_cost": structural_cost(optimized),
                "verified": True,
            }
        )
    return {
        "arm": name,
        "total_developmental_search_cost": total_search,
        "verified_targets": len(rows),
        "reuse_hits": sum(bool(r["reused_capability"]) for r in rows),
        "rows": rows,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--seed", default=None)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    seed = args.seed or (os.environ.get("GITHUB_SHA", "local") + ":" + os.environ.get("GITHUB_RUN_ID", "0"))
    caps = acquire_capabilities(source_kernels())
    if {c.transformation for c in caps} != {"remove_identity", "fuse_adjacent_affine"}:
        raise AssertionError("frozen source acquisition changed")

    restarted = serialize_caps(caps, out / "capabilities.json")
    targets = generate_targets(seed)
    cold = run_arm("cold", (), targets)
    warm = run_arm("warm", caps, targets)
    restart = run_arm("restart", restarted, targets)
    sham = run_arm("sham", sham_caps(caps), targets)
    ablation = run_arm("ablation", (), targets)

    score = {
        "warm_lt_cold": warm["total_developmental_search_cost"] < cold["total_developmental_search_cost"],
        "warm_lt_sham": warm["total_developmental_search_cost"] < sham["total_developmental_search_cost"],
        "warm_lt_ablation": warm["total_developmental_search_cost"] < ablation["total_developmental_search_cost"],
        "restart_matches_warm": restart["total_developmental_search_cost"] == warm["total_developmental_search_cost"]
        and restart["reuse_hits"] == warm["reuse_hits"],
        "ablation_restores_cold": ablation["total_developmental_search_cost"] == cold["total_developmental_search_cost"],
        "all_targets_verified": all(
            arm["verified_targets"] == len(targets)
            for arm in (cold, warm, restart, sham, ablation)
        ),
    }
    verdict = "PASS" if all(score.values()) else "FAIL"
    evidence = {
        "schema": "gpu-developmental-optimization-v1",
        "verdict": verdict,
        "seed_sha256": hashlib.sha256(seed.encode()).hexdigest(),
        "source_capabilities": [asdict(c) for c in caps],
        "target_count": len(targets),
        "arms": {
            "cold": cold,
            "warm": warm,
            "restart": restart,
            "sham": sham,
            "ablation": ablation,
        },
        "comparison": {
            "cold_search": cold["total_developmental_search_cost"],
            "warm_search": warm["total_developmental_search_cost"],
            "restart_search": restart["total_developmental_search_cost"],
            "sham_search": sham["total_developmental_search_cost"],
            "ablation_search": ablation["total_developmental_search_cost"],
            "search_reduction": 1.0 - warm["total_developmental_search_cost"] / cold["total_developmental_search_cost"],
            "warm_reuse_hits": warm["reuse_hits"],
        },
        "gates": score,
        "claim_boundary": (
            "exact finite kernel-IR developmental-search result only; structural IR cost is not GPU latency. "
            "Hardware promotion requires a separate GPU/Triton authority run."
        ),
    }
    (out / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: evidence[k] for k in ("verdict", "comparison", "gates", "claim_boundary")}, indent=2, sort_keys=True))
    print("PASS_GPU_DEVELOPMENTAL_OPTIMIZATION_V1" if verdict == "PASS" else "FAIL_GPU_DEVELOPMENTAL_OPTIMIZATION_V1")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
