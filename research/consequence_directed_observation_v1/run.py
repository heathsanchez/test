#!/usr/bin/env python3
"""EXPOSED calibrated receipt selector, not source-native discovery."""
from itertools import combinations
import json
from pathlib import Path

RECEIPTS = {'DOC': 1, 'DEFAULT': 3, 'AUTHOR': 4}
UNAVAILABLE = {'IDS': 6}
REQUIRED = frozenset(RECEIPTS)
def verdict(seen):
    return 'REFUTED' if REQUIRED <= set(seen) else 'UNKNOWN'
def directed():
    options = []
    names = sorted(RECEIPTS)
    for n in range(len(names)+1):
        for xs in combinations(names,n):
            if verdict(xs) != 'UNKNOWN':
                options.append((sum(RECEIPTS[x] for x in xs), len(xs), xs))
    return min(options)
def full_information_baseline():
    names = list(RECEIPTS)
    best = None
    for mask in range(1 << len(names)):
        xs = tuple(sorted(x for j,x in enumerate(names) if mask & (1 << j)))
        if set(xs) >= {'DOC','DEFAULT','AUTHOR'}:
            candidate = (sum(RECEIPTS[x] for x in xs),len(xs),xs)
            best = min(best,candidate) if best else candidate
    return best
def run():
    choice = directed()
    baseline = full_information_baseline()
    assert choice == baseline == (8,3,('AUTHOR','DEFAULT','DOC'))
    for x in RECEIPTS:
        assert verdict(REQUIRED-{x}) == 'UNKNOWN'
        assert verdict((REQUIRED-{x})|{x}) == 'REFUTED'
    assert verdict({'DEFAULT'}) == 'UNKNOWN'
    assert 'IDS' not in RECEIPTS
    # An irrelevant observation cannot improve the protected objective.
    assert directed() == choice
    result = {
       'boundary':'EXPOSED historical-receipt model; no new source-native test',
       'decision':'REFUTED under declared source/census assumptions',
       'selected_receipts':list(choice[2]), 'hypothetical_cost':choice[0],
       'full_information_baseline_cost':baseline[0], 'comparison':'TIE',
       'withdraw_restore':'PASS 3/3', 'case_identity':'UNKNOWN',
       'full_author_suite_completeness':'UNKNOWN',
       'general_semantic_fidelity':'UNKNOWN', 'G2':'UNKNOWN'
    }
    Path(__file__).with_name('result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': run()
