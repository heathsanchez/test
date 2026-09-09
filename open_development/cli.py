"""JSON input/output interface for the finite, model-relative implementation."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .finite import FiniteAdapter
from .lean_gate import LeanGate
from .runtime import Developer, EvidenceStore, Obligation, canonical, digest


def main() -> None:
    parser = argparse.ArgumentParser(description="Verified open development")
    parser.add_argument("--state", type=Path, default=Path(".open-development/state.sqlite"))
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--spec", type=Path, required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--world")
    run.add_argument("--mode", choices=("execute", "plan"), default="execute")
    run.add_argument("--budget", type=int, default=4)
    run.add_argument("--finite-only", action="store_true", help="Use the declared finite-model checker without Lean certification")
    status = sub.add_parser("status")
    revoke = sub.add_parser("revoke")
    revoke.add_argument("id")
    revoke.add_argument("--reason", required=True)
    args = parser.parse_args()
    store = EvidenceStore(args.state)
    try:
        if args.command == "run":
            spec = json.loads(args.spec.read_text())
            target = {"task": args.task, "mode": args.mode}
            if args.world is not None:
                target["actual_world"] = args.world
            gate = None if args.finite_only else LeanGate()
            result = Developer(store, FiniteAdapter(spec, gate)).run(
                Obligation("finite", target, args.budget))
            output = asdict(result)
        elif args.command == "revoke":
            output = {"revoked": store.revoke(args.id, args.reason)}
        else:
            output = {}
        state = store.state()
        output["active"] = [{"id": rid, "kind": rec["repair"]["kind"],
                             "name": rec["repair"]["name"]}
                            for rid, rec in state["capabilities"].items()]
        output["state_id"] = digest(state)
        print(canonical(output))
    finally:
        store.close()


if __name__ == "__main__":
    main()
