"""Past/present/future jointly: exact finite continuation equivalence and reclosure.

No physical time reversal is claimed. All histories and futures are evaluated
as one static finite relation; computation still runs sequentially.
"""
import itertools,json
from collections import defaultdict
from .pinhole_major_v4 import saturate

def partition(histories,futures,eval_fn):
    groups=defaultdict(list)
    for h in histories:
        groups[tuple(eval_fn(h,f) for f in futures)].append(h)
    return tuple(sorted(tuple(sorted(v)) for v in groups.values()))

def main():
    # Two-step binary input histories, deterministic automaton; past determines
    # present state, future tests determine which past distinctions survive.
    histories=tuple(itertools.product((0,1),repeat=3))
    def present(h):
        s=0
        for x in h:s=(2*s+x)%3
        return s
    # Future inputs of length 0..3, observed as final state mod 2.
    futures=tuple(itertools.chain.from_iterable(
        itertools.product((0,1),repeat=n) for n in range(4)))
    def outcome(h,f):
        s=present(h)
        for x in f:s=(2*s+x)%3
        return s%2
    full=partition(histories,futures,outcome)
    current=partition(histories,((),),outcome)
    # Independent direct pairwise equivalence oracle.
    for a,b in itertools.combinations(histories,2):
        same=all(outcome(a,f)==outcome(b,f) for f in futures)
        grouped=any(a in group and b in group for group in full)
        assert same==grouped
    # Adding tests only refines; never merges previous observational classes.
    previous=None
    refinements=[]
    for depth in range(4):
        tests=tuple(f for f in futures if len(f)<=depth)
        classes=partition(histories,tests,outcome)
        if previous is not None:
            for c in classes:
                assert any(set(c)<=set(p) for p in previous)
        refinements.append(len(classes))
        previous=classes
    # Complete future relation is built at once, not one greedy action.
    # Ablate a future observation and check if quotient actually changes.
    essential=[]
    for i,f in enumerate(futures):
        remain=futures[:i]+futures[i+1:]
        if partition(histories,remain,outcome)!=full:essential.append(f)
    # Source exact past -> present -> future evaluator is shared, but the
    # partition itself is a simultaneous constraint over every continuation.
    print(json.dumps({"status":"PASS_FINITE_WHOLE_CONTINUATION",
      "histories":len(histories),"futures":len(futures),
      "current_classes":len(current),"whole_future_classes":len(full),
      "classes_by_future_depth":refinements,
      "essential_single_future_tests":len(essential),
      "all_pairwise_checks":28,
      "no_time_reversal_claim":True,
      "no_physical_ontology_claim":True,
      "global_semantic_fixed_point":"EXACT_FINITE",
      "self_reconstruction":"UNKNOWN"},sort_keys=True,indent=2))
if __name__=="__main__":main()
