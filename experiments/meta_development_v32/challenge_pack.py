from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Any

from basis import Row, World, family

@dataclass(frozen=True)
class Case:
    axis: str
    world: World
    expected_stage: int
    expected_family: str
    expected_bank_pattern: tuple[int,...] | None = None
    contraction_control: bool = False
    probe_required: bool = False


def _raw_rows(kind: str, variant: int, *, incomplete=False) -> tuple[Row,...]:
    rows=[]
    # Seven independent anonymous binary coordinates. Their interpretation is
    # deliberately absent from the frozen kernel; only numbered banks exist.
    for idx,bits in enumerate(product((0,1), repeat=7)):
        x0,x1,x2,h,c,a,b = bits
        semantic=(x0,x1,x2,h,c,a,b)
        if kind=='constant': y=0
        elif kind=='present': y=x0
        elif kind=='memory': y=h
        elif kind=='relation': y=2*x0+x1
        elif kind=='arity': y=4*x0+2*x1+x2
        elif kind=='composition': y=x0^x1^x2
        elif kind=='context': y=x0 if c==0 else x1
        elif kind=='action': y=x0 if a==0 else x1
        elif kind=='joint': y=2*x0+b
        elif kind=='contraction': y=x0
        else: raise ValueError(kind)

        # Post-freeze relabellings: channel permutation, independent bit flips,
        # row permutation, and consequence label permutation. Structural content
        # is preserved but concrete coordinates are not.
        current=[x0,x1,x2]
        if variant%3==1: current=[x2,x0,x1]
        elif variant%3==2: current=[x1,x2,x0]
        flips=[(variant>>j)&1 for j in range(7)]
        current=[v^flips[j] for j,v in enumerate(current)]
        hb=h^flips[3]; cb=c^flips[4]; ab=a^flips[5]; bb=b^flips[6]
        banks=(tuple(current),(hb,),(cb,),(ab,),(bb,),(idx,))
        yy=None if incomplete else int(y)
        if yy is not None:
            if kind in {'relation','joint'} and variant%2: yy=3-yy
            elif kind=='arity' and variant%2: yy=7-yy
            elif kind not in {'constant'} and variant%2: yy=1-yy if yy in (0,1) else yy
        rows.append(Row(banks,yy))
    if variant%2: rows=list(reversed(rows))
    elif variant%3==2: rows=rows[17:]+rows[:17]
    return tuple(rows)


def _tie_world(variant: int) -> World:
    rows=[]
    for idx,bits in enumerate(product((0,1), repeat=6)):
        x0,x2,h,c,a,b=bits; x1=x0
        cur=[x0,x1,x2]
        if variant%2: cur=[x1,x0,x2]
        banks=(tuple(cur),(h,),(c,),(a,),(b,),(idx,))
        y=x0 if variant%2==0 else 1-x0
        rows.append(Row(banks,int(y)))
    # Two candidate current reads are identical on train. These probes make them
    # disagree while keeping every required key already observed in training.
    p0=Row(((0,1,0),(0,),(0,),(0,),(0,),(1000,)), 0 if variant%2==0 else 1)
    p1=Row(((1,0,0),(0,),(0,),(0,),(0,),(1001,)), 1 if variant%2==0 else 0)
    return World(f'tie_v{variant}',tuple(rows),True,(p0,p1))


def make_case(axis: str, variant: int) -> Case:
    if axis=='no_change':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('constant',variant)),0,'CONST')
    if axis=='present_split':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('present',variant)),1,'READ',(0,))
    if axis=='memory':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('memory',variant)),1,'READ',(1,))
    if axis=='relation':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('relation',variant)),2,'PAIR',(0,0))
    if axis=='higher_arity':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('arity',variant)),3,'TUPLE3',(0,0,0))
    if axis=='composition':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('composition',variant)),3,'NESTED',(0,0,0))
    if axis=='context_conditioned':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('context',variant)),2,'SWITCH',(2,0,0))
    if axis=='intervention_conditioned':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('action',variant)),2,'SWITCH',(3,0,0))
    if axis=='joint_carrier':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('joint',variant)),2,'PAIR',(0,4))
    if axis=='contraction':
        return Case(axis,World(f'{axis}_v{variant}',_raw_rows('contraction',variant)),1,'READ',(0,),True)
    if axis=='active_probe':
        return Case(axis,_tie_world(variant),1,'READ',(0,),False,True)
    raise ValueError(axis)

AXES=(
    'no_change','present_split','memory','relation','higher_arity','composition',
    'context_conditioned','intervention_conditioned','joint_carrier','contraction','active_probe',
)

TRAIN_A=tuple(make_case(a,0) for a in AXES)
TRAIN_B=tuple(make_case(a,1) for a in AXES)
HELDOUT=tuple(make_case(a,2) for a in AXES)
INCOMPLETE=World('incomplete',_raw_rows('present',0,incomplete=True),False)


def case_matches(case: Case, result: dict[str,Any]) -> bool:
    if result.get('status')!='VERIFIED': return False
    route=result.get('route',{})
    if result.get('stage')!=case.expected_stage: return False
    if route.get('family')!=case.expected_family: return False
    if case.expected_bank_pattern is not None:
        pat=tuple(route.get('bank_pattern',()))
        if case.axis=='joint_carrier':
            if tuple(pat)!=(0,4): return False
        elif pat!=case.expected_bank_pattern:
            return False
    if case.probe_required:
        if result.get('probe') is None: return False
        if result.get('frontier_size_after_probe') != 1: return False
    return True
