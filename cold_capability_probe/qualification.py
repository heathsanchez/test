"""Reproduce pinned WebArena composition claims using the ORIGINAL scorer.

This deliberately reuses archived source-observed inputs. Its output is an
independent native replay, NOT a new prospective source observation or G2/G3.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys


SOURCE = "6473f72db5dcefc97b5725b59e734504edc28a21"
CODE = "e4bf4175331252c2b2d2d192ca80999ee8ba377c9116349ebfbd3bd1de39849c"
ARCHIVES = {
    "e_archive.zip": "2ea6a89d4aae5bfdea4df8d31643c5dc016e294e1b1b694f1c86ea3151d5053c",
    "f_archive.zip": "e3d3dac4c096abbfc6020420e700433e603f769155a0424224b470a9d6829562",
    "composition_archive.zip": "c07211863fb7e8c006ec94bdbb87121fc6096efbe016c0b1aa6823b047ab5d81",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(repo: Path, output: Path) -> dict:
    repo, output = Path(repo).resolve(), Path(output).resolve()
    from webarena_verified.api import WebArenaVerified
    from webarena_verified.types.config import WebArenaVerifiedConfig
    from webarena_verified.types.tracing import NetworkTrace

    for name, expected in ARCHIVES.items():
        assert digest(repo / name) == expected, "archived evidence bytes changed: " + name
    original = repo / "scripts" / "webarena_two_capability_composition_v1.py"
    assert digest(original) == CODE, "original capability source changed"
    assert subprocess.check_output(
        ["git", "-C", str(repo / "official_upstream"), "rev-parse", "HEAD"],
        text=True,
    ).strip() == SOURCE
    sys.path.insert(0, str(repo / "scripts"))
    import webarena_two_capability_composition_v1 as x
    import webarena_compounding_economics_v1 as p

    archive = repo / "historical_composition"
    history = x.read(archive / "result.json")
    assert digest(archive / "observation.json") == history["fresh_observation_sha256"]
    assert digest(archive / "full_no_eval.json") == history["candidate_data_sha256"]
    retained_e, retained_f, receipts = x.verify_sources(archive)
    observation = x.read(archive / "observation.json")
    tasks = p.validate_input(x.read(archive / "full_no_eval.json"), observation)
    official = WebArenaVerified(config=WebArenaVerifiedConfig.from_file(archive / "config.json"))
    empty = NetworkTrace.model_construct(is_playwright=False, src_file=Path("<none>"), events=())

    replay = Counter()
    for response in sorted((archive / "candidate_responses").glob("*/*/*.json")):
        task = int(response.stem.split("_")[0])
        result = official.evaluate_task(task_id=task, agent_response=response, network_trace=empty)
        phase, arm = response.parts[-2], response.parts[-3]
        good = x.passed({"score": float(result.score), "status": result.status.value})
        replay["total"] += 1
        replay[phase] += 1
        replay[phase + ("_pass" if good else "_fail")] += 1
        if phase == "future":
            claim = next(r for r in history["arms"][arm]["future"] if r["task_id"] == task)
            assert (float(result.score), result.status.value) == (claim["score"], claim["status"])
            assert digest(response) == claim["response_sha256"]

    new = output / "new_native_replay"
    new.mkdir(parents=True, exist_ok=True)
    options = x.options(tasks[x.TRAIN], observation, retained_e, retained_f)
    arms = x.candidate(new, official, empty, observation, 12, options)
    selected_detail = x.read(archive / "source_detail.json")
    for arm_name, arm in arms.items():
        winner = arm["winner"]
        native = []
        if winner:
            native.append(x.score(official, empty, new, arm_name, "future", 292,
                                  p.response_for(292, observation, winner["group_key"], winner["status_filter"])))
            if x.select_winners(observation, winner["group_key"], winner["status_filter"]) == [selected_detail["selected_customer"]]:
                native.append(x.score(official, empty, new, arm_name, "future", 290,
                                      {"task_type": "RETRIEVE", "status": "SUCCESS",
                                       "retrieved_data": selected_detail["skus"], "error_details": None}))
        arm["native_future_pass"] = len(native) == 2 and all(x.passed(item) for item in native)

    counts = {name: arm["candidate_evaluations"] for name, arm in arms.items()}
    expected_counts = {name: arm["candidate_evaluations"] for name, arm in history["arms"].items()}
    assert counts == expected_counts, (counts, expected_counts)
    assert all(arm["native_future_pass"] for arm in arms.values())
    assert counts["retain_both"] == counts["strong_stateless"] == 1
    expected_replay = {"total": 27, "train": 17, "future": 10,
                       "train_pass": 5, "train_fail": 12, "future_pass": 10}
    assert replay == expected_replay, (replay, expected_replay)

    report = {
        "schema": "research.known-capability-cold-replay.v0",
        "selected_capability_id": "webarena-e-f-causal-composition",
        "capability_original_commit": "32e2e8f21d642001323237e31fbe7bea01cb975e",
        "capability_original_sha256": CODE,
        "original_native_verifier_commit": SOURCE,
        "archived_artifact_digests": ARCHIVES,
        "original_e_witness": receipts["e"]["freeze_sha256"],
        "archived_native_rescore": dict(replay),
        "recomputed_candidate_evaluations": counts,
        "recomputed_future_successful_arms": sum(a["native_future_pass"] for a in arms.values()),
        "comparative_economics": "TIE_STRONG_STATELESS",
        "replay_boundary": "ARCHIVED_SOURCE_OBSERVATION_NOT_NEW_NATIVE_TASK",
        "typed_transport_admission": "UNKNOWN",
        "source_native_new_observation_G2": "UNKNOWN",
        "lifetime_positive_economics": "UNKNOWN",
    }
    (output / "receipt.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.repo, args.out), indent=2))
