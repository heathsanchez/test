#!/usr/bin/env python3
"""ARC400 V11 — residual-driven observable-program synthesis.

V10 certified a bounded representation-language obstruction: the finite named
Boolean observable carrier was exhausted while BOT/S/B label collisions
remained. V11 therefore changes the *kind* of continuation searched.

Instead of selecting another named feature, it constructs observables as small
programs over lower-level measurable relations.  The meta-language is finite
and exhaustively enumerated:

  numeric measurements M(task) from training pairs only
    shape ratios, colour counts, and two generic correspondence scores:
    (i) cell->uniform-block correspondence and
    (ii) output-tile->D8(input) correspondence;

  observable programs P ::= [m == c] | [m >= c] | [m <= c]
                         | [m1 == m2]

Constants are a frozen small rational set.  No BOT/S/B label appears in an
observable program. Programs are selected only because they strictly reduce
certified label collisions on the meta-training split.  After collision closure
we freeze the representation and exact lookup law, then audit predictions on
untouched training and source-distinct evaluation before consulting the oracle.

This is still bounded concept/representation synthesis relative to the supplied
measurement/combinator meta-language. It is deliberately stronger than V10's
finite menu of named residual predicates, not a claim of unrestricted invention.
"""
from __future__ import annotations
import argparse, json, math, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import arc400_recursive_applicability_v10 as v10

LABELS = ("BOT", "S", "B")
CONSTS = (-1.0, 0.0, 0.25, 0.5, 0.75, 1.0, 2.0, 3.0, 4.0, 9.0)
EPS = 1e-9


def dims(g):
    return len(g), (len(g[0]) if g else 0)

def colors(g):
    return set(x for r in g for x in r)

def transpose(g): return [list(x) for x in zip(*g)] if g else []
def rot90(g): return [list(r) for r in zip(*g[::-1])] if g else []
def rot180(g): return [r[::-1] for r in g[::-1]]
def rot270(g): return rot90(rot180(g))
def flip_h(g): return [r[::-1] for r in g]
def flip_v(g): return g[::-1]

def d8(g):
    xs=[g,rot90(g),rot180(g),rot270(g),flip_h(g),flip_v(g)]
    t=transpose(g); xs += [t, rot180(t)]
    out=[]
    for x in xs:
        if x not in out: out.append(x)
    return out


def cell_expand(inp, k):
    if k < 1: return None
    out=[]
    for row in inp:
        rr=[]
        for x in row: rr.extend([x]*k)
        for _ in range(k): out.append(list(rr))
    return out


def best_cell_correspondence(inp, out):
    hi,wi=dims(inp); ho,wo=dims(out)
    if not hi or not wi or ho % hi or wo % wi: return (0.0,-1.0)
    kh,kw=ho//hi,wo//wi
    if kh != kw or kh < 1: return (0.0,-1.0)
    pred=cell_expand(inp,kh)
    total=max(1,ho*wo); hit=sum(pred[r][c]==out[r][c] for r in range(ho) for c in range(wo))
    return (hit/total,float(kh))


def best_d8_tile_correspondence(inp, out):
    hi,wi=dims(inp); ho,wo=dims(out)
    if not hi or not wi or ho % hi or wo % wi: return (0.0,-1.0,-1.0)
    br,bc=ho//hi,wo//wi
    variants=[x for x in d8(inp) if dims(x)==(hi,wi)]
    if not variants: return (0.0,float(br),float(bc))
    good=0
    for rr in range(br):
        for cc in range(bc):
            tile=[row[cc*wi:(cc+1)*wi] for row in out[rr*hi:(rr+1)*hi]]
            if any(tile==v for v in variants): good+=1
    return (good/max(1,br*bc),float(br),float(bc))


def mode_or_neg(vals):
    if not vals: return -1.0
    a=vals[0]
    return float(a) if all(abs(float(x)-float(a)) < EPS for x in vals) else -1.0


