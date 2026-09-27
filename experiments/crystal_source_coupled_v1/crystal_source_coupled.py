"""Bounded source-coupled audit; not a universal Collatz or quotient proof.

SharedBasin reuses dominated bounded suffixes without losing source witnesses.
No bounded miss is a negative semantic verdict. A constant-label control and
an exact source-27 self-loop prevent promotion of label purity into a rank.
The historical greedy feature experiment is retained, not used for promotion.
"""
from collections import defaultdict
import argparse, hashlib, json, random, sys, time
from pathlib import Path

def T(n): return n//2 if n%2==0 else (3*n+1)//2
def zero_tail_depth(n): return max(0,n.bit_length())

def lower_basin(n,h):
    hit={}
    for p in range(1,n):
        x=p
        for r in range(h+1):
            hit.setdefault(x,(p,r)); x=T(x)
    return hit


class SharedBasin:
    """Smallest source reaching each endpoint within a fixed step horizon.

    Process sources increasingly. At (x, remaining), stop only if an earlier
    traversal of x had at least as much remaining budget. Its suffix has
    already been covered by an equal-or-smaller source. A mere visit to x
    with a smaller remaining budget is NOT a valid pruning condition.
    This certifies bounded reachability, not all-depth basin completeness.
    """
    def __init__(self, max_source: int, horizon: int):
        if type(max_source) is not int or max_source < 1:
            raise ValueError('max_source must be a positive integer')
        if type(horizon) is not int or horizon < 0:
            raise ValueError('horizon must be a nonnegative integer')
        self.max_source, self.horizon = max_source, horizon
        first, remaining_at = {}, {}
        expanded = dominated = 0
        for p in range(1, max_source):
            x, r = p, 0
            while r <= horizon:
                remaining = horizon-r
                if remaining_at.get(x, -1) >= remaining:
                    dominated += 1
                    break
                if x not in first:
                    first[x] = (p,r)
                remaining_at[x] = remaining
                expanded += 1
                if remaining == 0:
                    break
                x = T(x)
                r += 1
        self.witnesses = first
        self.stats = {'sources_indexed': max_source-1,
                      'horizon': horizon, 'distinct_endpoints': len(first),
                      'expanded_states': expanded,
                      'dominated_suffixes': dominated}

    def witness(self, n: int, y: int):
        if n < 1 or n > self.max_source:
            raise ValueError('query source outside indexed domain')
        result = self.witnesses.get(y)
        return result if result is not None and result[0] < n else None

    def view(self, n: int):
        return _BasinView(self, n)


class _BasinView:
    def __init__(self, index, source):
        self.index, self.source = index, source

    def __contains__(self, y):
        return self.index.witness(self.source, y) is not None

    def __getitem__(self, y):
        result = self.index.witness(self.source, y)
        if result is None:
            raise KeyError(y)
        return result

def iter_rows(n,h):
    y, q, b = n, 0, 0
    for k in range(h+1):
        yield (k,y,q,b,y%2,y%3,y%9,y%12,y%27)
        if y%2:
            b=3*b+2**k
            q+=1
        y=T(y)


def actual_trace(n,h):
    return list(iter_rows(n,h))


def exit_at(n,y,basin):
    if y in (1,2): return ("terminal",)
    if y<n: return ("descent",)
    if y in basin:
        p,r=basin[y]; return ("merge",p,r)
    return None

def protected_future(n,x,h,basin):
    for j in range(h+1):
        e=exit_at(n,x,basin)
        if e is not None: return ("EXIT",)
        x=T(x)
    return ("UNKNOWN",)

def candidate(row,name):
    k,y,q,b,p2,m3,m9,m12,m27=row
    return {
      "parity":p2, "mod3":m3, "mod9":m9, "mod12":m12, "mod27":m27,
      "q_parity":q%2, "b_mod3":b%3, "b_mod9":b%9,
      "endpoint_vs_source":None, # filled source-relatively below
    }[name]

FEATURES=["parity","mod3","mod9","mod12","mod27","q_parity","b_mod3","b_mod9"]

def key_for(n,row,features):
    vals=[]
    for f in features:
        if f == "rel":
            vals.append(-1 if row[1]<n else (0 if row[1]==n else 1))
        else:
            vals.append(candidate(row,f))
    return tuple(vals)

