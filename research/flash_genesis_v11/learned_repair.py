# Source-compiled by V11 source-only structural repair search.
POLICY = {"bound": True, "include_first": True, "mode": "both_branches", "prune": False}

def learned_exact_rank(n, independent, order=None):
    if order is None: order=tuple(range(n))
    order=tuple(order)
    best=0
    def branch(i,chosen):
        nonlocal best
        if POLICY["prune"] and not independent(chosen):return
        if POLICY["bound"] and chosen.bit_count()+len(order)-i<=best:return
        if i==len(order):
            if independent(chosen):best=max(best,chosen.bit_count())
            return
        bit=1<<order[i]
        states=(chosen|bit,chosen) if POLICY["include_first"] else (chosen,chosen|bit)
        for state in states:branch(i+1,state)
    branch(0,0)
    return best
