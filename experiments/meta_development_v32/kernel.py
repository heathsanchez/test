from __future__ import annotations
from dataclasses import dataclass, field
from itertools import combinations, permutations, product
from typing import Any, Dict, Iterable, Tuple

from basis import (
    Expr, World, canonical_partition, consequence_partition, exact_quotient,
    family, fit_predictor, predict, read_exprs, route_of, vector,
)

@dataclass
class DevelopmentMemory:
    min_support: int = 2
    observations: Dict[str, list[dict[str,Any]]] = field(default_factory=dict)
    compiled: Dict[str, dict[str,Any]] = field(default_factory=dict)

    def observe(self, fingerprint: str, route: dict[str,Any]) -> None:
        rows=self.observations.setdefault(fingerprint,[])
        rows.append(dict(route))
        if len(rows) < self.min_support:
            return
        stages={r['stage'] for r in rows}; families={r['family'] for r in rows}
        if len(stages)!=1 or len(families)!=1:
            self.compiled.pop(fingerprint,None); return
        pats=[tuple(r['bank_pattern']) for r in rows]
        if not pats or len({len(p) for p in pats})!=1:
            self.compiled.pop(fingerprint,None); return
        generalized=tuple(pats[0][i] if len({p[i] for p in pats})==1 else -1 for i in range(len(pats[0])))
        self.compiled[fingerprint]={'stage':next(iter(stages)),'family':next(iter(families)),'bank_pattern':list(generalized)}

    def hint(self, fingerprint: str) -> dict[str,Any] | None:
        r=self.compiled.get(fingerprint)
        return dict(r) if r is not None else None


def _contingency_signature(values, target):
    # Canonical under raw-value and consequence-label relabelling.
    vgroups={}
    for i,v in enumerate(values): vgroups.setdefault(v,[]).append(i)
    ylabels=sorted(set(target), key=repr)
    rows=[]
    for idxs in vgroups.values():
        counts=[]
        for y in ylabels:
            counts.append(sum(1 for i in idxs if target[i]==y))
        rows.append(tuple(sorted(counts, reverse=True)))
    return tuple(sorted(rows))


