from __future__ import annotations

import json
from pathlib import Path

from .core import majority3_code, operator_orbit, parity3_code

ROOT = Path(__file__).parent
EXPECTED_ARMS = ("COLD", "WARM", "SHAM", "ABLATION", "RESTART")


def validate_results(rows: list[dict], metadata: dict) -> None:
    assert metadata["schema"] == "arc.robotics.cross_domain.v1"
    assert metadata["llm_used"] is False
    assert int(metadata["n_worlds"]) > 0
    provenance = metadata["seed_provenance"]
    assert "github_sha" in provenance and "github_run_id" in provenance

    by_arm = {row["arm"]: row for row in rows}
    assert set(by_arm) == set(EXPECTED_ARMS)

    n_worlds = int(metadata["n_worlds"])
    seed = int(metadata["seed"])
    source_code = int(metadata.get("source_code", parity3_code()))
    assert source_code == parity3_code()

    first = by_arm["COLD"]
    target_code = first["target_code"]
    target_adapter = first["target_adapter"]
    truths = first["truths"]

    for arm in EXPECTED_ARMS:
        row = by_arm[arm]
        assert row["seed"] == seed
        assert row["n_worlds"] == n_worlds
        assert row["source_code"] == source_code
        assert row["target_code"] == target_code
        assert row["target_adapter"] == target_adapter
        assert row["truths"] == truths
        assert row["predictions"] == truths
        assert row["correct"] == n_worlds
        assert row["unknown"] == 0
        assert row["execution_probes"] == 3 * n_worlds

    assert target_code in set(operator_orbit(source_code))
    assert by_arm["COLD"]["retained_code"] is None
    assert by_arm["ABLATION"]["retained_code"] is None
    assert by_arm["WARM"]["retained_code"] == source_code
    assert by_arm["RESTART"]["retained_code"] == source_code
    assert by_arm["SHAM"]["retained_code"] == majority3_code()
    assert by_arm["SHAM"]["transferred_rejected"] is True

    assert by_arm["WARM"]["calibration_trace"] == by_arm["COLD"]["calibration_trace"][:2]
    assert by_arm["RESTART"]["calibration_trace"] == by_arm["WARM"]["calibration_trace"]
    assert by_arm["ABLATION"]["calibration_trace"] == by_arm["COLD"]["calibration_trace"]
    assert by_arm["SHAM"]["calibration_trace"] == by_arm["COLD"]["calibration_trace"]

    assert by_arm["ABLATION"]["developmental_cost"] == by_arm["COLD"]["developmental_cost"]
    assert by_arm["RESTART"]["developmental_cost"] == by_arm["WARM"]["developmental_cost"]


def main() -> None:
    rows = json.loads((ROOT / "answers.json").read_text())
    metadata = json.loads((ROOT / "run_metadata.json").read_text())
    validate_results(rows, metadata)
    print("ARC_ROBOTICS_CROSS_DOMAIN_V1_VALIDATION_PASS", flush=True)


if __name__ == "__main__":
    main()
