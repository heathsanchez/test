#!/usr/bin/env python3
from contextlib import redirect_stdout
import io,json
with redirect_stdout(io.StringIO()):
    import collatz_crystal_phase_normalized_return_v40 as v40

old=[e for rr in v40.runs for e in rr["events"]]
old_ids={e["cert_id"] for e in old}
old_keys={e["source_key"] for e in old}
old_anchors=set(v40.banks)
tests=list(range(1,1025))
tests += [1018706+d for d in range(-32,33) if d]
found=None
checked=0
survivors=0
for t in tests:
    n=v40.v25.N0+v40.v25.NC*t
    rr=v40.actual_episode_returns(str(t),n,n.bit_length()+300)
    checked+=1
    if rr["note"]=="ordinary exit before zero-tail":
        continue
    survivors+=1
    for e in rr["events"]:
        row={"t":t,"source":str(n),"anchor":e["anchor"],"k0":e["k0"],"k1":e["k1"],
             "cert_id":e["cert_id"],"A":str(e["cert"]["A"]),"B":str(e["cert"]["B"]),
             "D":e["cert"]["D"],"rho":str(e["cert"]["rho"])}
        if e["anchor"] not in old_anchors:
            found={"kind":"new_anchor",**row}; break
        ik,sk=v40.event_keys(e)
        if sk not in old_keys:
            found={"kind":"new_protected_key","source_key":repr(sk),**row}; break
        if e["cert_id"] not in old_ids:
            found={"kind":"new_law_same_key","source_key":repr(sk),**row}; break
    if found: break
print(json.dumps({
 "schema":"COLLATZ_CRYSTAL_RETURN_GRAMMAR_SEPARATOR_V43",
 "checked":checked,"postzero_sources":survivors,"separator":found,
 "verdict":"SEPARATOR_FOUND" if found else "NO_SEPARATOR_BOUNDED",
 "global_collatz":"UNKNOWN"
},indent=2,sort_keys=True))