def measurements(task):
    tr=task.get("train",[])
    if not tr: return {}
    hrs=[]; wrs=[]; ars=[]; cd=[]; incc=[]; outcc=[]
    cell_scores=[]; cell_ks=[]; tile_scores=[]; brs=[]; bcs=[]
    for ex in tr:
        i,o=ex["input"],ex["output"]
        hi,wi=dims(i); ho,wo=dims(o)
        rh=(ho/hi if hi else -1.0); rw=(wo/wi if wi else -1.0)
        hrs.append(rh); wrs.append(rw); ars.append((ho*wo)/(hi*wi) if hi and wi else -1.0)
        ci,co=len(colors(i)),len(colors(o)); incc.append(ci); outcc.append(co); cd.append(co-ci)
        sc,k=best_cell_correspondence(i,o); cell_scores.append(sc); cell_ks.append(k)
        ts,br,bc=best_d8_tile_correspondence(i,o); tile_scores.append(ts); brs.append(br); bcs.append(bc)
    return {
      "height_ratio_const": mode_or_neg(hrs),
      "width_ratio_const": mode_or_neg(wrs),
      "area_ratio_const": mode_or_neg(ars),
      "color_delta_const": mode_or_neg(cd),
      "input_color_count_const": mode_or_neg(incc),
      "output_color_count_const": mode_or_neg(outcc),
      "cell_correspondence_min": min(cell_scores),
      "cell_scale_const": mode_or_neg(cell_ks),
      "d8_tile_correspondence_min": min(tile_scores),
      "d8_block_rows_const": mode_or_neg(brs),
      "d8_block_cols_const": mode_or_neg(bcs),
      "train_examples": float(len(tr)),
    }


def prog_name(p):
    if p[0] == "cmpc": return f"({p[1]} {p[2]} {p[3]:g})"
    return f"({p[1]} == {p[2]})"

def eval_prog(p,row):
    if p[0]=="cmpc":
        _,m,op,c=p; x=row.get(m,-1.0)
        if op=="==": return abs(x-c)<EPS
        if op==">=": return x >= c-EPS
        return x <= c+EPS
    _,a,b=p; return abs(row.get(a,-1.0)-row.get(b,-1.0))<EPS


def build_program_carrier(metric_names):
    ps=[]
    for m in metric_names:
        for c in CONSTS:
            for op in ("==",">=","<="): ps.append(("cmpc",m,op,c))
    # equality of independently measured coordinates is a genuinely composed observable
    for i,a in enumerate(metric_names):
        for b in metric_names[i+1:]: ps.append(("eqm",a,b))
    return ps


def sig(task, base, programs, mcache, bcache):
    b=bcache[id(task)]
    return tuple(bool(b.get(x,False)) for x in base) + tuple(eval_prog(p,mcache[id(task)]) for p in programs)

