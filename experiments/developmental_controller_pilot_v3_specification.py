#!/usr/bin/env python3
"""
Developmental controller pilot v3: ontology-free specification induction.

Protocol executed in the creating session:
1. A hidden Boolean causal rule was selected reproducibly from a frozen function family
   using seed 947261.
2. Training evidence was rendered in three heterogeneous domain vocabularies
   (kernel, SAIR, code). The model saw only the rendered training statements + labels
   and nine held-out statements without labels; it was not shown the hidden rule name.
3. Before held-out labels were revealed, the semantic synthesizer froze this induced
   specification:

      OUTCOME = 1 iff the identity/canonicality condition and the scope-validity
      condition disagree. The third 'required relation/witness present' dimension is
      observationally irrelevant to this outcome in the supplied evidence.

   Equivalently, after cross-domain alignment: y = identity XOR scope.
4. Frozen held-out predictions were:
      [1,0,0,0,0,1,1,1,1]
5. Only after that freeze were hidden held-out labels revealed.

This tests HISTORY -> cross-representation alignment -> latent specification ->
held-out prediction without supplying named obstruction classes to the synthesizer.
It remains a synthetic benchmark with author-supplied surface semantics; it does not
establish open-ended scientific representation invention.
"""
from __future__ import annotations
import json, random, itertools
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

SEED = 947261
FUNCTIONS = {
    "x_and_not_y": lambda x,y,z: int(bool(x) and not bool(y)),
    "x_xor_y": lambda x,y,z: int(bool(x) ^ bool(y)),
    "majority": lambda x,y,z: int((x+y+z)>=2),
    "x_and_z": lambda x,y,z: int(bool(x) and bool(z)),
    "y_or_z": lambda x,y,z: int(bool(y) or bool(z)),
    "exactly_one": lambda x,y,z: int((x+y+z)==1),
    "x_eq_y_and_z": lambda x,y,z: int((x==y) and bool(z)),
}

ALIASES = {
 "kernel": [
   ("closure key already canonical","identity not canonical"),
   ("scope invariant holds","scope counterexample exists"),
   ("producer exposes required witness","required witness absent")],
 "sair": [
   ("source-law separator is stable","source-law separator collapses"),
   ("constructor scope is lawful","constructor scope has counterexample"),
   ("witness grammar exposes bridge","bridge witness missing")],
 "code": [
   ("role abstraction preserves behavior","role alias collapses distinct behavior"),
   ("activation predicate is valid","activation predicate overfires"),
   ("AST exposes needed relation","needed relation is absent")],
}
HELD_ALIASES = {
 "database": [
   ("plan key is canonical across equivalent queries","equivalent queries receive divergent keys"),
   ("activation condition excludes harmful plans","activation condition admits a harmful plan"),
   ("optimizer state exposes required dependency","required dependency is not represented")],
 "compiler": [
   ("IR identity is canonical under harmless rewrites","harmless rewrites produce distinct identities"),
   ("optimization guard is valid on this regime","optimization guard has an in-scope counterexample"),
   ("IR exposes the dependency needed by the transform","transform dependency is hidden")],
 "planning": [
   ("state abstraction preserves relevant identity","relevant states are aliased incorrectly"),
   ("policy scope excludes harmful contexts","policy fires in a harmful context"),
   ("state includes the relation needed for the move","needed relation is absent from state")],
}
FROZEN_SPEC = "outcome iff identity/canonicality and scope-validity disagree; third dimension irrelevant"
FROZEN_PREDICTIONS = [1,0,0,0,0,1,1,1,1]

def render(alias, bits):
    return "; ".join(alias[i][0 if b else 1] for i,b in enumerate(bits))

def build():
    rng=random.Random(SEED)
    hidden_name=rng.choice(list(FUNCTIONS))
    f=FUNCTIONS[hidden_name]
    train=[]
    for dom,alias in ALIASES.items():
        pts=rng.sample(list(itertools.product([0,1], repeat=3)),5)
        for bits in pts:
            train.append({"domain":dom,"text":render(alias,bits),"label":f(*bits)})
    held=[]
    for dom,alias in HELD_ALIASES.items():
        pts=rng.sample(list(itertools.product([0,1], repeat=3)),3)
        for bits in pts:
            held.append({"domain":dom,"text":render(alias,bits),"label":f(*bits)})
    return hidden_name,train,held

def main():
    hidden_name,train,held=build()
    truth=[r["label"] for r in held]
    semantic_acc=sum(a==b for a,b in zip(FROZEN_PREDICTIONS,truth))/len(truth)

    # Fair lexical full-history baseline: supervised TF-IDF classifier gets all training labels.
    v=TfidfVectorizer(ngram_range=(1,2))
    X=v.fit_transform([r["text"] for r in train])
    H=v.transform([r["text"] for r in held])
    clf=LogisticRegression(random_state=0).fit(X,[r["label"] for r in train])
    lexical=clf.predict(H).astype(int).tolist()
    lexical_acc=sum(a==b for a,b in zip(lexical,truth))/len(truth)

    verdict={
      "frozen_semantic_predictions_exact": semantic_acc==1.0,
      "semantic_beats_full_history_lexical": semantic_acc>lexical_acc,
      "hidden_rule_not_named_in_frozen_spec": hidden_name not in FROZEN_SPEC,
    }
    payload={
      "protocol":"DEVELOPMENTAL_CONTROLLER_PILOT_V3_SPECIFICATION",
      "seed":SEED,
      "training_domains":list(ALIASES),
      "heldout_domains":list(HELD_ALIASES),
      "train_examples":len(train),
      "heldout_examples":len(held),
      "frozen_specification":FROZEN_SPEC,
      "frozen_predictions":FROZEN_PREDICTIONS,
      "heldout_truth":truth,
      "semantic_accuracy":semantic_acc,
      "lexical_predictions":lexical,
      "lexical_accuracy":lexical_acc,
      "revealed_hidden_rule_after_freeze":hidden_name,
      "verdict":verdict,
      "all_gates_pass":all(verdict.values()),
      "claim_boundary":"Synthetic ontology-free specification induction across heterogeneous surface vocabularies. The benchmark author supplies the three latent semantic axes through parallel natural-language descriptions. This does not establish discovery of an unanticipated ontology or natural scientific representation.",
    }
    with open("developmental_controller_pilot_v3_result.json","w") as f:
        json.dump(payload,f,indent=2,sort_keys=True)
    print(json.dumps(payload,indent=2,sort_keys=True))
    if not payload["all_gates_pass"]:
        raise SystemExit("v3 gates failed")

if __name__=="__main__":
    main()