def build_records(sources,post=96,future=512,reverse=256,index=None,certificates=None):
    sources=list(sources)
    if not sources:
        return []
    if any(type(n) is not int or n < 2 for n in sources):
        raise ValueError('census sources must be integers greater than one')
    if min(post,future,reverse) < 0:
        raise ValueError('horizons must be nonnegative')
    if index is None:
        index=SharedBasin(max(sources),reverse)
    if index.horizon != reverse or index.max_source < max(sources):
        raise ValueError('index does not cover this declared census')
    rec=[]
    for n in sources:
        basin=index.view(n)
        K=zero_tail_depth(n)
        pending=[]
        first_exit=None
        # Scan from depth zero: an earlier certified exit is never forgotten.
        # Bounded basin misses are unresolved, NOT actual no-exit proofs.
        for row in iter_rows(n,K+post+future):
            k,y,q,b,*_=row
            event=exit_at(n,y,basin)
            if event is not None:
                first_exit=k
                if certificates is not None:
                    certificates.append({'n':n,'depth':k,'endpoint':y,
                                         'odds':q,'bias':b,'witness':event})
                break
            if K <= k <= K+post:
                pending.append(row)
        for row in pending:
            lab=('EXIT',) if first_exit is not None and first_exit-row[0] <= future else ('UNKNOWN',)
            rec.append((n,row,lab))
    return rec


def impurity(records,features):
    groups=defaultdict(set)
    examples=defaultdict(list)
    for n,row,lab in records:
        k=key_for(n,row,features); groups[k].add(lab); examples[k].append((n,row,lab))
    bad=[k for k,v in groups.items() if len(v)>1]
    return groups,bad,examples

def greedy_crystal(records):
    chosen=["parity","mod3"]; history=[]
    groups,bad,ex=impurity(records,chosen)
    history.append((list(chosen),len(groups),len(bad)))
    while bad:
        best=None
        for f in FEATURES+["rel"]:
            if f in chosen: continue
            g,b,e=impurity(records,chosen+[f])
            score=(len(b),len(g))
            if best is None or score<best[0]: best=(score,f,g,b,e)
        if best is None or best[0][0]>=len(bad): break
        _,f,groups,bad,ex=best; chosen.append(f)
        history.append((list(chosen),len(groups),len(bad)))
    sep=[]
    for k in bad[:10]:
        vals=ex[k]; a=vals[0]
        b=next(z for z in vals[1:] if z[2]!=a[2])
        sep.append({"class":k,"a":{"n":a[0],"row":a[1],"future":a[2]},
                    "b":{"n":b[0],"row":b[1],"future":b[2]}})
    return {"chosen":chosen,"history":history,"classes":len(groups),
            "impure_classes":len(bad),"first_unresolved_separators":sep}

def classification_audit(records,features=('parity','mod3')):
    labels=sorted(set(r[2] for r in records))
    groups,bad,_=impurity(records,list(features))
    constant_groups,constant_bad,_=impurity(records,[])
    return {'chosen':list(features),'classes':len(groups),'impure_classes':len(bad),
            'label_values':labels,'constant_classes':len(constant_groups),
            'constant_impure_classes':len(constant_bad),
            'informative_for_quotient':len(labels)>1,
            'rank_certified':False,
            'interpretation':'SINGLE_LABEL_CONTROL_ONLY' if len(labels)<=1 else 'BUDGET_LABEL_VARIATION_ONLY'}


def verify_finite_exclusion(n,targets,values):
    """Finite invariant implies all-depth avoidance from sources 0<p<n.

    This is not a depth-limited search: inclusion of every lower source plus
    closure under the exact transition gives avoidance by induction.
    """
    values=set(values)
    return (n>1 and set(range(1,n)) <= values
            and all(T(x) in values for x in values)
            and all(y >= n and y not in (1,2) and y not in values for y in targets))


