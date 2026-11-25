"""Measure exact renovation beta inputs without pretending 3.2 support.

No checker semantics are changed. Source labels and bytes are bound to one
published beta run. Distinguish an unsupported format from an invalid proof.
"""
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import time
import zipfile

ARENA = "leanprover/lean-kernel-arena-beta"
RUN = 45496247921
REV = "e6d5f8c722a47b65c0ac0ea7cc83a4dae24fd41b"
ARTIFACTS = {
    "results": (14972588775, "b13a766a72ff82077a9e362e7eee13304d92ac2dec19a1511fc638ef520fd13f"),
    "tarball": (14967849994, "46e622cbc52cd820dd45e323f5441c4e9cbe7b571fde29ca6f3da0888f524cae"),
}
EXTRAS = (
    "C182_TYPED_PROOF_IRREL", "C189_NEUTRAL_LAMBDA_PROOF",
    "C190_QUOTIENT_IOTA", "C199_TWO_PARAM_EIGHT_FIELD_RECORD",
    "C201_CLOSED_NULLARY_ENUM", "C216_RIGID_DATA_FUNCTION_CTOR",
)
FLAGS = ("isImpredicative", "isK", "hasProjections", "hasEta", "hasLargeElim")

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def get(out, name):
    aid, expected = ARTIFACTS[name]
    raw = subprocess.check_output(["gh", "api", f"repos/{ARENA}/actions/artifacts/{aid}/zip"])
    assert digest(raw) == expected, (name, digest(raw), expected)
    p = out / (name + ".zip")
    p.write_bytes(raw)
    return p

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--checker", type=Path, required=True)
    p.add_argument("--flags", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    run = json.loads(subprocess.check_output(
        ["gh", "api", f"repos/{ARENA}/actions/runs/{RUN}"]))
    assert run["head_sha"] == REV
    write(a.out / "upstream-run.json", {k:run[k] for k in ("id","head_sha","conclusion","html_url")})
    with zipfile.ZipFile(get(a.out, "results")) as z:
        manifests = []
        for n in z.namelist():
            if n.endswith(".json"):
                d = json.loads(z.read(n))
                if isinstance(d, dict) and isinstance(d.get("tests"), list):
                    manifests.append(d)
    assert len(manifests) == 1
    data = manifests[0]
    assert data["meta"]["git_revision"] == REV
    tests = {t["name"]:t for t in data["tests"]}
    assert len(tests) == len(data["tests"])
    write(a.out / "official-results.json", data)
    with zipfile.ZipFile(get(a.out, "tarball")) as z:
        names = [n for n in z.namelist() if n.endswith("lean-arena-tests.tar.gz")]
        assert len(names) == 1, names
        tarpath = a.out / "tests.tar.gz"
        tarpath.write_bytes(z.read(names[0]))
    flags = json.loads(a.flags.read_text())["flags"]
    assert len(flags) == 24 and set(flags.values()) == {"1"}
    env = {k:v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
    env.update(flags)
    env.update({f"NUCLEUS_EXPERIMENTAL_{k}":"1" for k in EXTRAS})
    env["NUCLEUS_C234_CAPTURE_FALLBACK_RESERVE"] = "1"
    env["NUCLEUS_TRACE_PARSE_ERROR"] = "1"
    write(a.out / "checker-identity.json", {"binary_sha256":digest(a.checker.read_bytes()),
          "flags":{k:v for k,v in env.items() if k.startswith("NUCLEUS_")}})
    rows = []
    seen = set()
    with tarfile.open(tarpath, "r:gz") as tf:
        for m in tf:
            if not m.isfile():
                continue
            parts = Path(m.name).parts
            assert len(parts) >= 2 and parts[0] in ("good","bad")
            assert all(x not in ("", ".", "..") for x in parts)
            assert m.name.endswith(".ndjson")
            name = "/".join(parts[1:])[:-7]
            assert name in tests and name not in seen, name
            seen.add(name)
            expected = "accept" if parts[0] == "good" else "reject"
            raw = tf.extractfile(m).read()
            meta = tests[name]
            assert meta["outcome"] == expected and len(raw) == meta["size"]
            assert digest(raw) == meta["sha256"], name
            header = json.loads(raw.split(b"\n",1)[0])
            version = header.get("meta",{}).get("format",{}).get("version")
            field_counts = collections.Counter()
            flag_values = collections.Counter()
            if version == "3.2.0":
                for line in raw.splitlines()[1:]:
                    obj = json.loads(line)
                    for typ in obj.get("inductive",{}).get("types",[]):
                        for k in FLAGS:
                            if k in typ:
                                field_counts[k] += 1
                                flag_values[f"{k}={typ[k]}"] += 1
            started = time.monotonic()
            try:
                proc = subprocess.run([str(a.checker)], input=raw, env=env,
                    capture_output=True, timeout=min(int(meta.get("timeout") or 120), 120))
                rc = proc.returncode
                stderr = proc.stderr.decode(errors="replace")
            except subprocess.TimeoutExpired as exc:
                rc = None
                stderr = (exc.stderr or b"").decode(errors="replace")
            unsupported = rc == 3 and "unsupported export format" in stderr
            outcome = "unsupported" if unsupported else {0:"accept",1:"reject",2:"unknown",3:"error",None:"timeout"}.get(rc,"error")
            row = {"name":name,"sha256":digest(raw),"expected":expected,
                   "format":version,"raw_exit":rc,"observed":outcome,
                   "flag_counts":dict(field_counts),"flag_values":dict(flag_values),
                   "elapsed_s":round(time.monotonic()-started,4),
                   "diagnostic":stderr[-900:]}
            rows.append(row)
            print("BETA_CASE",json.dumps(row,sort_keys=True),flush=True)
            write(a.out/"beta-rows.json",rows)
    small = {n for n,t in tests.items() if t.get("outcome") in ("accept","reject")
             and t.get("size",0) <= 10 * 1024 * 1024}
    assert seen == small, (sorted(small-seen), sorted(seen-small))
    assert any(r["format"] == "3.2.0" for r in rows)
    wrong = [r["name"] for r in rows if r["observed"] in ("accept","reject") and r["observed"] != r["expected"]]
    summary = {"scope":"unchanged checker compatibility baseline only",
               "test_count":len(rows),
               "format_counts":dict(collections.Counter(str(r["format"]) for r in rows)),
               "outcomes":dict(collections.Counter(r["observed"] for r in rows)),
               "wrong_decisive":wrong,
               "format_outcome_counts":dict(collections.Counter(str(r["format"])+":"+r["observed"] for r in rows)),
               "uncovered_prescribed":sorted(n for n,t in tests.items() if t.get("outcome") in ("accept","reject") and n not in seen),
               "release_qualified":False}
    write(a.out/"beta-summary.json",summary)
    print("BETA_SUMMARY",json.dumps(summary,sort_keys=True),flush=True)
    assert not wrong, "Newly observed wrong decisive verdict"

if __name__ == "__main__":
    main()
