"""Bounded, externally authenticated Nucleus/MGSO historical reuse.

The MGSO store is untrusted data. A reader may skip an *identical historical*
kernel invocation only when the GitHub Actions producer, its stored ZIP bytes,
the candidate executable, current source, flags and MGSO graph all match.
This is not a Lean proof certificate or a new kernel ACCEPT operation.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
from urllib.request import Request, urlopen
import zipfile


SCHEMA = "mathgraph.nucleus-mgso-history.v1"
REPO = "heathsanchez/test"
BRANCH = "research/nucleus-mgso-authenticated-reuse-20261104"
WORKFLOW = ".github/workflows/nucleus-mgso-authenticated-reuse-20261104.yml"
PRODUCER_JOB = "producer"
ARTIFACT_NAME = "nucleus-mgso-verified-history"
MAX_ZIP = 16_000_000
MAX_UNCOMPRESSED = 40_000_000
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
INSPECT_LINE = re.compile(
    r"NUCLEUS_MGSO_INSPECT:status=candidate-match;authority=none;"
    r"fresh-check=false;declarations=([1-9][0-9]*)\Z"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unknown(reason: str) -> dict:
    return {"status": "UNKNOWN", "reason": reason, "fresh_check": False,
            "kernel_invocations_in_reader": 0, "permission": "NONE"}


def strict_json(raw: bytes, limit: int = 1_000_000):
    if len(raw) > limit:
        raise ValueError("JSON_TOO_LARGE")

    def unique_pairs(pairs):
        obj = {}
        for name, value in pairs:
            if name in obj:
                raise ValueError("DUPLICATE_JSON_FIELD")
            obj[name] = value
        return obj

    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))


def flags_from(env: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in sorted(env.items())
            if key.startswith("NUCLEUS_")}


def validate_metadata(metadata: dict, pin: dict, archive: bytes) -> str | None:
    """Trust only independent GitHub API facts, never a saved report's claims."""
    if not isinstance(metadata, dict) or not isinstance(pin, dict):
        return "INVALID_PRODUCER_METADATA"
    try:
        run, jobs, artifacts = (metadata["run"], metadata["jobs"], metadata["artifacts"])
        if not (isinstance(run, dict) and isinstance(jobs, list)
                and isinstance(artifacts, list)):
            return "INVALID_PRODUCER_METADATA"
        if (type(pin["run_id"]) is not int or pin["run_id"] < 1
                or type(pin["attempt"]) is not int or pin["attempt"] < 1
                or not isinstance(pin["commit"], str)
                or not SHA40.fullmatch(pin["commit"])):
            return "INVALID_PRODUCER_PIN"
        if (run.get("id") != pin["run_id"]
                or run.get("run_attempt") != pin["attempt"]
                or run.get("head_sha") != pin["commit"]
                or run.get("head_branch") != BRANCH
                or run.get("path") != WORKFLOW
                or run.get("event") != "push"
                or (run.get("repository") or {}).get("full_name") != REPO):
            return "PRODUCER_IDENTITY_MISMATCH"
        completed = pin.get("completed") is True
        if completed:
            if run.get("status") != "completed" or run.get("conclusion") != "success":
                return "PRODUCER_NOT_SUCCESSFUL"
        elif run.get("status") != "in_progress":
            return "SAME_RUN_NOT_ACTIVE"
        producers = [job for job in jobs if isinstance(job, dict)
                     and job.get("name") == PRODUCER_JOB]
        if len(producers) != 1 or (producers[0].get("run_id") != pin["run_id"]
                                   or producers[0].get("status") != "completed"
                                   or producers[0].get("conclusion") != "success"
                                   or type(producers[0].get("id")) is not int):
            return "PRODUCER_JOB_NOT_AUTHENTICATED"
        matching = [artifact for artifact in artifacts if isinstance(artifact, dict)
                    and artifact.get("name") == ARTIFACT_NAME]
        if len(matching) != 1:
            return "PRODUCER_ARTIFACT_AMBIGUOUS"
        artifact = matching[0]
        origin = artifact.get("workflow_run") or {}
        if (type(artifact.get("id")) is not int or artifact["id"] < 1
                or artifact.get("expired") is not False
                or origin.get("id") != pin["run_id"]
                or origin.get("head_sha") != pin["commit"]
                or artifact.get("digest") != "sha256:" + digest(archive)):
            return "PRODUCER_ARTIFACT_DIGEST_OR_PROVENANCE_MISMATCH"
    except (KeyError, TypeError, AttributeError, ValueError):
        return "INVALID_PRODUCER_METADATA"
    return None


