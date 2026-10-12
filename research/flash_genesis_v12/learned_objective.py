# Compiled by frozen V12 source-only objective refinement.
POLICY = {'topology': 'both', 'objective': 'sum_weights', 'bound': 'positive_weights', 'include_first': True}

def developed_optimize(n, independent, weights, order=None):
    if order is None:order=tuple(range(n))
    order=tuple(order)
    best=0
    def value(mask):
        return sum(weights[i] for i in range(n) if mask>>i&1)
    def branch(i,chosen):
        nonlocal best
        bound=value(chosen)+sum(max(0,weights[e]) for e in order[i:])
        if bound<=best:return
        if i==len(order):
            if independent(chosen):best=max(best,value(chosen))
            return
        bit=1<<order[i]
        states=(chosen|bit,chosen) if POLICY['include_first'] else (chosen,chosen|bit)
        for m in states:branch(i+1,m)
    branch(0,0)
    return best
