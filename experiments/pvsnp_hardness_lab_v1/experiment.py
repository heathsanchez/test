#!/usr/bin/env python3
"""Run the compact, dependency-free evidence slice and emit JSON."""

from __future__ import annotations

import json

from lab import (
    enumerate_nand,
    minimum_exclusion_core,
    parity_subcube_certificate,
    retained_parity_lower_bound,
    singleton_relaxation_cost,
    structural_signature,
    truth_table,
)


def build_evidence() -> dict:
    n3 = enumerate_nand(3, 5)
    n4 = enumerate_nand(4, 4)
    majority3 = truth_table(3, lambda bits: int(sum(bits) >= 2))
    parity4 = truth_table(4, lambda bits: sum(bits) & 1)
    parity_certificate = parity_subcube_certificate(parity4, 4)
    assert parity_certificate is not None

    return {
        "classification": "FINITE_SIGNAL",
        "model": {
            "basis": "fan-in-2 NAND",
            "inputs": "free",
            "constants": "none",
            "fan_out": "free",
            "cost": "DAG gate count",
            "truth_table": "bit r uses x_i=(r>>i)&1",
        },
        "n3_exact": {
            "state_counts": n3.state_counts,
            "new_functions": n3.new_function_counts,
            "cumulative_functions": len(n3.min_size),
        },
        "n4_transfer": {
            "state_counts": n4.state_counts,
            "new_functions": n4.new_function_counts,
            "cumulative_functions": len(n4.min_size),
        },
        "metric_collision": {
            "functions_hex": ["0x8f", "0xea"],
            "sizes": [n3.min_size[0x8F], n3.min_size[0xEA]],
            "shared_12_metric_signature": list(structural_signature(0x8F, 3)),
        },
        "coavailability_residual": {
            "function": "xor(x0,x1)",
            "truth_table_hex": "0x66",
            "xor_costs": [
                singleton_relaxation_cost(0x66, 3, n3.min_size),
                n3.min_size[0x66],
            ],
            "meaning": "singleton costs predict 3; exact joint availability requires 4",
        },
        "global_consistency": {
            "target": "majority3",
            "budget": 3,
            "reachable_functions": sum(size <= 3 for size in n3.min_size.values()),
            "minimum_core_rows": list(
                minimum_exclusion_core(
                    majority3,
                    {mask for mask, size in n3.min_size.items() if size <= 3},
                    8,
                )
                or ()
            ),
        },
        "imported_theorem_transfer": {
            "target": "parity4",
            "budget": 8,
            "certificate_free_variables": list(parity_certificate.free_variables),
            "with_theorem_lower_bound": retained_parity_lower_bound(parity4, 4),
            "without_theorem": retained_parity_lower_bound(parity4, 4, enabled=False),
            "theorem": "Schnorr U2 parity bound composed with restriction closure",
            "causal_scope": "module-toggle sanity check; not acquired-capability ablation",
        },
        "scope": "finite exact evidence plus one classical linear lower-bound theorem; no P!=NP claim",
    }


if __name__ == "__main__":
    print(json.dumps(build_evidence(), indent=2, sort_keys=True))
