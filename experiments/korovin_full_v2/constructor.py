from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from collections import defaultdict, Counter

# IMPORTANT:
# This module is the blind constructor.  CI scans it for target-specific
# mathematical vocabulary and known object names.  It receives only opaque
# programs, token strings, and observable input/output behavior.

@dataclass(frozen=True)
class Feature:
    kind: str
    arg: object

@dataclass
class Candidate:
    features: tuple[Feature, ...]
    key_to_rows: dict
    predictive_conflicts: int
    transition_conflicts: int
    state_count: int
    description_cost: int
    score: tuple

def _syntax_feature(word, feat):
    if feat.kind == "length":
        return len(word)
    if feat.kind == "first":
        return word[0] if word else "<empty>"
    if feat.kind == "last":
        return word[-1] if word else "<empty>"
    if feat.kind == "count":
        return word.count(feat.arg)
    if feat.kind == "suffix":
        k = int(feat.arg)
        return word[-k:] if len(word) >= k else word
    if feat.kind == "prefix":
        k = int(feat.arg)
        return word[:k]
    raise KeyError(feat.kind)

def _feature_value(word, output, feat):
    if feat.kind in {"length","first","last","count","suffix","prefix"}:
        return _syntax_feature(word, feat)
    if feat.kind == "probe":
        return output[int(feat.arg)]
    raise KeyError(feat.kind)

def make_key(word, output, features):
    return tuple(_feature_value(word, output, f) for f in features)

def _evaluate_candidate(train_rows, tokens, features):
    buckets = defaultdict(list)
    for w,out in train_rows:
        buckets[make_key(w,out,features)].append((w,out))

    predictive = 0
    for vals in buckets.values():
        behaviors = {out for _,out in vals}
        predictive += max(0, len(behaviors)-1)

    lookup = {w: out for w,out in train_rows}
    transition_targets = defaultdict(set)
    for w,out in train_rows:
        src = make_key(w,out,features)
        for tok in tokens:
            w2 = w + (tok,)
            if w2 in lookup:
                dst = make_key(w2,lookup[w2],features)
                transition_targets[(src,tok)].add(dst)
    transition = sum(max(0,len(v)-1) for v in transition_targets.values())

    cost = sum(1 if f.kind in {"length","first","last"} else 2 for f in features)
    states = len(buckets)
    score = (predictive + transition, states, cost, len(features))
    return Candidate(tuple(features), dict(buckets), predictive, transition, states, cost, score)

def _feature_library(train_rows, tokens, n_points):
    feats = [
        Feature("length",None),
        Feature("first",None),
        Feature("last",None),
        Feature("prefix",1),
        Feature("suffix",1),
        Feature("prefix",2),
        Feature("suffix",2),
    ]
    feats += [Feature("count",t) for t in tokens]
    feats += [Feature("probe",i) for i in range(n_points)]
    return feats

def search_representation(train_rows, tokens, n_points, max_width=4):
    """Residual-guided search over a generic feature language."""
    library = _feature_library(train_rows, tokens, n_points)
    history = []
    winner = None

    for width in range(1, max_width+1):
        level = []
        for combo in combinations(library, width):
            cand = _evaluate_candidate(train_rows, tokens, combo)
            level.append(cand)
        level.sort(key=lambda c:c.score)
        best = level[0]
        history.append({
            "width": width,
            "best_features": [(f.kind,f.arg) for f in best.features],
            "best_predictive_conflicts": best.predictive_conflicts,
            "best_transition_conflicts": best.transition_conflicts,
            "best_state_count": best.state_count,
            "best_score": best.score,
            "zero_conflict_candidates": sum(
                c.predictive_conflicts==0 and c.transition_conflicts==0 for c in level
            ),
        })
        exact = [c for c in level if c.predictive_conflicts==0 and c.transition_conflicts==0]
        if exact:
            exact.sort(key=lambda c:(c.state_count,c.description_cost,len(c.features),
                                     tuple((f.kind,str(f.arg)) for f in c.features)))
            winner = exact[0]
            break

    if winner is None:
        raise RuntimeError("representation search exhausted without a deterministic state description")

    keys = sorted(winner.key_to_rows, key=repr)
    sid = {k:i for i,k in enumerate(keys)}
    rep = {}
    behavior = {}
    for k,vals in winner.key_to_rows.items():
        vals = sorted(vals,key=lambda x:(len(x[0]),x[0]))
        rep[sid[k]] = vals[0][0]
        behavior[sid[k]] = vals[0][1]

    lookup = {w:o for w,o in train_rows}
    transitions = {}
    transition_missing = []
    for s,w in rep.items():
        for tok in tokens:
            w2=w+(tok,)
            if w2 not in lookup:
                transition_missing.append((s,tok,"training_extension_missing"))
                continue
            k2=make_key(w2,lookup[w2],winner.features)
            if k2 not in sid:
                transition_missing.append((s,tok,"state_missing"))
                continue
            transitions[(s,tok)] = sid[k2]

    empty = ()
    if empty not in lookup:
        raise RuntimeError("empty program missing")
    start_key=make_key(empty,lookup[empty],winner.features)
    start_state=sid[start_key]

    return {
        "selected_features":[{"kind":f.kind,"arg":f.arg} for f in winner.features],
        "search_history":history,
        "state_count":len(keys),
        "state_keys":keys,
        "representatives":rep,
        "behaviors":behavior,
        "transitions":transitions,
        "transition_missing":transition_missing,
        "start_state":start_state,
    }

def execute_state_machine(model, word):
    s=model["start_state"]
    for tok in word:
        k=(s,tok)
        if k not in model["transitions"]:
            return None
        s=model["transitions"][k]
    return s
