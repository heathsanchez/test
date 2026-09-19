from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from itertools import product

# Blind representation-program synthesizer.
# It never sees the mathematical verifier or any target object label.

@dataclass(frozen=True)
class Op:
    kind: str
    arg: object = None

def feature(word, output, op):
    if op.kind == "split_length": return len(word)
    if op.kind == "split_first": return word[0] if word else "<empty>"
    if op.kind == "split_last": return word[-1] if word else "<empty>"
    if op.kind == "split_count": return word.count(op.arg)
    if op.kind == "split_probe": return output[int(op.arg)]
    raise KeyError(op.kind)

def normalize(partition):
    # canonical ordered tuple of blocks, each block sorted by program.
    blocks=[]
    for b in partition:
        blocks.append(tuple(sorted(b,key=lambda x:(len(x[0]),x[0]))))
    blocks.sort(key=lambda b:(len(b), tuple((len(w),w) for w,_ in b)))
    return tuple(blocks)

def split_partition(partition, op):
    out=[]
    for block in partition:
        buckets=defaultdict(list)
        for row in block:
            w,obs=row
            buckets[feature(w,obs,op)].append(row)
        out.extend(buckets.values())
    return normalize(out)

def refine_successors(partition, tokens, lookup):
    # Generic congruence refinement: split states whose token successors
    # land in different current blocks. No output feature is consulted here.
    row_to_block={}
    for bi,b in enumerate(partition):
        for w,_ in b: row_to_block[w]=bi
    out=[]
    for block in partition:
        buckets=defaultdict(list)
        for w,obs in block:
            sig=[]
            for t in tokens:
                w2=w+(t,)
                sig.append(row_to_block.get(w2,-1))
            buckets[tuple(sig)].append((w,obs))
        out.extend(buckets.values())
    return normalize(out)

def merge_same_transition_profile(partition, tokens, lookup):
    # A deliberately different primitive: attempt to coarsen blocks whose
    # representative successor signatures agree. Safe only if scoring accepts it.
    row_to_block={}
    for bi,b in enumerate(partition):
        for w,_ in b: row_to_block[w]=bi
    sig_to_rows=defaultdict(list)
    for bi,b in enumerate(partition):
        rep=min(b,key=lambda x:(len(x[0]),x[0]))
        w,_=rep
        sig=tuple(row_to_block.get(w+(t,),-1) for t in tokens)
        sig_to_rows[sig].extend(b)
    return normalize(sig_to_rows.values())

def apply_program(rows, tokens, program):
    lookup={w:o for w,o in rows}
    p=normalize([rows])
    trajectory=[{"op":"START","blocks":len(p)}]
    for op in program:
        if op.kind.startswith("split_"):
            p=split_partition(p,op)
        elif op.kind=="refine_successors":
            p=refine_successors(p,tokens,lookup)
        elif op.kind=="merge_transition_profile":
            p=merge_same_transition_profile(p,tokens,lookup)
        else:
            raise KeyError(op.kind)
        trajectory.append({"op":op.kind,"arg":op.arg,"blocks":len(p)})
    return p,trajectory

def residuals(partition, tokens, lookup):
    # A valid representation must make both observable behavior and token
    # transition destinations deterministic at the block level.
    row_to_block={}
    for bi,b in enumerate(partition):
        for w,_ in b: row_to_block[w]=bi
    pred_conf=0
    trans_conf=0
    for bi,b in enumerate(partition):
        outs={obs for _,obs in b}
        pred_conf += max(0,len(outs)-1)
        for t in tokens:
            dest={row_to_block[w+(t,)] for w,_ in b if w+(t,) in lookup}
            trans_conf += max(0,len(dest)-1)
    return pred_conf,trans_conf

def library(tokens,n_points):
    ops=[
        Op("split_length"),Op("split_first"),Op("split_last"),
        Op("refine_successors"),Op("merge_transition_profile"),
    ]
    ops += [Op("split_count",t) for t in tokens]
    ops += [Op("split_probe",i) for i in range(n_points)]
    return tuple(ops)

def synthesize(rows,tokens,n_points,max_len=4):
    """
    Enumerate representation-building programs. A state space exists only as
    the output of executing one of these programs; there is no direct
    compound-feature constructor.

    Frozen score:
      residual conflicts, then number of blocks, then program length,
      then primitive description cost.
    """
    lookup={w:o for w,o in rows}
    lib=library(tokens,n_points)
    searched=0
    by_len=[]
    winner=None

    for L in range(0,max_len+1):
        best=None
        exact=[]
        for prog in product(lib,repeat=L):
            searched+=1
            part,traj=apply_program(rows,tokens,prog)
            pc,tc=residuals(part,tokens,lookup)
            cost=sum(1 if x.kind in {"split_length","split_first","split_last","refine_successors","merge_transition_profile"} else 2 for x in prog)
            score=(pc+tc,len(part),L,cost,tuple((x.kind,str(x.arg)) for x in prog))
            rec=(score,prog,part,traj,pc,tc)
            if best is None or score<best[0]: best=rec
            if pc==0 and tc==0: exact.append(rec)
        by_len.append({
            "program_length":L,
            "best_score":best[0],
            "best_program":[(x.kind,x.arg) for x in best[1]],
            "best_predictive_conflicts":best[4],
            "best_transition_conflicts":best[5],
            "exact_programs":len(exact),
        })
        if exact:
            exact.sort(key=lambda r:r[0])
            winner=exact[0]
            break

    if winner is None:
        raise RuntimeError("no residual-closing representation program found")

    _,prog,part,traj,pc,tc=winner
    # Freeze states from partition blocks. Representatives only name blocks.
    rep={i:min(b,key=lambda x:(len(x[0]),x[0]))[0] for i,b in enumerate(part)}
    behavior={i:min(b,key=lambda x:(len(x[0]),x[0]))[1] for i,b in enumerate(part)}
    row_to_state={w:i for i,b in enumerate(part) for w,_ in b}
    transitions={}
    for i,w in rep.items():
        for t in tokens:
            if w+(t,) in row_to_state:
                transitions[(i,t)]=row_to_state[w+(t,)]
    start=row_to_state[()]
    return {
        "program":[{"kind":x.kind,"arg":x.arg} for x in prog],
        "trajectory":traj,
        "search_history":by_len,
        "programs_searched":searched,
        "state_count":len(part),
        "representatives":rep,
        "behaviors":behavior,
        "transitions":transitions,
        "start_state":start,
    }

def execute(model,word):
    s=model["start_state"]
    for t in word:
        if (s,t) not in model["transitions"]: return None
        s=model["transitions"][(s,t)]
    return s
