#!/usr/bin/env python3
"""Source-only original V104/MSI training catalog. NO native candidates or G2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

from research.unified_consequence_runtime import typed_v104_msi_bridge_v7 as bridge

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = "research/unified_consequence_runtime/G2_TRAINING_METHOD_V104_PROTOCOL_V1.json"
PRE_FREEZE_COMMIT = "36f3f82ebe840eaeac049020844fb3ba54639a4a"


def git(repo, *cmd):
    return subprocess.check_output(["git", "-C", str(repo), *cmd],
                                   stderr=subprocess.PIPE).decode().strip()


def exact_protocol():
    actual = (ROOT / PROTOCOL).read_bytes()
    source = subprocess.check_output(["git", "-C", str(ROOT), "show",
                                      PRE_FREEZE_COMMIT + ":" + PROTOCOL])
    if actual != source:
        raise ValueError("CURRENT_POLICY_DIFFERS_FROM_PRECOMMITTED_V104_METHOD_PROTOCOL")
    d = json.loads(source)
    if d["original_methods"]["constructor_git"] != (
            "heathsanchez/triskelion@426c54f7c774560e0fabe7213c5ef333b1327c71"
    ) or d["original_methods"]["msi_git"] != (
            "heathsanchez/Minimal-Sufficient-Interface@56cfd7b523e3592cae4eafa5468f437ccb94dbe9"):
        raise ValueError("ORIGINAL_CONSTRUCTOR_OR_MSI_PIN_CHANGED")
    return d


def main(repo, triskelion, msi, dest):
    start = time.monotonic()
    dest.mkdir(parents=True, exist_ok=False)
    result = {"schema": "UDM_ORIGINAL_V104_MSI_SOURCE_CATALOG_PRE_NATIVE_V1",
              "status": "UNKNOWN_SOURCE_ONLY",
              "training_method_source": "ORIGINAL_PINNED_V104_AND_MSI_V10",
              "head_author_repaired_production": "NOT_READ",
              "future_executing_source": "UNOPENED",
              "native_calls": 0, "collection_calls": 0,
              "G2": "UNKNOWN", "G3": "UNKNOWN", "G4": "UNKNOWN",
              "G5": "UNKNOWN", "G6": "UNKNOWN"}
    try:
        p = exact_protocol()
        task = p["training"]
        if git(repo, "rev-parse", "HEAD") != task["base"]:
            raise ValueError("WRONG_TRAINING_BASE")
        if git(repo, "rev-parse", "HEAD^{tree}") != (
                "c6465ce4b900e2f21aa73ebbe16c779f5c6ae9bf"):
            raise ValueError("WRONG_TRAINING_GIT_TREE")
        if git(repo, "status", "--porcelain"):
            raise ValueError("DIRTY_SOURCE_PRE_CATALOG")
        if git(triskelion, "rev-parse", "HEAD") != (
                "426c54f7c774560e0fabe7213c5ef333b1327c71"):
            raise ValueError("WRONG_TRISKELION_SOURCE")
        if git(msi, "rev-parse", "HEAD") != (
                "56cfd7b523e3592cae4eafa5468f437ccb94dbe9"):
            raise ValueError("WRONG_MSI_SOURCE")
        catalog = bridge.catalog_v104_typed(
            repo, task["base"], task["production_paths"],
            triskelion, msi, cap=64, observation={}
        )
        if catalog["source"]["v104_language"] != "ORIGINAL_PINNED_V104" or (
                catalog["source"]["msi_policy"] != "ORIGINAL_PINNED_MSI_V10"
        ):
            raise ValueError("ORIGINAL_METHOD_SUBSTITUTED")
        rows = catalog["rows"]
        orders = catalog["orders"]
        ids = [x["id"] for x in rows]
        if not ids or len(ids) > 64 or len(ids) != len(set(ids)):
            raise ValueError("ORIGINAL_CATALOG_DUPLICATE_OR_INVALID_COUNT")
        if len(orders) != 37 or any(set(v) != set(ids) or len(v) != len(ids)
                                   for v in orders.values()):
            raise ValueError("INCOMPLETE_ORIGINAL_MSI_POLICY_ORDER")
        if "COLD_V104_ORDER" not in orders:
            raise ValueError("COLD_POLICY_ABSENT")
        output = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
        (dest / "COMPLETE_ORIGINAL_CATALOG.json").write_bytes(output + b"\n")
        index = {
            "schema": "UDM_ORIGINAL_V104_MSI_PRENATIVE_INDEX_V1",
            "source_sha256": catalog["original_typed_source_sha256"],
            "complete_catalog_sha256": hashlib.sha256(output).hexdigest(),
            "candidate_count": len(ids),
            "candidate_ids": ids,
            "candidate_descriptors": [
                {k: row[k] for k in ("id", "path", "selector", "builder",
                                      "changed_lines", "features")}
                for row in rows],
            "policy_count": len(orders), "policy_orders": orders,
            "horizon": p["native_gate"]["horizon_per_policy"],
            "source": catalog["source"],
            "native_calls": 0, "collection_calls": 0,
            "subject": task["repo"] + "@" + task["base"],
            "heldout_source": "UNOPENED"
        }
        (dest / "SOURCE_ONLY_INDEX.json").write_text(
            json.dumps(index, sort_keys=True, indent=2) + "\n")
        result.update(
            status="CANDIDATE_FROZEN_ORIGINAL_V104_MSI_CATALOG_NO_NATIVE",
            catalog_sha256=index["complete_catalog_sha256"],
            candidate_count=len(ids), policy_count=len(orders),
            source_manifest_sha256=index["source_sha256"])
    except Exception as e:
        result["status"] = "UNKNOWN_SOURCE_ONLY_CATALOG"
        result["reason"] = type(e).__name__ + ": " + str(e)
        result["traceback"] = traceback.format_exc(limit=10)[-3000:]
    finally:
        result["wall_seconds"] = time.monotonic() - start
        (dest / "RESULT.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: g2_v104_catalog_pre_native.py SOURCE_REPO V104_REPO MSI_REPO FRESH_OUT")
    result = main(*(Path(arg).resolve() for arg in sys.argv[1:]))
    print(json.dumps({k: result.get(k) for k in (
        "status", "candidate_count", "policy_count",
        "native_calls", "G2", "reason")}, sort_keys=True))
    raise SystemExit(0 if result["status"] ==
                     "CANDIDATE_FROZEN_ORIGINAL_V104_MSI_CATALOG_NO_NATIVE" else 2)
