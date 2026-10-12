"""Independent complete and stack-based solver; does not import V12/V13 engine."""
def optimum(world):
    n=world.n;value=-10**15;witness=None;reads=0
    for mask in range(1<<n):
        reads+=1
        if world.feasible(mask):
            current=world.score(mask)
            if current>value:value=current;witness=mask
    return {'value':value,'witness':witness,'feasible_calls':reads}

def strong_weighted(world):
    n=world.n;order=tuple(range(n));best=0;calls=0
    pending=[(0,0,0)]
    while pending:
        i,mask,val=pending.pop()
        bound=val+sum(max(0,world.weights[j]) for j in order[i:])
        if bound<=best:continue
        if i==n:
            calls+=1
            if world.feasible(mask):best=max(best,val)
            continue
        j=order[i]
        pending.append((i+1,mask,val))
        pending.append((i+1,mask|(1<<j),val+world.weights[j]))
    return {'value':best,'feasible_calls':calls}

def old_cardinality_witness(world):
    largest=-1;selected=None
    for mask in range(1<<world.n):
        if world.feasible(mask) and mask.bit_count()>largest:
            largest=mask.bit_count();selected=mask
    assert selected is not None
    return {'cardinality':largest,'canonical_example_mask':selected,
           'canonical_example_weight':world.score(selected)}
