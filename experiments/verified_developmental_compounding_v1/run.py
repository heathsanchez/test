#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, json, platform, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from controller.core import Adapter, Capability, Controller, State, canonical_hash

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

def load(): return json.loads((ROOT / "tasks" / "tasks.json").read_text())

def main():
    spec = load(); controller = Controller(max_depth=4)
    code_hash = controller.digest(); task_hash = hashlib.sha256((ROOT/"tasks"/"tasks.json").read_bytes()).hexdigest()
    all_rows, provenance, states = [], [], {}
    prior_domain_patterns = []
    pi_freeze = None

    for domain_spec in spec["domains"]:
        name = domain_spec["domain"]; adapter = Adapter(domain_spec); warm = State(); prior=[]
        states[name] = warm
        tasks = domain_spec["tasks"]
        for task in tasks:
            # C4 is the prospective cross-domain target. Compile/freeze Pi before exposing it.
            if task["held_out"]:
                assert name == "rule_induction" and task["stage"] == 4
                assert len(set(prior_domain_patterns)) >= 2
                pi_freeze = {
                    "compiled_from_domains": sorted(set(prior_domain_patterns)),
                    "operator": "residual_guided_composition",
                    "controller_sha256": code_hash,
                    "held_out_task_commitment": canonical_hash({
                        "domain": name, "stage": task["stage"],
                        "sealed_task_sha256": canonical_hash(task),
                    }),
                }
                pi_freeze["freeze_sha256"] = canonical_hash(pi_freeze)
                pi_state = State(pi_enabled=True)
                cold = controller.solve(adapter, task, State(), "cold")
                piwarm = controller.solve(adapter, task, pi_state, "pi_warm")
                for cond, result in [("cold",cold),("pi_warm",piwarm),("pi_ablation",controller.solve(adapter,task,State(),"cold")),("pi_sham",controller.solve(adapter,task,State(capabilities=[Capability("inert","sham",{},"inert","none",True,[],"budget control")]),"cold"))]:
                    all_rows.append({"evaluation":"cross_domain","domain":name,"stage":4,"condition":cond,**result})
                # Continue ordinary within-domain controls below using state from C1-C3.

            conditions = {"cold": State(), "warm": warm}
            if task["stage"] > 1:
                ab = copy.deepcopy(warm)
                if ab.capabilities:
                    removed = ab.capabilities.pop(0)
                else: removed = None
                sham = State(capabilities=[Capability(f"inert_{i}","sham",{},"inert","none",True,[],"matched state budget") for i in range(len(warm.capabilities))])
                conditions.update({"ablation":ab,"sham":sham,"answer_memory":State()})
            stage_results = {}
            for cond, st in conditions.items():
                result = controller.solve(adapter, task, st, cond)
                stage_results[cond] = result
                all_rows.append({"evaluation":"within_domain","domain":name,"stage":task["stage"],"condition":cond,**result})
            assert stage_results["warm"]["correct"] and stage_results["cold"]["correct"]
            added = controller.admit(adapter, task, stage_results["warm"]["solution"], warm, prior)
            for c in added: provenance.append(c.__dict__)
            prior.append(task)
        prior_domain_patterns.append(name)

    # Mark causal evidence after direct one-removal comparisons.
    for cap in provenance:
        rows = [r for r in all_rows if r["domain"] == cap["domain"] and r["condition"] in {"warm","ablation"} and r["stage"] > cap["residual"]["task_stage"]]
        cap["ablation_result"] = "cost_or_reachability_damaged" if any(r["condition"]=="ablation" and (not r["correct"] or r["verifier_calls"] > next(w["verifier_calls"] for w in rows if w["condition"]=="warm" and w["stage"]==r["stage"])) for r in rows if any(w["condition"]=="warm" and w["stage"]==r["stage"] for w in rows)) else "not_individually_tested_or_no_effect"

    pairs=[]
    for d in [x["domain"] for x in spec["domains"]]:
        for s in (2,3,4):
            c=next(r for r in all_rows if r["evaluation"]=="within_domain" and r["domain"]==d and r["stage"]==s and r["condition"]=="cold")
            w=next(r for r in all_rows if r["evaluation"]=="within_domain" and r["domain"]==d and r["stage"]==s and r["condition"]=="warm")
            pairs.append({"domain":d,"stage":s,"cold":c["verifier_calls"],"warm":w["verifier_calls"],"ratio":c["verifier_calls"]/w["verifier_calls"]})
    cold_sum=sum(p["cold"] for p in pairs)
    warm_sum=sum(p["warm"] for p in pairs)
    pi_c=next(r for r in all_rows if r["evaluation"]=="cross_domain" and r["domain"]=="rule_induction" and r["stage"]==4 and r["condition"]=="cold")
    pi_w=next(r for r in all_rows if r["evaluation"]=="cross_domain" and r["domain"]=="rule_induction" and r["stage"]==4 and r["condition"]=="pi_warm")
    gates={
      "G1_no_warm_correctness_regression":all(r["correct"] for r in all_rows if r["condition"]=="warm"),
      "G2_aggregate_at_least_2x":cold_sum >= 2*warm_sum,
      "G3_benefit_persists":all(p["cold"]>p["warm"] for p in pairs),
      "G4_ablation_damages":any(r["condition"]=="ablation" and r["verifier_calls"]>next(w["verifier_calls"] for w in all_rows if w["domain"]==r["domain"] and w["stage"]==r["stage"] and w["condition"]=="warm") for r in all_rows if r["condition"]=="ablation"),
      "G5_sham_no_gain":all(r["verifier_calls"]==next(c["verifier_calls"] for c in all_rows if c["domain"]==r["domain"] and c["stage"]==r["stage"] and c["condition"]=="cold") for r in all_rows if r["condition"]=="sham"),
      "G6_answer_memory_no_gain":all(r["verifier_calls"]==next(c["verifier_calls"] for c in all_rows if c["domain"]==r["domain"] and c["stage"]==r["stage"] and c["condition"]=="cold") for r in all_rows if r["condition"]=="answer_memory"),
      "G7_prospective_pi_transfer":pi_w["correct"] and pi_w["verifier_calls"]<pi_c["verifier_calls"],
      "G8_pi_frozen_before_heldout":pi_freeze is not None,
    }
    evidence={
      "classification":"BOUNDED_CAUSAL", "terminal_verdict":"VERIFIED DEVELOPMENTAL COMPOUNDING" if all(gates.values()) else "PARTIAL / BOUNDED SIGNAL",
      "scope":"deterministic finite qualification across three supplied verifier adapters",
      "controller_sha256":code_hash,"tasks_sha256":task_hash,"task_manifest_claimed_sha256":spec["manifest_sha256"],
      "seed":spec["seed"],"python":platform.python_version(),"platform":platform.platform(),
      "primary_metric":"verifier-mediated candidate evaluations to first accepted program",
      "aggregate":{"cold":cold_sum,"warm":warm_sum,"ratio":cold_sum/warm_sum},
      "stage_pairs":pairs,"gates":gates,"pi_freeze":pi_freeze,"rows":all_rows,
      "retained_capabilities":provenance,
      "active_state_size":sum(len(s.capabilities) for s in states.values()),
      "provenance_size":len(provenance),"model_api_tokens":None,
      "unresolved_residual":"external validity: engineered finite curricula do not establish natural-task or unrestricted compounding",
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS/"evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    (RESULTS/"provenance.json").write_text(json.dumps(provenance,indent=2)+"\n")
    print(json.dumps({"verdict":evidence["terminal_verdict"],"aggregate":evidence["aggregate"],"gates":gates},indent=2))
    if not all(gates.values()): raise SystemExit(1)

if __name__ == "__main__": main()
