# Source-compiled by V12 unbiased source-only selector (v2).
POLICY = {'topology': 'both', 'objective': 'sum_weights', 'bound': 'positive_weights', 'include_first': True}

def developed_optimize(n, independent, weights, order=None, score_fn=None):
    if order is None:order=tuple(range(n))
    order=tuple(order)
    def value(mask):
        m=POLICY['objective']
        if m=='count':return mask.bit_count()
        if m=='sum_weights':return sum(weights[i] for i in range(n) if mask>>i&1)
        if m=='max_singleton':return max([weights[i] for i in range(n) if mask>>i&1],default=0)
        if score_fn is None:raise ValueError('callback score required')
        return score_fn(mask)
    typ=POLICY['topology']
    if typ in ('greedy','rotate_greedy'):
        rotations=[order] if typ=='greedy' else [order[k:]+order[:k] for k in range(len(order))]
        best=0
        for arrangement in rotations:
            chosen=0
            for element in arrangement:
                nextmask=chosen|(1<<element)
                if independent(nextmask):chosen=nextmask
            best=max(best,value(chosen))
        return best
    if typ=='only_include':
        chosen=sum(1<<e for e in order)
        return value(chosen) if independent(chosen) else 0
    if typ!='both':raise ValueError('unsupported policy topology')
    best=0
    def branch(i,chosen):
        nonlocal best
        if POLICY['bound']!='none':
            if POLICY['bound']=='count':ub=chosen.bit_count()+len(order)-i
            elif POLICY['bound']=='positive_weights':
                ub=value(chosen)+sum(max(0,weights[e]) for e in order[i:])
            else:raise ValueError('unknown bound')
            if ub<=best:return
        if i==len(order):
            if independent(chosen):best=max(best,value(chosen))
            return
        bit=1<<order[i]
        states=(chosen|bit,chosen) if POLICY['include_first'] else (chosen,chosen|bit)
        for m in states:branch(i+1,m)
    branch(0,0)
    return best
