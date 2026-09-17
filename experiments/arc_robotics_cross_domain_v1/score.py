from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
EXPECTED_ARMS = ("COLD", "WARM", "SHAM", "ABLATION", "RESTART")


def score_results(rows: list[dict]) -> dict:
    by_arm = {row["arm"]: row for row in rows}
    missing = [arm for arm in EXPECTED_ARMS if arm not in by_arm]
    if missing:
        raise ValueError(f"missing arms: {missing}")

    summary = {}
    for arm in EXPECTED_ARMS:
        row = by_arm[arm]
        summary[arm] = {
            "n_worlds": row["n_worlds"],
            "correct": row["correct"],
            "unknown": row["unknown"],
            "calibration_interventions": row["calibration_interventions"],
            "operator_evaluations": row["operator_evaluations"],
            "developmental_cost": row["developmental_cost"],
            "execution_probes": row["execution_probes"],
            "transferred_rejected": bool(row["transferred_rejected"]),
        }

    all_exact = all(
        item["correct"] == item["n_worlds"] and item["unknown"] == 0
        for item in summary.values()
    )
    warm = summary["WARM"]
    cold = summary["COLD"]
    sham = summary["SHAM"]
    ablation = summary["ABLATION"]
    restart = summary["RESTART"]

    criteria = {
        "all_arms_exact": all_exact,
        "warm_lt_cold": warm["developmental_cost"] < cold["developmental_cost"],
        "warm_lt_sham": warm["developmental_cost"] < sham["developmental_cost"],
        "warm_lt_ablation": warm["developmental_cost"] < ablation["developmental_cost"],
        "restart_equals_warm": restart["developmental_cost"] == warm["developmental_cost"],
        "ablation_equals_cold": ablation["developmental_cost"] == cold["developmental_cost"],
        "warm_two_calibrations": warm["calibration_interventions"] == 2,
        "restart_two_calibrations": restart["calibration_interventions"] == 2,
        "cold_eight_calibrations": cold["calibration_interventions"] == 8,
        "sham_eight_calibrations": sham["calibration_interventions"] == 8,
        "ablation_eight_calibrations": ablation["calibration_interventions"] == 8,
        "sham_rejected": sham["transferred_rejected"],
    }
    criteria["primary_pass"] = all(criteria.values())

    return {"summary": summary, "primary": criteria}


def main() -> None:
    rows = json.loads((ROOT / "answers.json").read_text())
    scored = score_results(rows)
    (ROOT / "scores.json").write_text(json.dumps(scored, indent=2, sort_keys=True) + "\n")
    print(json.dumps(scored, indent=2, sort_keys=True), flush=True)
    if not scored["primary"]["primary_pass"]:
        raise SystemExit(1)
    print("ARC_ROBOTICS_CROSS_DOMAIN_V1_SCORE_PASS", flush=True)


if __name__ == "__main__":
    main()
