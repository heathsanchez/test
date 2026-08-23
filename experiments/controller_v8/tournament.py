from dataclasses import dataclass
from collections import defaultdict

@dataclass(frozen=True)
class GeneratorSpec:
    name: str
    family: str
    slots: tuple[str,...]
    budget_units: int

@dataclass(frozen=True)
class Proposal:
    generator: str
    slot: str
    canonical_move: str
    produced_at: int
    cost_units: int
    protected_leakage: bool=False
    valid: bool=True
    audited_split: float=0.0

@dataclass(frozen=True)
class ExecutedResult:
    canonical_move: str
    verified: bool
    deciding: bool
    survived_attack: bool=False
    survived_transfer: bool=False


def valid_proposals(specs, proposals):
    by={s.name:s for s in specs}
    out=[]
    spent=defaultdict(int)
    for p in sorted(proposals,key=lambda x:(x.produced_at,x.generator,x.slot,x.canonical_move)):
        s=by.get(p.generator)
        if s is None or p.slot not in s.slots or p.protected_leakage or not p.valid:
            continue
        if spent[p.generator]+p.cost_units>s.budget_units:
            continue
        spent[p.generator]+=p.cost_units
        out.append(p)
    return out


def provenance_map(specs, proposals):
    """Credit all generators that independently place an equivalent move on the table.
    First discovery is reported separately; ownership is never exclusive."""
    ps=valid_proposals(specs,proposals)
    prov=defaultdict(list)
    for p in ps:
        prov[p.canonical_move].append(p)
    return prov


def first_discovery(prov, move):
    xs=prov.get(move,[])
    if not xs:return None
    t=min(p.produced_at for p in xs)
    return tuple(sorted({p.generator for p in xs if p.produced_at==t}))


def generator_metrics(specs, proposals, results):
    prov=provenance_map(specs,proposals)
    result={r.canonical_move:r for r in results}
    metrics={s.name:{'unique_moves':0,'deciding_moves':0,'verified_moves':0,'attack_survivors':0,'transfer_survivors':0,'first_deciding':0,'duplicate_moves':0,'best_rank':None} for s in specs}
    seen_by_gen=defaultdict(set)
    for move,ps in prov.items():
        gens={p.generator for p in ps}
        for g in gens:
            if move in seen_by_gen[g]: metrics[g]['duplicate_moves']+=1
            else:
                seen_by_gen[g].add(move); metrics[g]['unique_moves']+=1
            ranks=sorted((p.produced_at,p.cost_units) for p in ps if p.generator==g)
            br=ranks[0][0]
            old=metrics[g]['best_rank']; metrics[g]['best_rank']=br if old is None else min(old,br)
            r=result.get(move)
            if r:
                metrics[g]['verified_moves']+=int(r.verified)
                metrics[g]['deciding_moves']+=int(r.deciding)
                metrics[g]['attack_survivors']+=int(r.survived_attack)
                metrics[g]['transfer_survivors']+=int(r.survived_transfer)
        r=result.get(move)
        if r and r.deciding:
            fd=first_discovery(prov,move)
            if fd:
                for g in fd: metrics[g]['first_deciding']+=1
    return metrics


def ablation_reach(specs, proposals, results, removed_generator):
    kept=[p for p in proposals if p.generator!=removed_generator]
    prov=provenance_map(specs,kept)
    deciding={r.canonical_move for r in results if r.deciding and r.verified}
    return bool(deciding & set(prov))


def substitution_matrix(specs, proposals, results):
    """For each generator, report whether some other generator independently produced
    an equivalent verified deciding move. This separates unique contribution from
    mere first arrival."""
    prov=provenance_map(specs,proposals)
    deciding={r.canonical_move for r in results if r.deciding and r.verified}
    out={}
    for s in specs:
        own={m for m,ps in prov.items() if any(p.generator==s.name for p in ps)} & deciding
        substitutes={m for m in own if any(p.generator!=s.name for p in prov[m])}
        out[s.name]={'own_deciding':len(own),'substitutable':len(substitutes),'unique_deciding':len(own-substitutes)}
    return out
