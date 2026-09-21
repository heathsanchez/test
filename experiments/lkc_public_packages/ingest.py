#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import urllib.parse
import zipfile
from pathlib import Path

API_BASE = "https://api.sair.foundation/api/public/v1"
COMPETITION = "lean-kernel-challenge"
KIND = "lean-kernel-package"
PROBLEMS = [
    "fib", "partition", "mertens", "primecount",
    "permanent", "ca-rule110", "sha256", "polydisc",
]
OUT = Path("experiments/lkc_public_packages/out")

KEYWORDS = [
    "BitVec", "Array", "List", "Nat.fold", "Nat.fastFib",
    "primeCounting", "minFac", "moebius", "sieve", "bitset",
    "permanent", "subset", "mask", "Rule110", "shift", "xor",
    "sha256", "Bareiss", "resultant", "subresultant", "determinant",
    "scanl", "zipWith", "getD", "foldl", "omega",
]


def curl_json(url: str, token: str) -> dict:
    proc = subprocess.run(
        ["curl", "-fsS", url, "-H", f"Authorization: Bearer {token}"],
        check=True,
        capture_output=True,
    )
    return json.loads(proc.stdout)


def curl_bytes(url: str, token: str) -> bytes:
    proc = subprocess.run(
        ["curl", "-fsS", url, "-H", f"Authorization: Bearer {token}"],
        check=True,
        capture_output=True,
    )
    return proc.stdout


def safe_extract(zf: zipfile.ZipFile, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    names = []
    root = dest.resolve()
    for info in zf.infolist():
        target = (dest / info.filename).resolve()
        if root != target and root not in target.parents:
            raise RuntimeError(f"unsafe zip path: {info.filename}")
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(zf.read(info))
        names.append(info.filename)
    return names


def lean_features(text: str) -> dict:
    defs = re.findall(r"(?m)^\s*(?:private\s+)?def\s+([A-Za-z0-9_'.]+)", text)
    theorems = re.findall(r"(?m)^\s*(?:private\s+)?theorem\s+([A-Za-z0-9_'.]+)", text)
    imports = re.findall(r"(?m)^\s*import\s+([^\s]+)", text)
    return {
        "bytes": len(text.encode()),
        "lines": text.count("\n") + 1,
        "defs": defs[:100],
        "theorems": theorems[:100],
        "imports": imports,
        "keyword_hits": {k: text.count(k) for k in KEYWORDS if k in text},
    }


def list_items(problem: str, token: str) -> list[dict]:
    items = []
    cursor = None
    while True:
        params = {
            "competitionId": COMPETITION,
            "kind": KIND,
            "problemId": problem,
            "limit": "100",
            "sort": "newest",
        }
        if cursor:
            params["cursor"] = cursor
        url = API_BASE + "/contributor-network/items?" + urllib.parse.urlencode(params)
        payload = curl_json(url, token)
        data = payload["data"]
        items.extend(data.get("items", []))
        cursor = data.get("nextCursor")
        if not cursor:
            return items


def main() -> None:
    token = os.environ.get("SAIR_API_KEY")
    if not token:
        raise SystemExit("SAIR_API_KEY is required")

    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    summary = {
        "schema_version": 1,
        "competition": COMPETITION,
        "kind": KIND,
        "problems": {},
    }

    total = 0
    for problem in PROBLEMS:
        items = list_items(problem, token)
        psummary = []
        for item in items:
            total += 1
            code = item["publicCode"]
            item_id = item["id"]
            download_url = item["downloadUrl"]
            if download_url.startswith("/"):
                download_url = "https://api.sair.foundation" + download_url
            blob = curl_bytes(download_url, token)
            digest = hashlib.sha256(blob).hexdigest()
            expected = item["packageSha256"]
            if digest != expected:
                raise RuntimeError(f"{code}: package hash mismatch {digest} != {expected}")

            package_dir = OUT / "packages" / problem / code
            zip_path = package_dir / item["packageFilename"]
            package_dir.mkdir(parents=True, exist_ok=True)
            zip_path.write_bytes(blob)

            with zipfile.ZipFile(zip_path) as zf:
                names = safe_extract(zf, package_dir / "workspace")

            submissions = []
            for path in sorted((package_dir / "workspace").rglob("Submission.lean")):
                text = path.read_text(errors="replace")
                submissions.append({
                    "path": str(path.relative_to(package_dir / "workspace")),
                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "features": lean_features(text),
                })

            rec = {
                "id": item_id,
                "publicCode": code,
                "title": item.get("title"),
                "author": item.get("author"),
                "problemId": problem,
                "publishedAt": item.get("publishedAt"),
                "approvedRevision": item.get("approvedRevision"),
                "solutionRevision": item.get("solutionRevision"),
                "executionSnapshotId": item.get("executionSnapshotId"),
                "workspaceSha256": item.get("workspaceSha256"),
                "packageSha256": expected,
                "packageFilename": item.get("packageFilename"),
                "packageFileCount": item.get("packageFileCount"),
                "artifactExcerpt": item.get("artifactExcerpt"),
                "favoriteCount": item.get("favoriteCount"),
                "files": names,
                "submissions": submissions,
            }
            psummary.append(rec)

        summary["problems"][problem] = {
            "count": len(psummary),
            "items": psummary,
        }

    summary["total_items"] = total
    (OUT / "manifest.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    compact = {
        p: [
            {
                "publicCode": x["publicCode"],
                "title": x["title"],
                "author": x["author"],
                "publishedAt": x["publishedAt"],
                "submissions": x["submissions"],
            }
            for x in data["items"]
        ]
        for p, data in summary["problems"].items()
    }
    (OUT / "algorithm-index.json").write_text(json.dumps(compact, indent=2, sort_keys=True) + "\n")
    print(json.dumps({p: summary["problems"][p]["count"] for p in PROBLEMS}, sort_keys=True))
    print(f"total_items={total}")


if __name__ == "__main__":
    main()