def rank_separator():
    invariant=set(range(1,27))|{29,32,35,38,40,44,53,80}
    rows=actual_trace(27,6)
    a,b=rows[5],rows[6]
    endpoints=[a[1],b[1]]
    keys=[list(key_for(27,row,['parity','mod3'])) for row in (a,b)]
    valid=(endpoints==[71,107] and T(a[1])==b[1]
           and all(27//(2**row[0])==0 for row in (a,b))
           and all(2**row[0]*row[1]==3**row[2]*27+row[3] for row in (a,b))
           and verify_finite_exclusion(27,endpoints,invariant))
    if not valid or keys[0]!=keys[1]:
        raise AssertionError('exact rank separator verification failed')
    return {'source':27,'depths':[5,6],'endpoints':endpoints,'coarse_keys':keys,
            'invariant':sorted(invariant),'invariant_successors':[[x,T(x)] for x in sorted(invariant)],
            'source_trace':[row[1] for row in rows],
            'both_no_exit_certified':True,'strict_coarse_rank_rejected':True,
            'scope':'No strictly decreasing one-step rank factors through (n, parity, mod3) on all actual unresolved states. Richer or macro-step ranks not rejected.',
            'verification':'EXACT_INTEGER_FINITE_INVARIANT_CHECK_NOT_LEAN'}


def run(sources,index=None,certificates=None):
    sources=list(sources)
    records=build_records(sources,index=index,certificates=certificates)
    unknown=sum(lab[0]=='UNKNOWN' for _,_,lab in records)
    return {'sources':len(sources),'unique_sources':len(set(sources)),
            'unresolved_post_zero_tail_states':len(records),
            'actual_pre_exit_states':len(records),
            'legacy_count_name_note':'Unresolved by bounded witnesses, not proved no-exit.',
            'bounded_unknown_states':unknown,
            'crystal':classification_audit(records),
            'unknown_examples':[{'n':n,'row':row} for n,row,lab in records if lab[0]=='UNKNOWN'][:20]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',default='evidence/crystal-source-coupled-v1')
    args=parser.parse_args()
    out=Path(args.output_dir)
    out.mkdir(parents=True,exist_ok=True)
    def write(name,data):
        target=out/name
        temporary=target.with_suffix(target.suffix+'.tmp')
        temporary.write_text(json.dumps(data,indent=2)+'\n')
        temporary.replace(target)
    rng=random.Random(28092026)
    train=list(range(3,4097))
    prospective=[rng.randrange(2**16,2**20) for _ in range(1024)]
    cohorts={'train':train,'prospective':prospective}
    write('cohorts.json',cohorts)
    write('progress.json',{'phase':'index','global_collatz':'UNKNOWN'})
    t=time.perf_counter()
    index=SharedBasin(max(train+prospective),256)
    index_seconds=time.perf_counter()-t
    print('Shared bounded index complete: '+str(index.stats),file=sys.stderr,flush=True)
    result={'schema':'COLLATZ_CRYSTAL_V4_SCALE_AUDIT_V1',
            'epistemic':'BOUNDED_EXECUTABLE_AUDIT_NOT_UNIVERSAL_PROOF',
            'cohort_sha256':hashlib.sha256(json.dumps(cohorts,sort_keys=True).encode()).hexdigest(),
            'index':index.stats,'index_seconds':index_seconds,
            'naive_endpoint_visits':257*sum(n-1 for n in train+prospective),
            'frozen_features':['parity','mod3'],
            'learned_model':False,'crystal_core_integrated':False}
    certificates=[]
    for name,sources in cohorts.items():
        result[name]=run(sources,index=index,certificates=certificates)
        write('progress.json',{'phase':name+'_complete','partial_result':result})
        print(name+' complete: '+str(result[name]['unresolved_post_zero_tail_states'])+' unresolved-prefix records',file=sys.stderr,flush=True)
    # Check all saved certificates independently of the shared-index traversal.
    for cert in certificates:
        n,k,y=cert['n'],cert['depth'],cert['endpoint']
        x=n
        for _ in range(k): x=T(x)
        if x!=y: raise AssertionError('source replay failed')
        event=cert['witness']
        if event[0]=='merge':
            p,r=event[1:]
            x=p
            for _ in range(r): x=T(x)
            if not 0<p<n or x!=y: raise AssertionError('lower-merge replay failed')
        elif event[0]=='descent':
            if not 0<y<n: raise AssertionError('descent witness failed')
        elif y not in (1,2): raise AssertionError('terminal witness failed')
    result['replayed_source_exit_certificates']=len(certificates)
    result['rank_separator']=rank_separator()
    result['global_collatz']='UNKNOWN'
    result['rank_certified']=False
    result['elapsed_seconds']=time.perf_counter()-t
    write('exit_certificates.json',certificates)
    write('result.json',result)
    write('progress.json',{'phase':'complete','global_collatz':'UNKNOWN'})
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