def unpack_checked(archive: bytes, directory: Path):
    """No user-supplied paths, duplicate entries, symlinks or ZIP bombs."""
    if len(archive) > MAX_ZIP:
        raise ValueError("ARCHIVE_TOO_LARGE")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        members = z.infolist()
        if not 1 <= len(members) <= 4096:
            raise ValueError("INVALID_ARCHIVE_SIZE")
        if sum(item.file_size for item in members) > MAX_UNCOMPRESSED:
            raise ValueError("ARCHIVE_DECOMPRESSED_TOO_LARGE")
        seen = set()
        for entry in members:
            name = entry.filename
            path = PurePosixPath(name)
            if (not name or "\\" in name or path.is_absolute()
                    or any(part in (".", "..") for part in path.parts)
                    or path.parts[0] not in ("nucleus", "report.json", "store")
                    or str(path) != name.rstrip("/")
                    or name in seen or stat.S_ISLNK(entry.external_attr >> 16)):
                raise ValueError("UNSAFE_ARCHIVE_ENTRY")
            seen.add(name)
            dest = directory.joinpath(*path.parts)
            if entry.is_dir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(entry, "r") as source, dest.open("xb") as target:
                    shutil.copyfileobj(source, target, length=65536)
    if not (directory / "nucleus").is_file() or not (directory / "report.json").is_file():
        raise ValueError("INCOMPLETE_ARCHIVE")


def make_producer(binary: Path, source: Path, output: Path, env: dict[str, str]) -> dict:
    """The only entry point that runs the fresh independent Lean checker."""
    if output.exists():
        raise ValueError("PRODUCER_OUTPUT_ALREADY_EXISTS")
    input_bytes, binary_bytes = source.read_bytes(), binary.read_bytes()
    if not input_bytes or not 0 < len(binary_bytes) <= 12_000_000:
        raise ValueError("INVALID_SOURCE_OR_BINARY")
    with tempfile.TemporaryDirectory(prefix="nucleus-mgso-producer-") as temp:
        store = Path(temp) / "store"
        completed = subprocess.run([str(binary), "--mgso-shadow-dir", str(store)],
                                   input=input_bytes, capture_output=True,
                                   env=env, timeout=120)
        if (completed.returncode != 0 or completed.stdout
                or b"NUCLEUS_MGSO_SHADOW:write=complete;" not in completed.stderr):
            raise ValueError("PRODUCER_FRESH_KERNEL_NOT_ACCEPTED_OR_NOT_RECORDED")
        root = store / "root.json"
        if not root.is_file():
            raise ValueError("PRODUCER_ROOT_NOT_STORED")
        receipt = {
            "schema": SCHEMA,
            "status": "WARRANTED_BOUNDED",
            "scope": "whole-export-exact-binary-source-config",
            "kernel_exit_code": completed.returncode,
            "source_sha256": digest(input_bytes),
            "binary_sha256": digest(binary_bytes),
            "root_sha256": digest(root.read_bytes()),
            "flags": flags_from(env),
        }
        output.mkdir(parents=True)
        (output / "nucleus").write_bytes(binary_bytes)
        shutil.copytree(store, output / "store")
        (output / "report.json").write_text(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    return receipt


def evaluate(metadata: dict, pin: dict, archive: bytes, current_source: bytes,
             env: dict[str, str], *, before_inspect=None) -> dict:
    """Read historical graph, independently measure actual current input.

    `before_inspect` injects adversarial fixture corruption in tests only.
    Even successful inspection is not an independent proof: prior authority is
    the externally authenticated successful producer job and exact context.
    """
    reason = validate_metadata(metadata, pin, archive)
    if reason:
        return unknown(reason)
    try:
        with tempfile.TemporaryDirectory(prefix="nucleus-mgso-reader-") as temp:
            directory = Path(temp)
            unpack_checked(archive, directory)
            report = strict_json((directory / "report.json").read_bytes())
            if not isinstance(report, dict) or (report.get("schema") != SCHEMA
                    or report.get("status") != "WARRANTED_BOUNDED"
                    or report.get("scope") != "whole-export-exact-binary-source-config"
                    or report.get("kernel_exit_code") != 0):
                return unknown("HISTORICAL_REPORT_NOT_ADMITTED")
            binary = directory / "nucleus"
            binary_bytes = binary.read_bytes()
            if (not 0 < len(binary_bytes) <= 12_000_000
                    or report.get("binary_sha256") != digest(binary_bytes)
                    or report.get("source_sha256") != digest(current_source)
                    or report.get("root_sha256") != digest((directory / "store/root.json").read_bytes())
                    or report.get("flags") != flags_from(env)):
                return unknown("CURRENT_SOURCE_BINARY_CONFIG_OR_ROOT_DRIFT")
            if before_inspect is not None:
                before_inspect(directory)
            binary.chmod(0o700)
            probe = subprocess.run([str(binary), "--mgso-inspect-dir", str(directory / "store")],
                                   input=current_source, capture_output=True,
                                   env=env, timeout=120)
            diagnostics = probe.stderr.decode("utf-8", errors="replace").strip().splitlines()
            if (probe.returncode != 2 or probe.stdout or len(diagnostics) != 1
                    or not INSPECT_LINE.fullmatch(diagnostics[0])
                    or digest((directory / "store/root.json").read_bytes())
                    != report["root_sha256"]):
                return unknown("INSPECTION_FAILED_OR_UNTRUSTED_GRAPH")
            return {"status": "REUSABLE_BOUNDED",
                    "reason": "EXACT_PRIOR_CHECK_AUTHENTICATED",
                    "permission": "REUSE_EXACT_HISTORICAL_CHECK_ONLY",
                    "authority": "PINNED_GITHUB_ACTIONS_PRODUCER",
                    "producer_run_id": pin["run_id"],
                    "historical_kernel_result": "ACCEPT",
                    "declarations": int(INSPECT_LINE.fullmatch(diagnostics[0]).group(1)),
                    "source_sha256": report["source_sha256"],
                    "binary_sha256": report["binary_sha256"],
                    "fresh_check": False,
                    "kernel_invocations_in_reader": 0}
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
        return unknown("UNVERIFIABLE_REUSE_MATERIAL:" + type(error).__name__)


def github_metadata(run_id: int, token: str) -> dict:
    if not token:
        raise ValueError("MISSING_GITHUB_READ_TOKEN")
    base = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}"

    def get_json(url):
        request = Request(url, headers={"Authorization": "Bearer " + token,
                                       "Accept": "application/vnd.github+json",
                                       "X-GitHub-Api-Version": "2022-11-28"})
        with urlopen(request, timeout=30) as connection:
            content = connection.read(2_000_001)
        return strict_json(content, limit=2_000_000)

    return {"run": get_json(base), "jobs": get_json(base + "/jobs?per_page=100")["jobs"],
            "artifacts": get_json(base + "/artifacts?per_page=100")["artifacts"]}