class Kernel:
    def __init__(self, memory: DevelopmentMemory | None = None):
        self.memory=memory

    @staticmethod
    def authority(world: World) -> dict[str,Any] | None:
        if not world.complete or any(r.consequence is None for r in world.rows):
            return {'status':'UNKNOWN_AUTHORITY'}
        return None

    def fingerprint(self, world: World) -> str:
        auth=self.authority(world)
        if auth: return 'UNKNOWN'
        target=tuple(r.consequence for r in world.rows)
        bank_sigs=[]
        reads=read_exprs(world)
        by_bank={}
        for e in reads:
            by_bank.setdefault(int(e.args[0]),[]).append(e)
        for b in sorted(by_bank):
            rs=[]
            for e in by_bank[b]:
                vals=vector(e,world.rows)
                rs.append(_contingency_signature(vals,target))
            bank_sigs.append(tuple(sorted(rs)))
        payload=(len(set(target)),tuple(bank_sigs),len(world.rows))
        return repr(payload)

    @staticmethod
    def _binary_reads(world: World, reads: Iterable[Expr]) -> Tuple[Expr,...]:
        out=[]
        for e in reads:
            vals=set(vector(e,world.rows))
            if vals <= {0,1}:
                out.append(e)
        return tuple(out)

    @staticmethod
    def _match_bank_pattern(expr: Expr, pattern: Tuple[int,...]) -> bool:
        actual=tuple(expr.bank_pattern()); pattern=tuple(pattern)
        return len(actual)==len(pattern) and all(p==-1 or a==p for a,p in zip(actual,pattern))

    def _stage0(self, world: World):
        return [Expr('CONST')]

    def _stage1(self, world: World):
        return list(read_exprs(world))

    def _stage2(self, world: World, *, family_hint=None, bank_pattern=None):
        reads=read_exprs(world)
        binaries=self._binary_reads(world,reads)
        out=[]
        families={family_hint} if family_hint else {'PAIR','APPLY','SWITCH'}
        if 'PAIR' in families:
            for a,b in combinations(reads,2):
                e=Expr('PAIR',(a,b))
                if bank_pattern is None or self._match_bank_pattern(e,bank_pattern): out.append(e)
        if 'APPLY' in families:
            for a,b in combinations(binaries,2):
                for tt in range(16):
                    e=Expr('APPLY',(tt,a,b))
                    if bank_pattern is None or self._match_bank_pattern(e,bank_pattern): out.append(e)
        if 'SWITCH' in families:
            for s in binaries:
                for a in reads:
                    for b in reads:
                        e=Expr('SWITCH',(s,a,b))
                        if bank_pattern is None or self._match_bank_pattern(e,bank_pattern): out.append(e)
        return out

    def _stage3_tuple(self, world: World, *, bank_pattern=None):
        reads=read_exprs(world)
        out=[]
        for a,b,c in combinations(reads,3):
            e=Expr('TUPLE3',(a,b,c))
            if bank_pattern is None or self._match_bank_pattern(e,bank_pattern): out.append(e)
        return out

    def _stage3_nested(self, world: World, *, bank_pattern=None):
        reads=read_exprs(world)
        binaries=self._binary_reads(world,reads)
        out=[]
        # Ordered reads permit role-sensitive composition; truth tables remain uncompiled.
        for a,b,c in permutations(binaries,3):
            for tt1 in range(16):
                inner=Expr('APPLY',(tt1,a,b))
                for tt2 in range(16):
                    e=Expr('APPLY',(tt2,inner,c))
                    if bank_pattern is None or self._match_bank_pattern(e,bank_pattern): out.append(e)
        return out

    def _exact(self, world: World, candidates: Iterable[Expr]):
        exact=[]; tested=0
        target=consequence_partition(world)
        for e in candidates:
            tested+=1
            if canonical_partition(vector(e,world.rows)) == target:
                exact.append(e)
        # Preserve exact non-canonicity: distinct syntactic constructions remain on the frontier.
        seen=set(); rows=[]
        for e in exact:
            k=repr(e.data())
            if k not in seen:
                seen.add(k); rows.append(e)
        rows.sort(key=lambda e:(e.token_count(),e.depth(),family(e),e.bank_pattern(),repr(e.data())))
        return tested,rows

    def _frontier(self, exprs: list[Expr]) -> list[Expr]:
        if not exprs: return []
        # Preserve all syntax-minimal exact-quotient candidates at this language stage.
        best=min((e.token_count(),e.depth()) for e in exprs)
        return [e for e in exprs if (e.token_count(),e.depth())==best]

    def choose_probe(self, world: World, frontier: list[Expr]) -> dict[str,Any] | None:
        if len(frontier)<2 or not world.probes: return None
        models=[fit_predictor(e,world) for e in frontier]
        best=None
        for i,row in enumerate(world.probes):
            preds=tuple(predict(e,m,row) if m is not None else None for e,m in zip(frontier,models))
            groups=len(set(preds))
            known=sum(p is not None for p in preds)
            score=(groups,known)
            if best is None or score>best[0]: best=(score,i,row,preds)
        if best is None or best[0][0] <= 1: return None
        _,i,row,preds=best
        return {'probe_index':i,'predictions':list(preds),'_row':row}

    def apply_probe(self, world: World, frontier: list[Expr], probe: dict[str,Any]) -> list[Expr]:
        row=probe['_row']
        if row.consequence is None: return frontier
        out=[]
        for e in frontier:
            m=fit_predictor(e,world)
            if m is not None and predict(e,m,row)==row.consequence:
                out.append(e)
        return out

    def solve(self, world: World, *, use_memory=True, forced_hint=None, verification_enabled=True) -> dict[str,Any]:
        auth=self.authority(world)
        if auth:return auth
        if not verification_enabled:
            return {'status':'UNKNOWN_NO_VERIFIER','acquisition_tested':0}
        fp=self.fingerprint(world)
        tested_total=0
        tested_by_stage={}
        hint=forced_hint
        if hint is None and use_memory and self.memory is not None:
            hint=self.memory.hint(fp)

        # CONST and READ are always exhausted; they constitute the cheap obstruction fingerprint.
        for stage,gen in ((0,self._stage0),(1,self._stage1)):
            tested,exact=self._exact(world,gen(world)); tested_total+=tested; tested_by_stage[str(stage)]=tested
            if exact:
                front=self._frontier(exact)
                probe=self.choose_probe(world,front)
                pre=len(front)
                if probe is not None:
                    front=self.apply_probe(world,front,probe)
                selected=front[0] if front else exact[0]
                route=route_of(selected,stage)
                return {
                    'status':'VERIFIED','stage':stage,'route':route,'selected':selected.data(),
                    'frontier_size_before_probe':pre,'frontier_size_after_probe':len(front),
                    'probe':None if probe is None else {k:v for k,v in probe.items() if not k.startswith('_')},
                    'fingerprint':fp,'used_memory_hint':False,'hint_replay_failed':False,
                    'tested_by_stage':tested_by_stage,'tested_total':tested_total,
                    'acquisition_tested':0,'_selected':selected,'_frontier':front,
                }

        # If compiled developmental memory is available, replay its structural route first.
        hint_failed=False
        if hint is not None and int(hint.get('stage',99)) in (2,3):
            stage=int(hint['stage']); fam=hint['family']; pattern=tuple(hint.get('bank_pattern',()))
            if stage==2:
                tested,exact=self._exact(world,self._stage2(world,family_hint=fam,bank_pattern=pattern))
            elif fam=='TUPLE3':
                tested,exact=self._exact(world,self._stage3_tuple(world,bank_pattern=pattern))
            else:
                tested,exact=self._exact(world,self._stage3_nested(world,bank_pattern=pattern))
            tested_total+=tested; tested_by_stage[f'hint_{stage}']=tested
            if exact:
                front=self._frontier(exact); selected=front[0]
                route=route_of(selected,stage)
                return {
                    'status':'VERIFIED','stage':stage,'route':route,'selected':selected.data(),
                    'frontier_size_before_probe':len(front),'frontier_size_after_probe':len(front),'probe':None,
                    'fingerprint':fp,'used_memory_hint':True,'hint_replay_failed':False,
                    'tested_by_stage':tested_by_stage,'tested_total':tested_total,
                    'acquisition_tested':tested,'_selected':selected,'_frontier':front,
                }
            hint_failed=True

        # Cold/full acquisition search, stage ordered.
        acquisition=0
        # Stage 2 is exhausted as one bounded language.
        tested,exact=self._exact(world,self._stage2(world)); tested_total+=tested; acquisition+=tested; tested_by_stage['2']=tested
        if exact:
            front=self._frontier(exact); selected=front[0]; route=route_of(selected,2)
            return {'status':'VERIFIED','stage':2,'route':route,'selected':selected.data(),
                    'frontier_size_before_probe':len(front),'frontier_size_after_probe':len(front),'probe':None,
                    'fingerprint':fp,'used_memory_hint':False,'hint_replay_failed':hint_failed,
                    'tested_by_stage':tested_by_stage,'tested_total':tested_total,'acquisition_tested':acquisition,
                    '_selected':selected,'_frontier':front}

        # Within stage 3, flat arity costs fewer tokens than nested computation,
        # so it is exhausted before the deeper compositional family is unlocked.
        tested,exact=self._exact(world,self._stage3_tuple(world)); tested_total+=tested; acquisition+=tested; tested_by_stage['3_tuple']=tested
        if exact:
            front=self._frontier(exact); selected=front[0]; route=route_of(selected,3)
            return {'status':'VERIFIED','stage':3,'route':route,'selected':selected.data(),
                    'frontier_size_before_probe':len(front),'frontier_size_after_probe':len(front),'probe':None,
                    'fingerprint':fp,'used_memory_hint':False,'hint_replay_failed':hint_failed,
                    'tested_by_stage':tested_by_stage,'tested_total':tested_total,'acquisition_tested':acquisition,
                    '_selected':selected,'_frontier':front}

        tested,exact=self._exact(world,self._stage3_nested(world)); tested_total+=tested; acquisition+=tested; tested_by_stage['3_nested']=tested
        if exact:
            front=self._frontier(exact); selected=front[0]; route=route_of(selected,3)
            return {'status':'VERIFIED','stage':3,'route':route,'selected':selected.data(),
                    'frontier_size_before_probe':len(front),'frontier_size_after_probe':len(front),'probe':None,
                    'fingerprint':fp,'used_memory_hint':False,'hint_replay_failed':hint_failed,
                    'tested_by_stage':tested_by_stage,'tested_total':tested_total,'acquisition_tested':acquisition,
                    '_selected':selected,'_frontier':front}
        return {'status':'CERTIFIED_LANGUAGE_INADEQUACY','fingerprint':fp,'tested_by_stage':tested_by_stage,
                'tested_total':tested_total,'acquisition_tested':acquisition,'used_memory_hint':False,
                'hint_replay_failed':hint_failed}

    def compile(self, result: dict[str,Any]) -> dict[str,Any]:
        if self.memory is None or result.get('status')!='VERIFIED':
            return {'status':'NO_COMPILE'}
        self.memory.observe(result['fingerprint'],result['route'])
        return {'status':'COMPILED' if self.memory.hint(result['fingerprint']) else 'OBSERVED',
                'fingerprint':result['fingerprint'],'route':result['route']}
