#!/usr/bin/env python3
"""Construct a label-blind agent input view from frozen historical evidence.

This tool fixes dataset answer leakage; it does not create an independently
hidden benchmark. A fair, equally informed exact-match baseline is included.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runner

HERE=Path(__file__).resolve().parent
EXPECTED_LEGACY_SHA="e79ccaf52f817379306713de8b7628a25a38d3b6457146a8d6913edf33972c95"
DOMAIN=b"mathgraph-cashtrack-blind-v2\x00"

def opaque(packet):
    return hashlib.sha256(DOMAIN+runner.canonical(packet)).hexdigest()[:24]

def pack_lines(records):
    return b"".join(runner.canonical(r)+b"\n" for r in records)

def independent_expected(c):
    """An equally informed exact-authority baseline, not the MathGraph admit()."""
    return {
        "case_id":c["id"],"repo":c["repo"],"subject":c["subject"],
        "ci_run_id":c["run_id"],"ci_job":c["job"],
        "ci_conclusion":"success","claim":c["claim"],
        "observed_phases":list(c["required_phases"]),
        "source_active":True,"evidence_url":c["citation"],
    }

def compare_exact(packet, cases):
    c=cases.get(packet.get("case_id"))
    return bool(c and packet==independent_expected(c))

def baseline_green(packet,cases):
    return packet.get("ci_conclusion")=="success"

def baseline_unknown(packet,cases):
    return False

def score(examples,cases,func):
    tp=fp=fn=tn=0
    for row in examples:
        got=bool(func(row["packet"],cases))
        positive=row["admissible"]
        if positive and got:tp+=1
        elif positive and not got:fn+=1
        elif not positive and got:fp+=1
        else:tn+=1
    return {"true_admissions":tp,"false_admissions":fp,
            "missed_true":fn,"correct_refusals":tn,
            "sensitivity":tp/(tp+fn),"specificity":tn/(tn+fp),
            "balanced_accuracy":(tp/(tp+fn)+tn/(tn+fp))/2}

def construct():
    raw=runner.load_authorities()
    cases={c["id"]:c for c in raw["cases"]}
    original=runner.build_examples(raw)
    legacy=pack_lines(original)
    legacy_sha=hashlib.sha256(legacy).hexdigest()
    if legacy_sha!=EXPECTED_LEGACY_SHA:
        raise RuntimeError("The exact original labeled archive has changed; refuse silent refreeze")
    cases_in=[];gold=[];sample_ids=set()
    for row in original:
        packet=row["packet"]
        sid=opaque(packet)
        if sid in sample_ids:raise RuntimeError("Opaque sample ID collision")
        sample_ids.add(sid)
        item={"sample_id":sid,"packet":packet}
        if set(item)!={"sample_id","packet"} or not re.fullmatch("[0-9a-f]{24}",sid):
            raise RuntimeError("Agent input format leak")
        if any(key in item for key in ("admissible","control","source_case","id")):
            raise RuntimeError("Explicit answer label in model-facing input")
        cases_in.append(item)
        gold.append({"sample_id":sid,"admissible":row["admissible"],
                     "source_case":row["source_case"],"control":row["control"]})
    if len(original)!=56 or len(cases_in)!=56 or len(gold)!=56:
        raise RuntimeError("Incomplete preservation")
    if sum(x["admissible"] for x in gold)!=7:raise RuntimeError("Positive count mismatch")
    if any(k in r["sample_id"] for r in gold for k in ("original_scoped","wrong_ci_run","false","true")):
        raise RuntimeError("Control leaked into opaque identity")
    items={r["sample_id"]:r["packet"] for r in cases_in}
    for key in gold:
        if key["sample_id"] not in items:raise RuntimeError("Gold input mismatch")
        if compare_exact(items[key["sample_id"]],cases)!=key["admissible"]:
            raise RuntimeError("Gold/equal-information source mismatch")
    scores={
        "accept_green_ci":score(original,cases,baseline_green),
        "always_unknown":score(original,cases,baseline_unknown),
        "independent_equal_information_exact_baseline":score(original,cases,compare_exact),
        "mathgraph_typed_admission":score(original,cases,runner.admit),
    }
    assert scores["independent_equal_information_exact_baseline"]==scores["mathgraph_typed_admission"]
    assert scores["accept_green_ci"]["false_admissions"]==49
    assert scores["always_unknown"]["missed_true"]==7
    scores["direct_leak_baselines"]={
        "literal_admissible_field_correct":sum(bool(x["admissible"])==bool(x["admissible"]) for x in original),
        "control_name_correct":sum((x["control"]=="original_scoped")==x["admissible"] for x in original),
        "visible_id_suffix_correct":sum(x["id"].endswith("::original_scoped")==x["admissible"] for x in original),
    }
    assert all(v==56 for v in scores["direct_leak_baselines"].values())
    input_bytes=pack_lines(cases_in)
    gold_bytes=pack_lines(gold)
    report={
        "status":"WARRANTED_BOUNDED_LEAKAGE_REMOVED_WITH_EQUAL_INFO_BASELINE_TIE",
        "existing_legacy_labeled_corpus_sha256":legacy_sha,
        "original_case_count":7,
        "original_falsifiers":49,
        "agent_input_sha256":hashlib.sha256(input_bytes).hexdigest(),
        "separate_gold_sha256":hashlib.sha256(gold_bytes).hexdigest(),
        "input_fields":["sample_id","packet"],
        "visible_id_contains_control_label":False,
        "new_independent_model_output":False,
        "new_hidden_eval_data":False,
        "matched_frontier_coding_agent_run":False,
        "inference_qualification":"none",
        "limitations":[
            "Labels are separate outputs but publicly archived; not a confidential hidden test",
            "Negatives are researcher constructed using the declared accepted packet",
            "Both exact-authority validators have the same sufficient information and tie",
            "Full raw CI artifact authentication and inference on unseen coding-agent output remain outside this experiment",
        ],
        "methods":scores,
    }
    return input_bytes,gold_bytes,pack_lines(original),runner.canonical(report)+b"\n"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default=str(HERE/"out_blind_v2"))
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    ip,gold,legacy,metrics=construct()
    if args.self_test:
        assert construct()==(ip,gold,legacy,metrics)
        print("PASS: 56 agent inputs with no answer labels; 56 separate gold labels; independent exact-authority tie")
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    (out/"agent_inputs.jsonl").write_bytes(ip)
    (out/"gold_labels.jsonl").write_bytes(gold)
    (out/"legacy_labeled_training_only.jsonl").write_bytes(legacy)
    (out/"metrics.json").write_bytes(metrics)
    (out/"README.md").write_text(
        "# Cash-track V2 split\n\n"
        "Use agent_inputs.jsonl by itself for agent input. Never mount gold_labels.jsonl "
        "or legacy_labeled_training_only.jsonl into the agent context if measuring "
        "decision accuracy. These files remain public and are not a hidden holdout.\n\n"
        "The historical 7 positives + 49 constructed negatives are NOT independent samples. "
        "The equally informed exact authority baseline TIES the MathGraph checker.\n",
        encoding="utf-8")
    print(metrics.decode())

if __name__=="__main__":
    main()