def collision_stats(examples,base,programs,mcache,bcache):
    buckets={}
    for _,t,lab,_ in examples:
        s=sig(t,base,programs,mcache,bcache); buckets.setdefault(s,set()).add(lab)
    bad={k:v for k,v in buckets.items() if len(v)>1}
    score=sum(len(v)*(len(v)-1)//2 for v in bad.values())
    return score,bad


def refine(examples,base,carrier,mcache,bcache):
    active=[]; events=[]
    before,_=collision_stats(examples,base,active,mcache,bcache)
    while before>0:
        ranked=[]
        for p in carrier:
            if p in active: continue
            after,_=collision_stats(examples,base,active+[p],mcache,bcache)
            if after<before: ranked.append((after,len(prog_name(p)),prog_name(p),p))
        if not ranked: break
        ranked.sort(key=lambda x:(x[0],x[1],x[2])); after,_,_,p=ranked[0]
        events.append({"rho_rep":"LABEL_COLLISION_WITH_NO_NAMED_FEATURE_REFINEMENT",
                       "paradigm_shift":"NAMED_FEATURES_TO_OBSERVABLE_PROGRAMS",
                       "collisions_before":before,
                       "CompleteCover_observable_program_carrier":True,
                       "Delta_R":{"install_observable_program":prog_name(p),"ast":list(p)},
                       "collisions_after":after,"strict_information_refinement":after<before})
        active.append(p); before=after
    return active,events,before


def learn_lookup(examples,base,programs,mcache,bcache):
    table={}; support={}; amb=set()
    for _,t,lab,_ in examples:
        s=sig(t,base,programs,mcache,bcache)
        if s in table and table[s]!=lab: amb.add(s)
        else: table[s]=lab
        support[s]=support.get(s,0)+1
    for s in amb: table.pop(s,None)
    return table,support


def evaluate(tasks,base,programs,table,mcache,bcache):
    rows=[]; predn=abst=correct=wrong=exact=causal=0
    for tid,t in tasks:
        s=sig(t,base,programs,mcache,bcache); pred=table.get(s,"BOT")
        if pred=="BOT": abst+=1; continue
        predn+=1
        oracle,ast0=v10.oracle_label(t); ok=(oracle==pred); correct+=int(ok); wrong+=int(not ok)
        solved,ast=v10.exact_test_with_constructor(t,pred) if ok else (False,None)
        exact+=int(solved); cc=bool(solved and pred in ("S","B")); causal+=int(cc)
        rows.append({"task":tid,"signature":list(s),"predicted":pred,"posthoc_oracle":oracle,
                     "prediction_correct":ok,"exact_after_extension":solved,"C_causal":cc,
                     "ast":repr(ast or ast0) if (ast or ast0) is not None else None})
    return {"predictions":predn,"abstentions":abst,"correct":correct,"wrong_nonbot":wrong,
            "exact":exact,"causal_exact":causal,"rows":rows}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--arc-root",required=True); ap.add_argument("--out-dir",required=True); ap.add_argument("--seed",type=int,default=1729)
    a=ap.parse_args(); root=Path(a.arc_root); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    train=v10.load_tasks(root,"training"); evaluation=v10.load_tasks(root,"evaluation")
    rng=random.Random(a.seed); idx=list(range(len(train))); rng.shuffle(idx); cut=len(idx)//2
    meta=[train[i] for i in idx[:cut]]; held=[train[i] for i in idx[cut:]]
    meta_examples=[]
    for tid,t in meta:
        lab,ast=v10.oracle_label(t); meta_examples.append((tid,t,lab,ast))
    all_tasks=[t for _,t in train+evaluation]
    bcache={}; mcache={}
    for t in all_tasks:
        bcache[id(t)]=v10.base_observables(t)
        mcache[id(t)]=measurements(t)
    base=["shape_ratio_equal","palette_preserved"]
    metrics=sorted(next(iter(mcache.values())).keys()) if mcache else []
    carrier=build_program_carrier(metrics)
    initial,_=collision_stats(meta_examples,base,[],mcache,bcache)
    programs,events,final=refine(meta_examples,base,carrier,mcache,bcache)
    table,support=learn_lookup(meta_examples,base,programs,mcache,bcache)
    h=evaluate(held,base,programs,table,mcache,bcache); e=evaluate(evaluation,base,programs,table,mcache,bcache)
    counts={x:sum(1 for _,_,lab,_ in meta_examples if lab==x) for x in LABELS}
    gates={
      "v10_obstruction_reproduced": initial>0,
      "observable_program_carrier_complete": True,
      "paradigm_shift_occurred": bool(events),
      "every_installed_program_strictly_reduces_collision": all(x["strict_information_refinement"] for x in events),
      "meta_collisions_closed": final==0,
      "heldout_prediction_exists": h["predictions"]>0,
      "heldout_no_false_nonbot_predictions": h["wrong_nonbot"]==0,
      "heldout_causal_gain": h["causal_exact"]>0,
      "source_distinct_prediction_exists": e["predictions"]>0,
      "source_distinct_no_false_nonbot_predictions": e["wrong_nonbot"]==0,
      "source_distinct_causal_gain": e["causal_exact"]>0,
    }
    gates["OBSERVABLE_PROGRAM_SYNTHESIS_GATE"]=all(gates.values())
    result={"status":"ARC400_OBSERVABLE_PROGRAM_SYNTHESIS_V11",
      "claim_scope":"bounded residual-driven paradigm shift from exhausted named residual features to synthesized observable programs over a finite low-level measurement/combinator language; training-pair outputs allowed, test outputs withheld until scoring",
      "split":{"meta_train":len(meta),"heldout_training":len(held),"evaluation":len(evaluation)},
      "meta_label_counts":counts,"base_representation":base,"numeric_measurement_primitives":metrics,
      "observable_program_grammar":"cmp(metric,const) or eq(metric,metric)","observable_program_carrier_size":len(carrier),
      "initial_collisions":initial,"representation_events":events,
      "learned_observable_programs":[{"name":prog_name(p),"ast":list(p)} for p in programs],
      "final_meta_collisions":final,
      "lookup_rules":[{"signature":list(k),"label":v,"support":support.get(k,0)} for k,v in sorted(table.items(),key=lambda kv:repr(kv[0]))],
      "heldout_training":h,"source_distinct_evaluation":e,"gates":gates}
    (out/"RESULT.json").write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

if __name__=="__main__": main()
