#!/usr/bin/env python3
"""Run one frozen Gemma E2B CPU proposal against the pinned real Go oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request

import run_heldout_fern as native

SHA = "8e30dff3ac4c8434c49a7036fa15564bdbb6044e42bf04550bf1a096ad7e6a52"
PROTOCOL = "4aec77a860d3d6ff8c427ae9ae5ec173a5527bff"
SOURCE = "internal/api/coverage_verdict.go"
FIXTURE = "internal/api/cashtrack_outage_test.go"
TASK = ("In the Go coverage-verdict evaluator, a STEP FAIL line during a declared outage "
        "should count as an environmental inconclusive result if and only if no "
        "independently unexcused CHECK FAIL line appears. Unannotated failures must "
        "continue to count as product failures. Propose the smallest safe source change "
        "and state precisely what your proposal establishes, without claiming you ran tests.")
SYSTEM = ("Return ONLY a JSON object with exactly three string fields: old_regex, "
          "new_regex, claim. The regex fields must contain the raw regex text inside "
          "the Go declared-outage regexp.MustCompile literal, escaping backslashes for JSON. "
          "Change nothing except this one regex. Do not claim to have run any tests.")

def sha(b):
    return hashlib.sha256(b).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(4194304), b""):
            h.update(chunk)
    return h.hexdigest()

def tree(root, allowed):
    if not native.verify_source(root, native.BASE):
        return False
    code, status = native.shell(["git", "status", "--porcelain=v1", "--untracked-files=all"],
                                cwd=root, seconds=15)
    return code == 0 and sorted(status.splitlines()) == sorted(allowed)

def infer(server, model, prompt, out, report):
    with (out / "server.log").open("w", encoding="utf-8") as logfile:
        process = subprocess.Popen(
            [str(server), "-m", str(model), "-c", "4096", "-t", "4", "--parallel", "1",
             "--host", "127.0.0.1", "--port", "8876", "-ngl", "0"],
            stdout=logfile, stderr=subprocess.STDOUT)
        try:
            base = "http://127.0.0.1:8876"
            for _ in range(180):
                if process.poll() is not None:
                    raise RuntimeError("SERVER_EXITED")
                try:
                    with urllib.request.urlopen(base + "/health", timeout=2) as response:
                        if response.status == 200:
                            break
                except Exception:
                    pass
                time.sleep(1)
            else:
                raise RuntimeError("SERVER_UNREADY")
            request = {
                "model": "gemma-4-E2B-it-Q4_0", "temperature": 0, "seed": 181026,
                "max_tokens": 240, "stream": False,
                "messages": [{"role": "system", "content": SYSTEM},
                             {"role": "user", "content": prompt}],
            }
            payload = json.dumps(request, sort_keys=True).encode("utf-8")
            report["request_sha256"] = sha(payload)
            start = time.monotonic()
            req = urllib.request.Request(base + "/v1/chat/completions", data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=420) as response:
                raw_data = response.read()
            report["model_inference_seconds"] = round(time.monotonic() - start, 3)
            (out / "model_response.json").write_bytes(raw_data)
            report["response_sha256"] = sha(raw_data)
            response = json.loads(raw_data)
            report["usage"] = response.get("usage", {})
            report["model_executed"] = True
            answer = response["choices"][0]["message"].get("content") or ""
            report["raw_answer"] = answer
            return answer
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)

def decode(answer):
    if answer.lstrip().startswith(chr(96) * 3):
        return None, "REJECTED_CODE_FENCE"
    try:
        obj = json.loads(answer)
    except (TypeError, ValueError):
        return None, "REJECTED_INVALID_JSON"
    if not isinstance(obj, dict) or set(obj) != {"old_regex", "new_regex", "claim"}:
        return None, "REJECTED_OUTPUT_SCHEMA"
    if any(not isinstance(v, str) for v in obj.values()):
        return None, "REJECTED_FIELD_TYPES"
    old, new = obj["old_regex"], obj["new_regex"]
    if not old or not new or old == new or len(old) > 300 or len(new) > 300:
        return None, "REJECTED_REGEX_EMPTY_OR_LONG"
    if any(ch in new for ch in (chr(96), "\r", "\n")):
        return None, "REJECTED_REGEX_LITERAL_ESCAPE"
    return obj, "VALID_JSON"

def apply_exact(source, obj):
    marker = '{"declared outage", regexp.MustCompile(' + chr(96)
    suffix = chr(96) + ')}'
    if source.count(marker) != 1:
        return None, "UNKNOWN_TARGET_SOURCE_STRUCTURE"
    actual = source.split(marker, 1)[1].split(suffix, 1)[0]
    if actual != obj["old_regex"]:
        return None, "REJECTED_OLD_REGEX_MISMATCH"
    before = marker + actual + suffix
    after = marker + obj["new_regex"] + suffix
    if source.count(before) != 1:
        return None, "REJECTED_AMBIGUOUS_REPLACEMENT"
    return source.replace(before, after, 1), "EXACT_ONE_REGEX_REPLACEMENT"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--server", required=True)
    parser.add_argument("--out", required=True)
    opts = parser.parse_args()
    out = Path(opts.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "protocol": PROTOCOL, "model_file": Path(opts.model).name,
        "model_digest_expected": SHA, "model_executed": False,
        "one_model_request_maximum": True, "kaggle_submitted": False,
        "strong_agent_comparator_executed": False, "status": "UNKNOWN_ENVIRONMENT",
    }
    start = time.monotonic()
    try:
        if file_hash(opts.model) != SHA:
            raise RuntimeError("MODEL_SHA256_REFUSED")
        report["model_hash_verified"] = True
        with tempfile.TemporaryDirectory() as temp:
            root = native.clone_sha(Path(temp), "original", native.BASE)
            if not tree(root, []):
                raise RuntimeError("ORIGINAL_WORKTREE_NOT_CLEAN")
            original = (root / SOURCE).read_bytes()
            source = original.decode("utf-8")
            report["original_source_sha256"] = sha(original)
            excerpt = "\n".join(
                f"{i}: {line}" for i, line in enumerate(source.splitlines(), 1)
                if 244 <= i <= 336)
            prompt = TASK + "\n\nOriginal, unrepaired Go source:\n" + excerpt
            (out / "prompt.txt").write_text(prompt, encoding="utf-8")
            report["prompt_sha256"] = sha(prompt.encode("utf-8"))
            report["test_sha256"] = file_hash(native.TEST)
            answer = infer(Path(opts.server), Path(opts.model), prompt, out, report)
            proposed, parse_status = decode(answer)
            report["parse_status"] = parse_status
            if not tree(root, []):
                raise RuntimeError("SOURCE_CHANGED_AFTER_MODEL")
            target = root / FIXTURE
            if target.exists():
                raise RuntimeError("PREEXISTING_INDEPENDENT_TEST")
            shutil.copyfile(native.TEST, target)
            if not native.verify_authorized_tree(root, native.BASE, True, report["test_sha256"]):
                raise RuntimeError("TEST_BYTES_WRONG")
            baseline = native.run_go(root, "baseline_native", out)
            report["original_native"] = baseline
            expected = {key: ("FAIL" if key == "step_declared_only" else "PASS")
                        for key in native.CASES}
            if (baseline["verdicts"] != expected or baseline["returncode"] == 0
                    or not baseline["named_all_executed"]):
                raise RuntimeError("PROTECTED_ORIGINAL_BASELINE_MISMATCH")
            if proposed is None:
                report["status"] = parse_status
            else:
                report["model_claim_not_independently_warranted"] = proposed["claim"]
                edited, status = apply_exact(source, proposed)
                report["binding_status"] = status
                if edited is None:
                    report["status"] = status
                else:
                    changed = edited.encode("utf-8")
                    (root / SOURCE).write_bytes(changed)
                    allowed = [" M " + SOURCE, "?? " + FIXTURE]
                    if not tree(root, allowed) or file_hash(target) != report["test_sha256"]:
                        raise RuntimeError("MODEL_PATCH_EXCEEDS_ALLOWED_SOURCE")
                    report["patched_source_sha256"] = sha(changed)
                    patched = native.run_go(root, "model_patch_native", out)
                    report["model_patch_native"] = patched
                    if not tree(root, allowed) or (root / SOURCE).read_bytes() != changed:
                        raise RuntimeError("PATCHED_SOURCE_CHANGED_DURING_NATIVE_TEST")
                    passed = (patched["named_all_executed"] and patched["returncode"] == 0
                              and all(v == "PASS" for v in patched["verdicts"].values()))
                    (root / SOURCE).write_bytes(original)
                    if not native.verify_authorized_tree(root, native.BASE, True, report["test_sha256"]):
                        raise RuntimeError("PHYSICAL_RESTORE_CHANGED_SOURCE")
                    removed = native.run_go(root, "restored_failure_native", out)
                    report["restored_original_native"] = removed
                    if (removed["verdicts"] != expected or removed["returncode"] == 0
                            or not removed["named_all_executed"]):
                        raise RuntimeError("PHYSICAL_ABLATION_NOT_REPRODUCED")
                    report["status"] = ("WARRANTED_BOUNDED_ONE_MODEL_PATCH" if passed
                                        else "REJECTED_MODEL_PATCH_NATIVE")
    except Exception as err:
        report["status"] = "UNKNOWN_ENVIRONMENT"
        report["error"] = str(err)
    report["wall_seconds"] = round(time.monotonic() - start, 3)
    (out / "metrics.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    if report["status"] == "UNKNOWN_ENVIRONMENT":
        raise SystemExit(3)

if __name__ == "__main__":
    main()
