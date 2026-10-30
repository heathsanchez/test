"""Source-pinned external false-green test: zero cases, native cases, mutation.

This tests the authority of a test receipt, not any bug in the external project.
It never modifies the pinned external checkout. Each run has its own process.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

SOURCE_REPO = "pallets/itsdangerous"
SOURCE_COMMIT = "672971d66a2ef9f85151e53283113f33d642dabd"


def classify(*, exit_code: int, recognized: Optional[int], failed: int = 0) -> str:
    """A green process exit is never evidence when the verifier ran no cases."""
    if recognized is None or recognized < 1:
        return "UNKNOWN_ZERO_RECOGNIZED_TESTS"
    if exit_code != 0 or failed > 0:
        return "REJECTED"
    return "PASS_BOUNDED"


def run(*args: str, cwd: Path, env: Optional[dict] = None) -> dict:
    result = subprocess.run(
        [sys.executable, *args], cwd=cwd, env=env, capture_output=True,
        text=True, timeout=180,
    )
    return {
        "exit_code": result.returncode,
        "output": (result.stdout + "\n" + result.stderr)[-12000:],
    }


def count(regex: str, output: str) -> Optional[int]:
    found = re.search(regex, output)
    return int(found.group(1)) if found else None


def assess(source: Path) -> dict:
    head = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True,
    ).strip()
    if head != SOURCE_COMMIT:
        raise ValueError(f"UNKNOWN_SOURCE_PIN_MISMATCH {head}")

    original = source / "src" / "itsdangerous" / "encoding.py"
    original_bytes = original.read_bytes()
    result = {
        "source": f"{SOURCE_REPO}@{SOURCE_COMMIT}",
        "original_encoding_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "boundary": "REAL_THIRD_PARTY_SOURCE_TEST_ORACLE_IN_EPHEMERAL_CLONE",
        "production_change": False,
        "strict_seven_gate_closure": "UNKNOWN",
    }

    # This is a deliberately wrong runner for the *actual* pytest tests.
    wrong = run("-m", "unittest", "discover",
                "-s", "tests", "-p", "test_*.py", cwd=source)
    wrong_count = count(r"Ran (\d+) tests? in", wrong["output"])
    result["wrong_runner"] = {
        "exit_code": wrong["exit_code"],
        "recognized_tests": wrong_count,
        "guard": classify(exit_code=wrong["exit_code"], recognized=wrong_count),
        "output_tail": wrong["output"][-1500:],
    }
    if wrong["exit_code"] != 0 or wrong_count != 0:
        raise ValueError(f"UNKNOWN_WRONG_RUNNER_DID_NOT_MISLEAD {result['wrong_runner']}")

    # Correct original framework, source and tests, no substitute oracle.
    native = run("-m", "pytest", "-q", "tests/test_itsdangerous", cwd=source)
    passed = count(r"(\d+) passed", native["output"])
    result["original_pytest"] = {
        "exit_code": native["exit_code"],
        "passed_tests": passed,
        "guard": classify(exit_code=native["exit_code"], recognized=passed),
        "output_tail": native["output"][-1500:],
    }
    if result["original_pytest"]["guard"] != "PASS_BOUNDED" or passed < 10:
        raise ValueError("UNKNOWN_ORIGINAL_PYTEST_UNQUALIFIED")

    # Mutate only a temporary copy; test the ORIGINAL pytest oracle unchanged.
    with tempfile.TemporaryDirectory(prefix="g1-false-green-mutant-") as tmp:
        mutated_src = Path(tmp) / "src"
        shutil.copytree(source / "src" / "itsdangerous", mutated_src / "itsdangerous")
        mutation_path = mutated_src / "itsdangerous" / "encoding.py"
        content = mutation_path.read_text()
        marker = "    return s\n\n\ndef base64_encode("
        if content.count(marker) != 1:
            raise ValueError("UNKNOWN_MUTATION_SITE_NOT_UNIQUE")
        mutation_path.write_text(
            content.replace(marker, '    return b""\n\n\ndef base64_encode(', 1)
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(mutated_src) + os.pathsep + env.get("PYTHONPATH", "")
        probe = run("-c", "import itsdangerous.encoding as e; print(e.__file__)",
                    cwd=source, env=env)
        if (probe["exit_code"] != 0
                or not str(mutation_path.resolve()) in probe["output"]):
            raise ValueError("UNKNOWN_MUTATED_IMPORT_NOT_VERIFIED")
        negative = run("-m", "pytest", "-q",
                       "tests/test_itsdangerous/test_encoding.py",
                       cwd=source, env=env)
        failed = count(r"(\d+) failed", negative["output"])
        result["original_pytest_negative_mutation"] = {
            "exit_code": negative["exit_code"],
            "failed_tests": failed,
            "guard": classify(exit_code=negative["exit_code"],
                              recognized=failed, failed=failed or 0),
            "mutated_encoding_sha256": hashlib.sha256(
                mutation_path.read_bytes()
            ).hexdigest(),
            "output_tail": negative["output"][-1800:],
        }
    if negative["exit_code"] != 1 or not failed or failed < 1:
        raise ValueError("UNKNOWN_MUTATION_NOT_DETECTED")
    if result["original_pytest_negative_mutation"]["guard"] != "REJECTED":
        raise ValueError("UNKNOWN_FAILED_VERIFIER_ACCEPTED")

    result["status"] = "WARRANTED_BOUNDED_NATIVE_ZERO_TEST_FALSE_GREEN"
    result["scope"] = (
        "The same pinned external suite returns success with zero recognized "
        "tests under the wrong unittest runner; the guard refuses admission; "
        "the original pytest suite passes and rejects one injected mutation. "
        "No external bug, production integration or universal G1 closure."
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {"status": "UNKNOWN", "source": f"{SOURCE_REPO}@{SOURCE_COMMIT}"}
    try:
        result = assess(args.source.resolve())
    except Exception as exc:
        result["status"] = "UNKNOWN_EXPERIMENT_FAILURE"
        result["error"] = f"{type(exc).__name__}: {exc}"
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "scope"}, indent=2))
    if result["status"] != "WARRANTED_BOUNDED_NATIVE_ZERO_TEST_FALSE_GREEN":
        sys.exit(1)


if __name__ == "__main__":
    main()
