"""Independent exhaustive finite dependency oracle; not a Lean kernel proof."""
import itertools, json
NODES=('A','B','C','D','E','F')
PARENTS={'A':(), 'B':('A',), 'C':('B',), 'D':(), 'E':('D',), 'F':('A','D')}
def computed(active):
    admitted=set()
    for _ in NODES:
        admitted|={n for n in active if all(p in admitted for p in PARENTS[n])}
    return admitted
def ancestors(n):
    seen=set(); todo=list(PARENTS[n])
    while todo:
        p=todo.pop()
        if p not in seen: seen.add(p); todo.extend(PARENTS[p])
    return seen
for flags in itertools.product((False,True),repeat=len(NODES)):
    active={n for n,f in zip(NODES,flags) if f}
    independent={n for n in active if ancestors(n)<=active}
    assert computed(active)==independent,(active,computed(active),independent)
full=set(NODES); without=full-{'A'}
assert computed(without)=={'D','E'}
assert computed(full)==full
print(json.dumps({'status':'PASS','states':64,'withdraw_A_remaining':sorted(computed(without)),'withdraw_A_lost':sorted(full-computed(without)),'restore_exact':computed(full)==full},sort_keys=True))
