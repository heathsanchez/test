#!/usr/bin/env python3
import ast, json, re, sys
from pathlib import Path

MAP={-2:1,-1:2,1:3,2:4}
GENS=(1,-1,2,-2)

def parse(path):
    out={}
    for line in Path(path).read_text().splitlines():
        m=re.match(r"^(ac-[0-9]+):\s*(\[.*\])$",line.strip())
        if m: out[m.group(1)]=list(ast.literal_eval(m.group(2)))
    return out

def replay_states(core, initial, moves):
    s=tuple(tuple(w) for w in initial)
    out=[s]
    for m in moves:
        s=core.apply_move(s,m); out.append(s)
    return out

def longest_common(a,b):
    dp=[0]*(len(b)+1); best=(0,0,0)
    for i,x in enumerate(a,1):
        nd=[0]*(len(b)+1)
        for j,y in enumerate(b,1):
            if x==y:
                nd[j]=dp[j-1]+1
                if nd[j]>best[0]: best=(nd[j],i-nd[j],j-nd[j])
        dp=nd
    return best

def phi_letter(img,g):
    return img[g-1] if g>0 else -img[-g-1]

def syms():
    out=[]
    for perm in ((1,2),(2,1)):
      for s1 in (-1,1):
       for s2 in (-1,1):
        for swap in (False,True):
          out.append(((s1*perm[0],s2*perm[1]),swap))
    return out

SYMS=syms()

def transform_state(s,sym):
    img,swap=sym
    a=tuple(phi_letter(img,x) for x in s[0])
    b=tuple(phi_letter(img,x) for x in s[1])
    return (b,a) if swap else (a,b)

def related(a,b):
    return [k for k,s in enumerate(SYMS) if transform_state(a,s)==b]

def abel_word(w):
    return (sum(1 if x==1 else -1 if x==-1 else 0 for x in w),
            sum(1 if x==2 else -1 if x==-2 else 0 for x in w))

def abel_state(s): return [abel_word(w) for w in s]

def macro_matrix(seq):
    M=[[1,0],[0,1]]
    for m in seq:
      if m==0: M[0]=[-x for x in M[0]]
      elif m==1: M[1]=[-x for x in M[1]]
      elif m==2: M[0]=[M[0][k]+M[1][k] for k in range(2)]
      elif m==3: M[0]=[M[0][k]-M[1][k] for k in range(2)]
      elif m==4: M[1]=[M[1][k]+M[0][k] for k in range(2)]
      elif m==5: M[1]=[M[1][k]-M[0][k] for k in range(2)]
    return M

def main():
    acc=Path(sys.argv[1]); sub=Path(sys.argv[2]); out=Path(sys.argv[3])
    sys.path.insert(0,str(acc/"competition/tools"))
    from verifier import core
    manifest=json.loads((acc/"competition/tools/verifier/data/manifest.json").read_text())
    byid={c["challenge_id"]:c for c in manifest["challenges"]}
    limits=manifest["limits"]
    paths=parse(sub)
    states={}
    for cid,p in paths.items():
        c=byid[cid]
        v=core.verify(c,p,c["move_spec_version"],limits)
        if not v.get("ok"): raise RuntimeError((cid,v))
        states[cid]=replay_states(core,c["initial_relators"],p)

    rows=[]
    ids=sorted(paths)
    for ai,a in enumerate(ids):
      for b in ids[ai+1:]:
        L,ia,ib=longest_common(paths[a],paths[b])
        if L<4: continue
        motif=paths[a][ia:ia+L]
        sa,sb=states[a][ia],states[b][ib]
        ea,eb=states[a][ia+L],states[b][ib+L]
        rows.append({
          "a":a,"b":b,"length":L,"a_pos":ia,"b_pos":ib,
          "moves":motif,
          "start_symmetries":related(sa,sb),
          "end_symmetries":related(ea,eb),
          "start_a":sa,"start_b":sb,"end_a":ea,"end_b":eb,
          "start_abelianization_a":abel_state(sa),
          "start_abelianization_b":abel_state(sb),
          "macro_abelianization_matrix":macro_matrix(motif),
        })
    rows.sort(key=lambda r:(-r["length"],r["a"],r["b"]))
    best=rows[0] if rows else None
    report={
      "experiment":"ACC_PROOF_TRACK_MOTIF_MINER_V1",
      "verified_ac_certificates":len(paths),
      "pair_matches":len(rows),
      "best":best,
      "classification":(
        "SYMMETRY_NORMALIZED_REUSABLE_ROUTE" if best and best["start_symmetries"]
        else "SHARED_PROGRAM_DIFFERENT_STATES" if best else "NO_SHARED_MOTIF"
      ),
      "claim_boundary":"Finite mining over committed verifier-clean V1 AC certificates only; no universality claim."
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"all_matches.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print("THEOREM_MOTIF_MINER",json.dumps({
      "verified":len(paths),"matches":len(rows),
      "best_length":None if not best else best["length"],
      "best_pair":None if not best else [best["a"],best["b"]],
      "start_symmetries":None if not best else best["start_symmetries"],
      "end_symmetries":None if not best else best["end_symmetries"],
      "macro_matrix":None if not best else best["macro_abelianization_matrix"],
      "classification":report["classification"],
    },sort_keys=True))

if __name__=="__main__": main()
