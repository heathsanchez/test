"""Bounded, evidence-preserving asynchronous client for pinned H100 differential.

RUNPOD_API_KEY stays in GitHub Actions. No upstream writes.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import time

ENDPOINT_NAME = "mathgraph-megakernel-h100-20261027"
SOURCE_PIN = "7309cec801537b61fea3b50d7dfe454a6cde578e"
MAX_WAIT_SECONDS = 1200


def select_endpoint(endpoints, expected=ENDPOINT_NAME):
    matches = [e for e in endpoints if isinstance(e, dict) and e.get("name") == expected]
    if len(matches) != 1 or not isinstance(matches[0].get("id"), str) or not matches[0]["id"]:
        raise ValueError("expected exactly one named endpoint with a nonempty id")
    return matches[0]["id"]


def save_state(out, state):
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n")


async def resolve_endpoint(app_name, env_name):
    """Resolve the deployed resource from RunPod cloud state, not Flash cache."""
    from runpod_flash.core.resources.app import FlashApp
    from runpod_flash.core.api.runpod import RunpodGraphQLClient

    app = await FlashApp.from_name(app_name)
    environment = await app.get_environment_by_name(env_name)
    if not isinstance(environment, dict) or not environment.get("id"):
        raise ValueError("missing Flash environment identity")
    async with RunpodGraphQLClient() as client:
        details = await client.get_flash_environment({"flashEnvironmentId": environment["id"]})
    return select_endpoint((details or {}).get("endpoints") or [])


async def run_async(client, gate_source, out, wait_seconds=MAX_WAIT_SECONDS):
    """Submit exactly once and persist job ID before polling; cancel on timeout."""
    if not 1 <= wait_seconds <= MAX_WAIT_SECONDS:
        raise ValueError("unbounded wait disallowed")
    state = {"schema": "mathgraph-h100-async-v1", "status": "UNKNOWN_NOT_SUBMITTED",
             "source_pin": SOURCE_PIN, "transport": "runpod-async", "job_id": None}
    save_state(out, state)
    job = None
    started = time.monotonic()
    try:
        job = await client.run({"gate_source": gate_source})
        if not isinstance(job.id, str) or not job.id:
            raise ValueError("missing RunPod job ID")
        state["job_id"] = job.id
        state["status"] = "UNKNOWN_JOB_SUBMITTED"
        save_state(out, state)
        await job.wait(timeout=wait_seconds)
        runpod_status = getattr(job, "_data", {}).get("status")
        state["runpod_status"] = runpod_status
        if runpod_status != "COMPLETED":
            state["status"] = "UNKNOWN_REMOTE_JOB_NOT_COMPLETED"
            state["runpod_error_present"] = bool(job.error)
        elif not isinstance(job.output, dict):
            state["status"] = "UNKNOWN_MISSING_STRUCTURED_OUTPUT"
        else:
            state["worker"] = job.output
            state["status"] = job.output.get("status", "UNKNOWN_WORKER_NO_VERDICT")
    except (asyncio.TimeoutError, TimeoutError):
        state["status"] = "UNKNOWN_RUNPOD_JOB_TIMEOUT"
        if job is not None and state["job_id"]:
            try:
                await asyncio.wait_for(job.cancel(), timeout=15)
                state["cancel_requested"] = True
            except Exception:
                state["cancel_requested"] = False
    except Exception as exc:
        state["status"] = "UNKNOWN_RUNPOD_TRANSPORT_ERROR"
        state["exception_type"] = type(exc).__name__
    finally:
        state["wall_seconds"] = round(time.monotonic() - started, 3)
        save_state(out, state)
    return state


def host_accept(state):
    worker = state.get("worker") or {}
    return bool(state.get("status") == "PASS"
                and state.get("runpod_status") == "COMPLETED"
                and worker.get("source_pin") == SOURCE_PIN
                and worker.get("sm_count") == 132
                and all(isinstance(worker.get("checks", {}).get(s), dict)
                        and worker["checks"][s].get("passed") is True
                        for s in ("rr", "dag")))


async def main_async(args):
    if not os.getenv("RUNPOD_API_KEY", "").strip():
        raise RuntimeError("RUNPOD_API_KEY not set")
    initial = {"schema": "mathgraph-h100-async-v1", "status": "UNKNOWN_ENDPOINT_DISCOVERY",
               "source_pin": SOURCE_PIN, "job_id": None}
    save_state(args.out, initial)
    try:
        endpoint_id = await resolve_endpoint(os.environ["FLASH_APP"], os.environ["FLASH_ENV"])
    except Exception as exc:
        initial["exception_type"] = type(exc).__name__
        save_state(args.out, initial)
        return 1
    from runpod_flash import Endpoint
    state = await run_async(Endpoint(id=endpoint_id), args.gate.read_text(), args.out)
    state["gate_passed"] = host_accept(state)
    save_state(args.out, state)
    print(json.dumps({"status": state["status"], "gate_passed": state["gate_passed"],
                      "job_id": state.get("job_id")}, sort_keys=True))
    return 0 if state["gate_passed"] else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
