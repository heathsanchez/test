#!/usr/bin/env python3
"""Finite qualification of retention-policy genesis and revision.

The learner exhaustively synthesizes a set-valued policy from a frozen DSL.
Only completed streams provide authority. Deployment sees observables, never
future value. All candidate/stream verifier evaluations are charged.
"""
import hashlib, itertools, json, pathlib, random

ROOT = pathlib.Path(__file__).parent
CAPACITY = 4
WEIGHTS = (-1, 0, 1)
FEATURES = ("recent", "scope", "breadth", "persistence", "amort", "depth", "genesis", "support")
NODES = ("a", "b", "c", "d", "e", "f", "g", "h")
DEPS = {"a": (), "b": (), "c": ("a",), "d": ("b",), "e": ("a", "b"), "f": ("c",), "g": (), "h": ("d",)}

def closure(xs):
    out = set(xs)
    changed = True
    while changed:
        changed = False
        for x in tuple(out):
            for d in DEPS[x]:
                if d not in out: out.add(d); changed = True
    return frozenset(out)

SUBSETS = tuple(sorted({closure(xs) for k in range(CAPACITY + 1)
                        for xs in itertools.combinations(NODES, k)
                        if len(closure(xs)) <= CAPACITY}, key=lambda s:(len(s), tuple(sorted(s)))))

def make_stream(seed, regime):
    r = random.Random(seed)
    obs = {}
    for i,n in enumerate(NODES):
        obs[n] = {
            "recent": r.randint(0,4), "scope": r.randint(1,4), "breadth": r.randint(1,5),
            "persistence": r.randint(0,5), "amort": r.randint(-2,5), "depth": 0 if not DEPS[n] else (2 if n in "fh" else 1),
            "genesis": r.randint(1,5)
        }
    # Frozen external authority. Regime 0 rewards broad, scoped, recent supported
    # sets; regime 1 makes persistence and low genesis decisive.
    if regime == 0:
        true_w = (2,3,3,1,1,-1,-1,3)
    else:
        true_w = (-1,0,1,4,-2,0,-3,-2)
    values = {s: 180 * raw_score(true_w, s, obs) + r.randint(-15,15) for s in SUBSETS}
    best = max(values.values()); costs = {s: 5000 + best - v for s,v in values.items()}
    return {"seed":seed,"regime":regime,"obs":obs,"costs":costs}

def raw_score(w, subset, obs):
    totals = [sum(obs[n][f] for n in subset) for f in FEATURES[:-1]]
    support = sum(1 for n in subset for d in DEPS[n] if d in subset)
    return sum(a*b for a,b in zip(w, totals + [support]))

def choose(w, stream):
    return max(SUBSETS, key=lambda s:(raw_score(w,s,stream["obs"]), tuple(sorted(s))))

def scalar(feature, stream):
    idx = FEATURES.index(feature)
    w = tuple(1 if i == idx else 0 for i in range(len(FEATURES)))
    return choose(w,stream)

def synthesize(streams):
    best = None; calls = 0
    for w in itertools.product(WEIGHTS, repeat=len(FEATURES)):
        cost = 0
        for st in streams:
            cost += st["costs"][choose(w,st)]; calls += 1
        key = (cost, sum(abs(x) for x in w), w)
        if best is None or key < best[0]: best = (key,w)
    return best[1], calls, best[0][0]

def evaluate(policy, streams):
    return sum(st["costs"][policy(st)] for st in streams)

