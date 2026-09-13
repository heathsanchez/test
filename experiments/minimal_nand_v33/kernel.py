from __future__ import annotations
from itertools import combinations
from math import ceil, log2
from basis import Row, World, Term

class Kernel:
    def __init__(self,max_nand_cost=5): self.max_nand_cost=max_nand_cost; self._closure_cache={}
    @staticmethod
    def authority(w):
        if not w.complete or any(r.consequence is None for r in w.rows): return {'status':'UNKNOWN_AUTHORITY'}
    @staticmethod
    def _raw_key(w): return tuple(r.banks for r in w.rows)
    def atoms(self,w):
        out=[]
        if not w.rows:return out
        for b,bank in enumerate(w.rows[0].banks):
            for i in range(len(bank)):
                vals=[int(r.banks[b][i]) for r in w.rows]
                if set(vals)<={0,1}:
                    bits=sum(v<<j for j,v in enumerate(vals)); out.append(Term('ATOM',(b,i),0,bits,((b,i),),1))
        return out
    def closure(self,w):
        key=(self._raw_key(w),self.max_nand_cost)
        if key in self._closure_cache:return self._closure_cache[key]
        n=len(w.rows);mask=(1<<n)-1;best={};by=[[] for _ in range(self.max_nand_cost+1)];pair_tests=0
        for t in self.atoms(w):
            if t.bits not in best:best[t.bits]=t;by[0].append(t)
        for c in range(1,self.max_nand_cost+1):
            new=[]
            for i in range(c):
                j=c-1-i
                if i>j:continue
                A=by[i];B=by[j]
                for ia,a in enumerate(A):
                    start=ia if i==j else 0
                    for b in B[start:]:
                        pair_tests+=1; bits=mask^(a.bits&b.bits)
                        if bits in best:continue
                        deps=tuple(sorted(set(a.deps)|set(b.deps)));t=Term('NAND',(a,b),c,bits,deps,max(a.depth,b.depth)+1)
                        best[bits]=t;new.append(t)
            by[c]=new
        val=(best,by,pair_tests);self._closure_cache[key]=val;return val
    @staticmethod
    def target_classes(w):
        ids={};cl=[]
        for r in w.rows:
            y=r.consequence
            if y not in ids:ids[y]=len(ids)
            cl.append(ids[y])
        return tuple(cl),len(ids)
    @staticmethod
    def class_sig(bits,classes,k):
        out=[]
        for c in range(k):
            vals={((bits>>i)&1) for i,cc in enumerate(classes) if cc==c}
            if len(vals)!=1:return None
            out.append(next(iter(vals)))
        return tuple(out)
    @staticmethod
    def separates(sigs,k): return len({tuple(s[c] for s in sigs) for c in range(k)})==k
    def root_frontier(self,w,best):
        classes,k=self.target_classes(w)
        if k==1:return [()],0,0
        bysig={}
        term_pool=list(best.values())
        atom_seen={(t.bits,t.args) for t in term_pool if t.op=='ATOM'}
        for t in self.atoms(w):
            if (t.bits,t.args) not in atom_seen: term_pool.append(t)
        for t in term_pool:
            sig=self.class_sig(t.bits,classes,k)
            if sig is None:continue
            m=(t.cost,t.depth,len(t.deps))
            rows=bysig.get(sig)
            if rows is None or m<rows[0][0]: bysig[sig]=[(m,t)]
            elif m==rows[0][0] and all(repr(t.data())!=repr(x[1].data()) for x in rows): rows.append((m,t))
        cand=sorted(((sig,rows[0][1]) for sig,rows in bysig.items()),key=lambda x:(x[1].cost,x[1].depth,len(x[1].deps),x[0]))
        lower=ceil(log2(k));bestm=None;front=[];combo_tests=0
        for roots in range(lower,min(k,3)+1):
            for combo in combinations(cand,roots):
                combo_tests+=1;sigs=[x[0] for x in combo]
                if not self.separates(sigs,k):continue
                base_terms=tuple(x[1] for x in combo);m=(sum(t.cost for t in base_terms),max(t.depth for t in base_terms),sum(len(t.deps) for t in base_terms))
                if bestm is not None and m>bestm: continue
                choices=[]
                for sig,_ in combo:
                    choices.append([row[1] for row in bysig[sig]])
                import itertools
                expanded=[tuple(xs) for xs in itertools.product(*choices)]
                if bestm is None or m<bestm:bestm=m;front=expanded[:64]
                elif m==bestm:front.extend(expanded[:max(0,64-len(front))])
            if front:break
        front.sort(key=lambda ts:repr([t.data() for t in ts]));return front,len(cand),combo_tests
    @staticmethod
    def eval_term(t,row):
        if t.op=='ATOM':b,i=t.args;return int(row.banks[b][i])
        a,b=t.args;return 1-(Kernel.eval_term(a,row)&Kernel.eval_term(b,row))
    @staticmethod
    def code(roots,row): return tuple(Kernel.eval_term(t,row) for t in roots)
    @staticmethod
    def fit(roots,w):
        m={}
        for r in w.rows:
            c=Kernel.code(roots,r);y=r.consequence
            if c in m and m[c]!=y:return None
            m[c]=y
        return m
    def choose_probe(self,w,front):
        if len(front)<2 or not w.probes:return None
        models=[self.fit(ts,w) for ts in front];best=None
        for i,r in enumerate(w.probes):
            preds=tuple(m.get(self.code(ts,r)) if m is not None else None for ts,m in zip(front,models));score=(len(set(preds)),sum(p is not None for p in preds))
            if best is None or score>best[0]:best=(score,i,r,preds)
        if best is None or best[0][0]<=1:return None
        return {'probe_index':best[1],'predictions':list(best[3]),'_row':best[2]}
    def solve(self,w,verification_enabled=True):
        a=self.authority(w)
        if a:return a
        if not verification_enabled:return {'status':'UNKNOWN_NO_VERIFIER','searched_terms':0}
        classes,k=self.target_classes(w)
        if k==1:return {'status':'VERIFIED','root_count':0,'nand_cost':0,'depth':0,'frontier_size_before_probe':1,'frontier_size_after_probe':1,'probe':None,'roots':[],'dependency_pattern':[],'searched_terms':0,'_roots':()}
        best,by,pairs=self.closure(w);front,compat,combos=self.root_frontier(w,best)
        if not front:return {'status':'CERTIFIED_SUBSTRATE_INADEQUACY','searched_terms':len(best),'pair_tests':pairs,'compatible_terms':compat,'combo_tests':combos}
        before=len(front);probe=self.choose_probe(w,front)
        if probe is not None:
            row=probe['_row'];good=[]
            for ts in front:
                m=self.fit(ts,w)
                if m is not None and m.get(self.code(ts,row))==row.consequence:good.append(ts)
            front=good
        roots=front[0]
        return {'status':'VERIFIED','root_count':len(roots),'nand_cost':sum(t.cost for t in roots),'depth':max(t.depth for t in roots),
                'frontier_size_before_probe':before,'frontier_size_after_probe':len(front),'probe':None if probe is None else {k:v for k,v in probe.items() if not k.startswith('_')},
                'roots':[t.data() for t in roots],'dependency_pattern':[list(t.deps) for t in roots], 'searched_terms':len(best),'pair_tests':pairs,'compatible_terms':compat,'combo_tests':combos,'_roots':roots}
