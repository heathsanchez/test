"""Independent native WebArenaVerified verdicts for frozen original tasks.

Run this file with the installed evaluator's Python and ``-I``. A successful
process exit means a verdict was written; only an accepted native score is a pass.
The output deliberately contains no reference answers or evaluator assertions.
"""

import argparse
import hashlib
import importlib.abc
import importlib.metadata
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


VERIFIER_SOURCE_COMMIT = "6473f72db5dcefc97b5725b59e734504edc28a21"
# SHA256 of sorted [installed_relative_path, file_sha256] records from the
# commit's 74 src/webarena_verified/*.py files and six bundled assets.
PACKAGE_SHA256 = "f0d42328008ef9e0f82008cc12399052c2be4c50fc90ac29dbbc38d8eefe7428"
DATASET_SHA256 = "d65275660814663375028e9017e1f929e3c38321041b125795e2713b52243d30"
TASK_TEMPLATES = {62: 276, 63: 276, 64: 276, 65: 276, 168: 289, 169: 289, 172: 289}
DEFAULT_EVALUATOR = Path("/workspace/repos/webarena-verified")


class VerifierPinError(ValueError):
    """The installed native authority does not match the frozen source."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _package_manifest(package_root: Path) -> list:
    files = sorted(
        path for path in package_root.rglob("*")
        if path.is_file() and (
            path.suffix == ".py"
            or ("assets" in path.relative_to(package_root).parts and path.name != ".gitkeep")
        )
    )
    return [[path.relative_to(package_root).as_posix(), _sha256(path.read_bytes())] for path in files]


def verify_package_pin(package_root: Path, evaluator_path: Path | None = None) -> dict:
    """Check every installed Python source and bundled asset before importing it."""
    package_root = Path(package_root).resolve()
    manifest = _package_manifest(package_root)
    digest = _sha256(json.dumps(manifest, separators=(",", ":")).encode())
    if digest != PACKAGE_SHA256:
        raise VerifierPinError("installed_package_pin_mismatch")
    source = Path(evaluator_path or DEFAULT_EVALUATOR).resolve()
    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    if commit != VERIFIER_SOURCE_COMMIT:
        raise VerifierPinError("verifier_source_commit_mismatch")
    return {
        "verifier_source_commit": commit,
        "verifier_package_sha256": digest,
        "verifier_package_file_count": len(manifest),
        "verifier_package_path": str(package_root),
    }


class _PinnedSourceLoader(importlib.machinery.SourceFileLoader):
    """Compile the hashed source directly, bypassing all existing bytecode caches."""

    def __init__(self, name: str, path: Path, digest: str):
        super().__init__(name, str(path))
        self._expected_digest = digest

    def get_code(self, fullname):
        source = Path(self.path).read_bytes()
        if _sha256(source) != self._expected_digest:
            raise VerifierPinError("native_source_changed_during_import")
        code = self.source_to_code(source, self.path)
        self.verified_source_sha256 = self._expected_digest
        return code


class _PinnedSourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, package_root: Path):
        self.root = package_root.resolve()
        manifest = _package_manifest(self.root)
        if _sha256(json.dumps(manifest, separators=(",", ":")).encode()) != PACKAGE_SHA256:
            raise VerifierPinError("installed_package_pin_mismatch")
        self.sources = dict(manifest)
        for name, module in tuple(sys.modules.items()):
            if name == "webarena_verified" or name.startswith("webarena_verified."):
                source = Path(module.__file__).resolve()
                expected = self.sources.get(source.relative_to(self.root).as_posix())
                if not expected or getattr(module.__loader__, "verified_source_sha256", None) != expected:
                    raise VerifierPinError("native_module_preloaded_without_verified_source")

    def find_spec(self, fullname, path=None, target=None):
        if fullname != "webarena_verified" and not fullname.startswith("webarena_verified."):
            return None
        location = self.root.joinpath(*fullname.split(".")[1:])
        is_package = (location / "__init__.py").is_file()
        source = location / "__init__.py" if is_package else location.with_suffix(".py")
        digest = self.sources.get(source.relative_to(self.root).as_posix())
        if digest is None:
            raise VerifierPinError("native_module_outside_pinned_source")
        return importlib.util.spec_from_file_location(
            fullname, source, loader=_PinnedSourceLoader(fullname, source, digest),
            submodule_search_locations=[str(location)] if is_package else None,
        )


def verify(
    response_path: Path,
    task_id: int,
    config_path: Path,
    *,
    evaluator_path: Path | None = None,
) -> dict:
    """Use the genuine native API on an exact byte snapshot of the response."""
    started = time.perf_counter()
    source_finder = None
    verdict = {
        "status": "error",
        "score": 0.0,
        "native_status": None,
        "native_score": None,
        "evaluated": False,
        "task_id": task_id,
        "intent_template_id": None,
        "response_sha256": None,
        "config_sha256": None,
        "verifier_source_commit": VERIFIER_SOURCE_COMMIT,
        "scope": "frozen_original_tasks",
    }
    try:
        response_path, config_path = Path(response_path).resolve(), Path(config_path).resolve()
        response_bytes = response_path.read_bytes()
        verdict["response_sha256"] = _sha256(response_bytes)
        config_bytes = config_path.read_bytes()
        verdict["config_sha256"] = _sha256(config_bytes)
        if type(task_id) is not int or task_id not in TASK_TEMPLATES:
            verdict.update(status="rejected", reason="task_out_of_scope")
            return verdict

        spec = importlib.util.find_spec("webarena_verified")
        if spec is None or spec.origin is None:
            raise VerifierPinError("native_evaluator_not_installed")
        package_root = Path(spec.origin).parent
        verdict.update(verify_package_pin(package_root, evaluator_path))
        if importlib.metadata.version("webarena-verified") != "1.2.3":
            raise VerifierPinError("native_evaluator_version_mismatch")

        source_finder = _PinnedSourceFinder(package_root)
        sys.meta_path.insert(0, source_finder)
        from webarena_verified import WebArenaVerified
        from webarena_verified.types.tracing import NetworkTrace

        with tempfile.TemporaryDirectory(prefix="native-developmental-verifier-") as directory:
            response_snapshot = Path(directory) / "agent_response.json"
            config_snapshot = Path(directory) / "config.json"
            response_snapshot.write_bytes(response_bytes)
            config_snapshot.write_bytes(config_bytes)
            evaluator = WebArenaVerified(config=config_snapshot)
            if _sha256(evaluator.config.test_data_file.read_bytes()) != DATASET_SHA256:
                verdict.update(status="rejected", reason="dataset_pin_mismatch")
                return verdict
            task = evaluator.get_task(task_id)
            verdict["intent_template_id"] = task.intent_template_id
            if task.task_id != task_id or task.intent_template_id != TASK_TEMPLATES[task_id]:
                verdict.update(status="rejected", reason="task_template_out_of_scope")
                return verdict

            result = evaluator.evaluate_task(
                task_id=task_id,
                agent_response=response_snapshot,
                network_trace=NetworkTrace.model_construct(
                    is_playwright=False, src_file=Path("<none>"), events=()
                ),
            )
            verdict.update(
                evaluated=True,
                native_status=str(result.status),
                native_score=result.score,
                native_evaluator_checksum=result.webarena_verified_evaluator_checksum,
                native_dataset_sha256=result.webarena_verified_data_checksum,
                native_version=result.webarena_verified_version,
            )
            if result.task_id != task_id or result.intent_template_id != TASK_TEMPLATES[task_id]:
                raise VerifierPinError("native_result_task_binding_mismatch")
            if result.webarena_verified_data_checksum != DATASET_SHA256:
                raise VerifierPinError("native_result_dataset_pin_mismatch")
            if response_path.read_bytes() != response_bytes or config_path.read_bytes() != config_bytes:
                raise VerifierPinError("input_changed_during_verification")
            if str(result.status) == "error":
                verdict.update(status="error", reason="native_evaluation_error")
                return verdict
            raw_response = response_snapshot.read_text()
            if not result.evaluators_results or any(
                evaluation.actual != raw_response for evaluation in result.evaluators_results
            ):
                raise VerifierPinError("native_response_binding_mismatch")
            if result.score == 1.0 and str(result.status) == "success":
                verdict.update(status="accepted", score=1.0, reason="native_success")
            else:
                verdict.update(status="rejected", reason="native_failure")
    except Exception as error:
        verdict.update(status="error", score=0.0, reason=str(error), error_type=type(error).__name__)
    finally:
        if source_finder is not None and source_finder in sys.meta_path:
            sys.meta_path.remove(source_finder)
        verdict["elapsed_seconds"] = time.perf_counter() - started
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--response", required=True, type=Path)
    parser.add_argument("--task-id", required=True, type=int)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--evaluator", type=Path, default=DEFAULT_EVALUATOR)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.resolve() in (args.response.resolve(), args.config.resolve()):
        parser.error("--out must not overwrite a verifier input")
    verdict = verify(args.response, args.task_id, args.config, evaluator_path=args.evaluator)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