def main():
    train = [make_stream(x,0) for x in range(11,15)]
    held = [make_stream(x,0) for x in range(101,121)]
    shift_cal = [make_stream(x,1) for x in range(201,205)]
    shift_test = [make_stream(x,1) for x in range(301,321)]
    p1, genesis_calls, train_cost = synthesize(train)
    p2, revision_calls, revision_train_cost = synthesize(shift_cal)
    generated1 = lambda st: choose(p1,st)
    generated2 = lambda st: choose(p2,st)
    controls = {f"scalar_{f}":(lambda st,f=f:scalar(f,st)) for f in FEATURES[:-1]}
    controls["hand_geometry"] = lambda st: choose((1,1,1,1,1,-1,-1,1),st)
    controls["amortization"] = lambda st: scalar("amort",st)
    controls["sham"] = lambda st: SUBSETS[int(hashlib.sha256(str(st["seed"]).encode()).hexdigest()[:8],16)%len(SUBSETS)]
    oracle = lambda st:min(SUBSETS,key=lambda s:st["costs"][s])

    held_cost = evaluate(generated1,held)
    totals = {k:evaluate(v,held) for k,v in controls.items()}
    totals.update({"generated_policy":held_cost,"oracle":evaluate(oracle,held)})
    shifted_old = evaluate(generated1,shift_test)
    shifted_new = evaluate(generated2,shift_test)
    # Policy residual is externally certified on completed calibration streams.
    cal_old=evaluate(generated1,shift_cal); cal_new=evaluate(generated2,shift_cal)
    policy_residual = cal_new < cal_old
    # Full economic accounting. Genesis/revision calls are charged once.
    generated_cumulative = genesis_calls + held_cost + revision_calls + shifted_new
    old_policy_cumulative = genesis_calls + held_cost + shifted_old
    scalar_best = min(totals[k] for k in totals if k.startswith("scalar_"))
    # Ablating revision means replaying the frozen old policy after the shift.
    revision_ablation_penalty = shifted_old-shifted_new
    distinct = p1 != p2 and any(choose(p1,s)!=choose(p2,s) for s in shift_test)
    gates = {
      "policy_constructed_from_frozen_grammar": p1 in itertools.product(WEIGHTS,repeat=len(FEATURES)),
      "dependency_closed_budgeted_outputs": all(len(choose(p1,s))<=CAPACITY and closure(choose(p1,s))==choose(p1,s) for s in held),
      "prospective_beats_every_scalar": held_cost < scalar_best,
      "prospective_beats_hand_geometry": held_cost < totals["hand_geometry"],
      "non_oracle": held_cost > totals["oracle"],
      "verified_policy_residual": policy_residual,
      "revision_is_behaviorally_distinct": distinct,
      "revision_improves_untouched_suffix": shifted_new < shifted_old,
      "revision_ablation_restores_old_cost": revision_ablation_penalty > 0,
      "full_construction_cost_charged": genesis_calls==revision_calls==len(train)*(len(WEIGHTS)**len(FEATURES)),
    }
    snap={"capacity":CAPACITY,"features":FEATURES,"weights":WEIGHTS,"dependencies":DEPS,"subset_count":len(SUBSETS),
          "train_seeds":[s["seed"] for s in train],"heldout_seeds":[s["seed"] for s in held],
          "revision_seeds":[s["seed"] for s in shift_cal],"post_revision_seeds":[s["seed"] for s in shift_test],
          "authority":"completed-stream fully charged reconstruction cost","policy_information":"present observables and dependencies only"}
    enc=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"),default=list)
    ev={"verdict":"VERIFIED_RETENTION_POLICY_GENESIS_AND_REVISION" if all(gates.values()) else "NEGATIVE_OR_PARTIAL",
        "classification":"FINITE_CONSTRUCTED_SET_VALUED_POLICY_QUALIFICATION","policy_1":dict(zip(FEATURES,p1)),"policy_2":dict(zip(FEATURES,p2)),
        "grammar_programs":len(WEIGHTS)**len(FEATURES),"feasible_subsets":len(SUBSETS),"genesis_verifier_calls":genesis_calls,
        "revision_verifier_calls":revision_calls,"training_authority_cost":train_cost,"revision_training_authority_cost":revision_train_cost,
        "heldout_totals":totals,"shift":{"old_policy":shifted_old,"revised_policy":shifted_new,"calibration_old":cal_old,"calibration_new":cal_new,
        "revision_ablation_penalty":revision_ablation_penalty},"fully_charged_cumulative":{"generated_and_revised":generated_cumulative,"no_revision":old_policy_cumulative},
        "gates":gates,"snapshot_digest":hashlib.sha256(enc(snap).encode()).hexdigest(),
        "not_established":["natural-world policy learning","open-ended policy grammar","global optimality","unbounded self-modification"]}
    out=ROOT/"results";out.mkdir(exist_ok=True)
    (out/"snapshot.json").write_text(json.dumps(snap,indent=2,default=list)+"\n")
    (out/"evidence.json").write_text(json.dumps(ev,indent=2)+"\n")
    print(json.dumps(ev,indent=2))

if __name__=="__main__": main()