def github_archive(metadata: dict, token: str) -> bytes:
    matches = [x for x in metadata["artifacts"] if x.get("name") == ARTIFACT_NAME]
    if len(matches) != 1 or type(matches[0].get("id")) is not int:
        raise ValueError("ARTIFACT_MISSING_OR_AMBIGUOUS")
    url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{matches[0]['id']}/zip"
    request = Request(url, headers={"Authorization": "Bearer " + token,
                                   "Accept": "application/vnd.github+json"})
    with urlopen(request, timeout=40) as connection:
        raw = connection.read(MAX_ZIP + 1)
    if len(raw) > MAX_ZIP:
        raise ValueError("ARCHIVE_TOO_LARGE")
    return raw


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    producer = modes.add_parser("produce")
    producer.add_argument("--binary", type=Path, required=True)
    producer.add_argument("--source", type=Path, required=True)
    producer.add_argument("--output", type=Path, required=True)
    consumer = modes.add_parser("consume")
    consumer.add_argument("--source", type=Path, required=True)
    consumer.add_argument("--run-id", type=int, required=True)
    consumer.add_argument("--commit", required=True)
    consumer.add_argument("--attempt", type=int, default=1)
    consumer.add_argument("--completed", action="store_true")
    consumer.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.mode == "produce":
        result = make_producer(args.binary, args.source, args.output, dict(os.environ))
        print(json.dumps(result, sort_keys=True))
        return 0
    try:
        pin = {"run_id": args.run_id, "commit": args.commit, "attempt": args.attempt,
               "completed": args.completed}
        metadata = github_metadata(args.run_id, os.environ.get("GITHUB_TOKEN", ""))
        archive = github_archive(metadata, os.environ.get("GITHUB_TOKEN", ""))
        result = evaluate(metadata, pin, archive, args.source.read_bytes(), dict(os.environ))
    except (OSError, KeyError, ValueError, TimeoutError) as error:
        result = unknown("EXTERNAL_PROVENANCE_UNAVAILABLE:" + type(error).__name__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "REUSABLE_BOUNDED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
