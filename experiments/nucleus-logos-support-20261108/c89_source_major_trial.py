"""Bounded original-Arena source-argument census for pending qualified recursors."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

from c88_exact_pending_trial import parse_c88


def parse_c89(lines):
    records = [json.loads(line.removeprefix("NUCLEUS_C89_MAJOR_SOURCE:"))
               for line in lines if line.startswith("NUCLEUS_C89_MAJOR_SOURCE:")]
    assert records, "C89 source-argument census missing"
    assert len({row["seq"] for row in records}) == len(records), "C89 duplicate sequence"
    for row in records:
        for name in ("seq", "major_parents", "unique_source_exprs",
                     "unique_major_closures", "major_closure_repeats", "missing_major_source"):
            assert type(row.get(name)) is int and row[name] >= 0, name
        groups = row.get("source_expr_groups")
        assert isinstance(groups, list) and all(
            isinstance(group, list) and len(group) == 2
            and all(type(value) is int and value >= 0 for value in group)
            and group[1] > 0 for group in groups), "source-ExprId histogram shape"
        assert len(groups) == row["unique_source_exprs"]
        assert len({group[0] for group in groups}) == len(groups)
        assert groups == sorted(groups, key=lambda x: (-x[1], x[0]))
        assert sum(group[1] for group in groups) + row["missing_major_source"] == row["major_parents"]
        assert (row["unique_major_closures"] + row["major_closure_repeats"]
                + row["missing_major_source"] == row["major_parents"])
    return sorted(records, key=lambda x:x["seq"])


def run_trial():
    flags=json.loads(Path("base/flags.json").read_text())
    assert len(flags)==24 and set(flags.values())=={"1"}
    previous=json.loads(Path("reports/c88.json").read_text())
    frozen=[
        ("magma-list-pair-n7",8837,"abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"),
        ("magma-list-pair-n21",8827,"b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84"),
    ]
    rows=[]
    for case, expr, digest in frozen:
        src=Path(f"arena207/good/perf/{case}.ndjson").read_bytes()
        assert hashlib.sha256(src).hexdigest()==digest
        prior=next(row for row in previous["rows"] if row["case"]==case)
        env={key:value for key,value in os.environ.items() if not key.startswith("NUCLEUS_")}
        env.update(flags)
        env.update({
            "NUCLEUS_ASSURANCE_SOURCE_OWNED_PROBE":"1",
            "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR":str(expr),
            "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE":"1",
            "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR":"1",
            "NUCLEUS_C84_EXACT_CLOSURE_CENSUS":"1",
            "NUCLEUS_C85_COMPLETION_CENSUS":"1",
            "NUCLEUS_DIAGNOSTIC_C48_SOURCE_TRANSITIONS":"1",
            "NUCLEUS_DIAGNOSTIC_C50_STATE_LOSS":"1",
            "NUCLEUS_C87_PENDING_MAJOR":"1",
            "NUCLEUS_C88_EXACT_PENDING":"1",
            "NUCLEUS_C89_MAJOR_SOURCE":"1",
        })
        proc=subprocess.run(["candidate/nucleus-diagnostic","262144"],
                            input=src,capture_output=True,env=env,timeout=180)
        assert proc.returncode==2,(case,"original-verdict-changed",proc.returncode)
        lines=proc.stderr.decode(errors="replace").splitlines()
        c88=parse_c88(lines)
        assert c88==prior["records"], (case,"C88-equivalence-failed")
        records=parse_c89(lines)
        assert [record["seq"] for record in records]==[record["seq"] for record in c88]
        for prev,now in zip(c88,records):
            assert prev["major_parents"]==now["major_parents"]
        Path(f"reports/c89-{case}.stderr").write_bytes(proc.stderr)
        maximum=max(records,key=lambda row:row["major_parents"])
        rows.append({"case":case,"original_sha256":digest,"verdict":"UNKNOWN",
                     "c88_exact_pending_unchanged":True,"records":records,
                     "max_pending":maximum,"stderr_sha256":hashlib.sha256(proc.stderr).hexdigest()})
        print("C89_ORIGINAL_CASE="+json.dumps({"case":case,"max_pending":maximum,"verdict":"UNKNOWN"},sort_keys=True),flush=True)
    result={"experiment":"C89 source ExprId census of distinct unfinished recursor Major arguments",
            "standard_budget":262144,"selected_C58_source_unchanged":True,
            "no_accept_or_proof_rule_changed":True,"original_standard_accepts":0,
            "full_403_protected_corpus_not_run":True,"rows":rows}
    Path("reports/c89.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")


if __name__=="__main__":
    run_trial()
