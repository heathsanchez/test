"""Offline diagnostic closure. Never imported by the checker.

Port of the historical semantic-contract idea, not its stale registry.
Keep every subset-minimal support set, so a derived fact cannot erase a
candidate premise and shared dependencies are counted once. Facts belong to
ONE evidence object per invocation; callers must not pool objects.
"""
from dataclasses import dataclass
from itertools import product

@dataclass(frozen=True)
class Contract:
    id: str
    requires: set
    produces: set
    warranted: bool
    preserves: str = 'lean.verdict'

def plan(contracts, seeds, goal, limit=4096):
    registry = {c.id:c for c in contracts}
    if len(registry) != len(contracts):
        raise ValueError('duplicate contract id')
    facts = {s:{frozenset()} for s in seeds}
    steps = 0
    def result(status, support=()):
        ids=sorted(support)
        candidates=[i for i in ids if not registry[i].warranted]
        return dict(status=status,contracts=ids,candidates=candidates,
                    path_id=f'{goal}|'+'>'.join(ids))
    while True:
        changed=False
        for c in sorted(contracts,key=lambda c:c.id):
            if c.preserves != 'lean.verdict' or any(r not in facts for r in c.requires):
                continue
            choices=[list(facts[r]) for r in sorted(c.requires)]
            for paths in product(*choices):
                steps+=1
                if steps>limit:
                    return result('UNKNOWN_PLANNER_LIMIT')
                support=frozenset({c.id}).union(*paths)
                for target in c.produces:
                    old=facts.setdefault(target,set())
                    if any(p<=support for p in old): continue
                    old.difference_update([p for p in old if support<p])
                    old.add(support)
                    changed=True
        if not changed: break
    if goal not in facts:
        return result('NO_REGISTERED_PATH')
    support=min(facts[goal],key=lambda p:(sum(not registry[i].warranted for i in p),len(p),sorted(p)))
    return result('WARRANTED_PATH' if all(registry[i].warranted for i in support) else 'CANDIDATE_PATH',support)
