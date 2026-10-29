"""Single-source experimental cold transport; NOT an unrestricted .mg runtime.

Only the exact pinned, separately qualified FLASH V16b Python blob is admitted.
Importing Python code is not a security sandbox or an independent verifier.
"""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil


ID = "flash-v16b-source-byte-identical-executable-constructor"
GIT_BLOB = "0f7fb6b837cd65aa86b5fef7c097196fc0df4845"
SCHEMA = "mg.cold-executable-experiment.v0"
ENTRY = "learned_exact_rank"


class PackageError(Exception):
    pass


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def _manifest(package: Path) -> dict:
    try:
        manifest = json.loads((package / "capability.mg").read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise PackageError("INVALID_MANIFEST") from error
    if (manifest.get("schema"), manifest.get("id"), manifest.get("entrypoint"),
        manifest.get("source_git_blob_sha"), manifest.get("permission")) != (
        SCHEMA, ID, ENTRY, GIT_BLOB, "READ_ONLY_TEST"
    ):
        raise PackageError("INVALID_MANIFEST")
    return manifest


def create_package(source: Path, package: Path) -> None:
    data = source.read_bytes()
    if blob_sha(data) != GIT_BLOB:
        raise PackageError("SOURCE_HASH_MISMATCH")
    if (package / "capability.mg").exists():
        raise PackageError("EXISTING_PACKAGE")
    package.mkdir(parents=True, exist_ok=True)
    (package / "learned_repair.py").write_bytes(data)
    (package / "capability.mg").write_text(json.dumps({
        "schema": SCHEMA, "id": ID, "source_git_blob_sha": GIT_BLOB,
        "source_commit": "483b62435c406c364c773246658dbac82f92365e",
        "entrypoint": ENTRY, "input_binding": "undirected-simple-graph-edge-bits-v1",
        "permission": "READ_ONLY_TEST", "generation": 1, "active": True,
        "prior_native_verifier": "MathGraph original 420-case oracle (NOT rerun here)",
    }, sort_keys=True, indent=2) + "\n")


def execute(package: Path, n: int, edge_bits: int) -> int:
    manifest = _manifest(package)
    if not manifest.get("active"):
        raise PackageError("INACTIVE_GENERATION")
    if not (0 <= n <= 6 and 0 <= edge_bits < (1 << (n * (n - 1) // 2))):
        raise PackageError("OUT_OF_SCOPE")
    source = package / "learned_repair.py"
    try:
        data = source.read_bytes()
    except OSError as error:
        raise PackageError("SOURCE_MISSING") from error
    if blob_sha(data) != GIT_BLOB:
        raise PackageError("SOURCE_HASH_MISMATCH")
    spec = importlib.util.spec_from_file_location("pinned_flash_v16b", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    method = getattr(module, ENTRY, None)
    if not callable(method):
        raise PackageError("ENTRYPOINT_MISSING")
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    edges = [pair for bit, pair in enumerate(pairs) if edge_bits & (1 << bit)]

    def independent(chosen: int) -> bool:
        return all(not (chosen & (1 << i) and chosen & (1 << j)) for i, j in edges)

    return method(n, independent)


def withdraw(package: Path) -> None:
    item = _manifest(package)
    if not item["active"]:
        raise PackageError("ALREADY_INACTIVE")
    source = package / "learned_repair.py"
    if blob_sha(source.read_bytes()) != GIT_BLOB:
        raise PackageError("SOURCE_HASH_MISMATCH")
    source.rename(package / f"quarantine.gen{item['generation']}.py")
    item["active"] = False
    (package / "capability.mg").write_text(json.dumps(item, sort_keys=True, indent=2) + "\n")


def requalify(package: Path) -> int:
    item = _manifest(package)
    if item["active"]:
        raise PackageError("NOT_WITHDRAWN")
    source = package / f"quarantine.gen{item['generation']}.py"
    if blob_sha(source.read_bytes()) != GIT_BLOB:
        raise PackageError("SOURCE_HASH_MISMATCH")
    shutil.copyfile(source, package / "learned_repair.py")
    item["generation"] += 1
    item["active"] = True
    (package / "capability.mg").write_text(json.dumps(item, sort_keys=True, indent=2) + "\n")
    return item["generation"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--edges", type=int, required=True)
    args = parser.parse_args()
    try:
        result = execute(args.package, args.n, args.edges)
        print(json.dumps({"generation": _manifest(args.package)["generation"],
                          "n": args.n, "rank": result}, sort_keys=True))
    except PackageError as error:
        parser.exit(2, str(error) + "\n")
