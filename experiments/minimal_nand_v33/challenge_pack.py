from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Any

from basis import Row, World

@dataclass(frozen=True)
class Case:
    axis: str
    world: World

AXES=(
    'no_change','present','memory','relation','arity','composition',
    'context','intervention','joint','contraction','probe',
)

def make_world(axis: str, variant: int, *, incomplete: bool=False) -> World:
    rows=[]
    for bits in product((0,1), repeat=7):
        x0,x1,x2,h,c,a,b=bits
        if axis=='no_change': y=0
        elif axis in ('present','contraction','probe'): y=x0
        elif axis=='memory': y=h
        elif axis=='relation': y=2*x0+x1
        elif axis=='arity': y=4*x0+2*x1+x2
        elif axis=='composition': y=x0|x1
        elif axis=='context': y=x0 if c==0 else x1
        elif axis=='intervention': y=x0 if a==0 else x1
        elif axis=='joint': y=2*x0+b
        else: raise ValueError(axis)

        current=[x0,x1,x2]
        if variant%3==1: current=[x2,x0,x1]
        elif variant%3==2: current=[x1,x2,x0]
        banks=(tuple(current),(h,),(c,),(a,),(b,))
        rows.append(Row(banks,None if incomplete else int(y)))

    if variant%2:
        rows=list(reversed(rows))
    elif variant%3==2:
        rows=rows[23:]+rows[:23]

    probes=()
    if axis=='probe':
        target_pos=(0,1,2)[variant%3]
        alias_pos=(target_pos+1)%3
        repaired=[]
        for r in rows:
            cur=list(r.banks[0])
            cur[alias_pos]=cur[target_pos]
            repaired.append(Row((tuple(cur),)+r.banks[1:],r.consequence))
        rows=repaired

        c0=[0,0,0]; c1=[0,0,0]
        c0[target_pos]=0; c0[alias_pos]=1
        c1[target_pos]=1; c1[alias_pos]=0
        probes=(
            Row((tuple(c0),(0,),(0,),(0,),(0,)),0),
            Row((tuple(c1),(0,),(0,),(0,),(0,)),1),
        )

    return World(f'{axis}_v{variant}',tuple(rows),not incomplete,probes)

VARIANTS={
    0: tuple(Case(a,make_world(a,0)) for a in AXES),
    1: tuple(Case(a,make_world(a,1)) for a in AXES),
    2: tuple(Case(a,make_world(a,2)) for a in AXES),
}
INCOMPLETE=make_world('present',0,incomplete=True)

def dep_banks(result: dict[str,Any]) -> list[set[int]]:
    out=[]
    for root in result.get('dependency_pattern',[]):
        out.append({int(cell[0]) for cell in root})
    return out

def expected(case: Case, result: dict[str,Any], variant: int) -> bool:
    if result.get('status')!='VERIFIED': return False
    axis=case.axis
    banks=dep_banks(result)
    if axis=='no_change':
        return result.get('root_count')==0 and result.get('nand_cost')==0
    if axis=='present':
        return result.get('root_count')==1 and result.get('nand_cost')==0 and banks==[{0}]
    if axis=='memory':
        return result.get('root_count')==1 and result.get('nand_cost')==0 and banks==[{1}]
    if axis=='relation':
        return result.get('root_count')==2 and result.get('nand_cost')==0 and all(b=={0} for b in banks)
    if axis=='arity':
        return result.get('root_count')==3 and result.get('nand_cost')==0 and all(b=={0} for b in banks)
    if axis=='composition':
        return result.get('root_count')==1 and result.get('nand_cost',0)>0 and banks==[{0}]
    if axis=='context':
        return result.get('root_count')==1 and result.get('nand_cost',0)>0 and banks==[{0,2}]
    if axis=='intervention':
        return result.get('root_count')==1 and result.get('nand_cost',0)>0 and banks==[{0,3}]
    if axis=='joint':
        return result.get('root_count')==2 and result.get('nand_cost')==0 and sorted(banks,key=lambda z:sorted(z))==[{0},{4}]
    if axis=='contraction':
        raw_codes={r.banks for r in case.world.rows}
        targets={r.consequence for r in case.world.rows}
        return result.get('root_count')==1 and len(raw_codes)>len(targets)==2
    if axis=='probe':
        return (
            result.get('root_count')==1
            and result.get('nand_cost')==0
            and result.get('frontier_size_before_probe',0)>=2
            and result.get('frontier_size_after_probe')==1
            and result.get('probe') is not None
        )
    return False
