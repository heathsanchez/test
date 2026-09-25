#!/usr/bin/env python3
import future_quotient_v4 as v4
_orig=v4.fg_contexts
def _one(_):
    xs=_orig(v4.fg)
    out=[x for x in xs if x[0]=="S7:quad-cycle"]
    if len(out)!=1: raise RuntimeError("bad context selector")
    return out
v4.fg_contexts=_one
if __name__=="__main__":
    v4.main()
