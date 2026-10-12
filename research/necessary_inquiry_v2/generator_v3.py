"""V3 structural repair: nuisance dimension comes from observed feature rank.

The former n+1 assumption in V2 was exactly the affine-only specialization.
This generator uses only a source nuisance-evaluation table and a target table;
it does not hardcode measurement-derivative order, arity, or feature labels.
"""

def parity(x):
    return x.bit_count()&1


def members(v):
    while v:
        low=v&-v
        yield low.bit_length()-1
        v ^= low


def image(row,feature_table):
    v=0
    for i in members(row):v ^= feature_table[i]
    return v


def insert(basis,x):
    while x:
        p=x.bit_length()-1
        if p in basis:x^=basis[p]
        else:
            basis[p]=x
            return True
    return False


def rank(vectors):
    b={}
    for v in vectors:insert(b,v)
    return len(b)


def synthesize(n,nuisance_table,target_table,old_rows=()):
    """Derive a minimal-count additional *binary* observation basis.

    Each returned row is a bitset of raw input locations whose outcomes must
    be XORed. The generator is conditional on both feature tables being known.
    It minimizes new aggregate *sensor count*, not lifetime computation or
    physical/raw outcome cost.
    """
    assert len(nuisance_table)==len(target_table)==1<<n
    nuisance_rank=rank(nuisance_table)
    target_rank=rank(target_table)
    pivot={};null_rows=[];pivot_locations=[]
    for x in sorted(range(1<<n), key=lambda x:(x.bit_count(),x)):
        vec=nuisance_table[x]
        combo=1<<x
        while vec:
            p=vec.bit_length()-1
            if p in pivot:
                pv,pc=pivot[p]
                vec ^= pv
                combo ^= pc
            else:
                pivot[p]=(vec,combo)
                pivot_locations.append(x)
                break
        if not vec:
            assert combo and image(combo,nuisance_table)==0
            null_rows.append(combo)
    assert len(pivot_locations)==nuisance_rank
    assert len(null_rows)==(1<<n)-nuisance_rank
    # Old observations are admissible only if they cancel all nuisance modes.
    assert all(image(row,nuisance_table)==0 for row in old_rows)
    basis={}
    for row in old_rows:insert(basis,image(row,target_table))
    old_rank=len(basis)
    selected=[]
    for row in sorted(null_rows,key=lambda row:(row.bit_count(),tuple(members(row)))):
        if insert(basis,image(row,target_table)):
            selected.append(row)
            if len(basis)==target_rank:break
    return dict(nuisance_rank=nuisance_rank,target_rank=target_rank,
                old_rank=old_rank,new_rows=selected,
                resulting_rank=len(basis),lower_bound=target_rank-old_rank,
                candidate_count=len(null_rows),pivot_locations=pivot_locations)
